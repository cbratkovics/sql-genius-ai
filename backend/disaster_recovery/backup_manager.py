import asyncio
import boto3
import gzip
import json
import logging
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import aiofiles
from botocore.exceptions import NoCredentialsError, ClientError
import redis.asyncio as redis
from backend.core.config import settings
from backend.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class BackupType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    TRANSACTION_LOG = "transaction_log"


class BackupStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class RecoveryType(str, Enum):
    POINT_IN_TIME = "point_in_time"
    FULL_RESTORE = "full_restore"
    PARTIAL_RESTORE = "partial_restore"
    CROSS_REGION = "cross_region"


@dataclass
class BackupMetadata:
    backup_id: str
    backup_type: BackupType
    timestamp: datetime
    size_bytes: int
    checksum: str
    location: str
    retention_until: datetime
    status: BackupStatus
    database_name: str = None
    table_names: List[str] = field(default_factory=list)
    compression: str = "gzip"
    encryption: bool = True
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class RecoveryPlan:
    recovery_id: str
    recovery_type: RecoveryType
    target_timestamp: datetime
    source_backups: List[str]
    estimated_duration: int  # seconds
    estimated_rto: int  # Recovery Time Objective in seconds
    estimated_rpo: int  # Recovery Point Objective in seconds
    steps: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


class DisasterRecoveryManager:
    """Enterprise disaster recovery management system"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION
        )
        self.redis_client = redis.from_url(settings.REDIS_URL)
        
        # Backup configuration
        self.primary_bucket = f"{settings.PROJECT_NAME.lower()}-backups"
        self.dr_bucket = f"{settings.PROJECT_NAME.lower()}-dr-backups"
        self.backup_prefix = "sql-genius-ai"
        
        # Retention policies (in days)
        self.retention_policies = {
            BackupType.FULL: 90,
            BackupType.INCREMENTAL: 30,
            BackupType.DIFFERENTIAL: 30,
            BackupType.TRANSACTION_LOG: 7
        }
        
        # RTO/RPO targets
        self.rto_targets = {
            "critical": 60,    # 1 minute
            "high": 300,       # 5 minutes
            "medium": 1800,    # 30 minutes
            "low": 3600        # 1 hour
        }
        
        self.rpo_targets = {
            "critical": 60,    # 1 minute
            "high": 300,       # 5 minutes
            "medium": 900,     # 15 minutes
            "low": 3600        # 1 hour
        }
    
    async def initialize(self):
        """Initialize disaster recovery system"""
        await self._ensure_backup_buckets()
        await self._initialize_backup_schedules()
        logger.info("Disaster recovery system initialized")
    
    async def _ensure_backup_buckets(self):
        """Ensure S3 backup buckets exist with proper configuration"""
        try:
            for bucket_name in [self.primary_bucket, self.dr_bucket]:
                try:
                    self.s3_client.head_bucket(Bucket=bucket_name)
                except ClientError as e:
                    if e.response['Error']['Code'] == '404':
                        # Create bucket
                        self.s3_client.create_bucket(Bucket=bucket_name)
                        logger.info(f"Created backup bucket: {bucket_name}")
                        
                        # Configure bucket
                        await self._configure_backup_bucket(bucket_name)
        
        except NoCredentialsError:
            logger.error("AWS credentials not configured for backup storage")
            raise
    
    async def _configure_backup_bucket(self, bucket_name: str):
        """Configure S3 bucket for backup storage"""
        try:
            # Enable versioning
            self.s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Configure encryption
            self.s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [{
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        },
                        'BucketKeyEnabled': True
                    }]
                }
            )
            
            # Set lifecycle policy for automated cleanup
            lifecycle_policy = {
                'Rules': [
                    {
                        'ID': 'BackupRetention',
                        'Status': 'Enabled',
                        'Transitions': [
                            {
                                'Days': 30,
                                'StorageClass': 'STANDARD_IA'
                            },
                            {
                                'Days': 90,
                                'StorageClass': 'GLACIER'
                            },
                            {
                                'Days': 365,
                                'StorageClass': 'DEEP_ARCHIVE'
                            }
                        ],
                        'Expiration': {
                            'Days': 2555  # 7 years
                        }
                    }
                ]
            }
            
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_policy
            )
            
            logger.info(f"Configured backup bucket: {bucket_name}")
            
        except ClientError as e:
            logger.error(f"Failed to configure bucket {bucket_name}: {e}")
    
    async def create_database_backup(
        self,
        backup_type: BackupType = BackupType.FULL,
        database_name: str = None,
        tables: List[str] = None
    ) -> BackupMetadata:
        """Create database backup"""
        backup_id = f"db-{backup_type.value}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        try:
            logger.info(f"Starting {backup_type.value} database backup: {backup_id}")
            
            # Create backup metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type=backup_type,
                timestamp=datetime.utcnow(),
                size_bytes=0,
                checksum="",
                location="",
                retention_until=datetime.utcnow() + timedelta(days=self.retention_policies[backup_type]),
                status=BackupStatus.IN_PROGRESS,
                database_name=database_name,
                table_names=tables or []
            )
            
            # Store metadata
            await self._store_backup_metadata(metadata)
            
            # Perform backup based on type
            if backup_type == BackupType.FULL:
                backup_file = await self._create_full_database_backup(database_name, tables)
            elif backup_type == BackupType.INCREMENTAL:
                backup_file = await self._create_incremental_backup(database_name, tables)
            elif backup_type == BackupType.TRANSACTION_LOG:
                backup_file = await self._create_transaction_log_backup(database_name)
            else:
                raise ValueError(f"Unsupported backup type: {backup_type}")
            
            # Upload to S3
            s3_key = f"{self.backup_prefix}/{backup_type.value}/{backup_id}.sql.gz"
            await self._upload_backup_to_s3(backup_file, s3_key)
            
            # Update metadata
            file_size = os.path.getsize(backup_file)
            checksum = await self._calculate_file_checksum(backup_file)
            
            metadata.size_bytes = file_size
            metadata.checksum = checksum
            metadata.location = f"s3://{self.primary_bucket}/{s3_key}"
            metadata.status = BackupStatus.COMPLETED
            
            await self._store_backup_metadata(metadata)
            
            # Cross-region replication
            await self._replicate_to_dr_region(backup_file, s3_key)
            
            # Cleanup local file
            os.unlink(backup_file)
            
            logger.info(f"Database backup completed: {backup_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            metadata.status = BackupStatus.FAILED
            await self._store_backup_metadata(metadata)
            raise
    
    async def _create_full_database_backup(
        self,
        database_name: str = None,
        tables: List[str] = None
    ) -> str:
        """Create full database backup using pg_dump"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            temp_file = f.name
        
        try:
            # Build pg_dump command
            cmd = [
                'pg_dump',
                '--host', settings.POSTGRES_HOST,
                '--port', str(settings.POSTGRES_PORT),
                '--username', settings.POSTGRES_USER,
                '--no-password',
                '--verbose',
                '--clean',
                '--no-acl',
                '--no-owner',
                '--format', 'custom',
                '--file', temp_file
            ]
            
            # Add specific tables if provided
            if tables:
                for table in tables:
                    cmd.extend(['--table', table])
            
            # Add database name
            cmd.append(database_name or settings.POSTGRES_DB)
            
            # Set environment variables
            env = os.environ.copy()
            env['PGPASSWORD'] = settings.POSTGRES_PASSWORD
            
            # Execute backup
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"pg_dump failed: {stderr.decode()}")
            
            # Compress backup
            compressed_file = temp_file + '.gz'
            with open(temp_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            os.unlink(temp_file)
            return compressed_file
            
        except Exception as e:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            raise e
    
    async def _create_incremental_backup(
        self,
        database_name: str = None,
        tables: List[str] = None
    ) -> str:
        """Create incremental backup using WAL files"""
        
        # Get last backup timestamp
        last_backup = await self._get_last_backup(BackupType.FULL, database_name)
        if not last_backup:
            # No full backup exists, create one
            return await self._create_full_database_backup(database_name, tables)
        
        # Create WAL archive backup
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            temp_file = f.name
        
        try:
            # Get WAL files since last backup
            await self._get_wal_files_since(last_backup.timestamp)
            
            # Archive WAL files
            cmd = [
                'pg_receivewal',
                '--host', settings.POSTGRES_HOST,
                '--port', str(settings.POSTGRES_PORT),
                '--username', settings.POSTGRES_USER,
                '--no-password',
                '--directory', os.path.dirname(temp_file),
                '--verbose'
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = settings.POSTGRES_PASSWORD
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Run for a short time to collect recent WAL
            await asyncio.sleep(5)
            process.terminate()
            await process.wait()
            
            # Compress the WAL directory
            compressed_file = temp_file + '.gz'
            with gzip.open(compressed_file, 'wb') as f_out:
                # Archive directory contents
                import tarfile
                with tarfile.open(fileobj=f_out, mode='w') as tar:
                    tar.add(os.path.dirname(temp_file), arcname='wal_files')
            
            return compressed_file
            
        except Exception as e:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            raise e
    
    async def _create_transaction_log_backup(self, database_name: str = None) -> str:
        """Create transaction log backup"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            temp_file = f.name
        
        try:
            # Get current WAL position
            async with AsyncSessionLocal() as db:
                result = await db.execute("SELECT pg_current_wal_lsn()")
                result.scalar()
            
            # Create logical backup of recent transactions
            cmd = [
                'pg_dump',
                '--host', settings.POSTGRES_HOST,
                '--port', str(settings.POSTGRES_PORT),
                '--username', settings.POSTGRES_USER,
                '--no-password',
                '--format', 'custom',
                '--file', temp_file,
                '--serializable-deferrable',
                database_name or settings.POSTGRES_DB
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = settings.POSTGRES_PASSWORD
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Transaction log backup failed: {stderr.decode()}")
            
            # Compress
            compressed_file = temp_file + '.gz'
            with open(temp_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            os.unlink(temp_file)
            return compressed_file
            
        except Exception as e:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            raise e
    
    async def _upload_backup_to_s3(self, file_path: str, s3_key: str):
        """Upload backup file to S3"""
        try:
            # Upload with multipart for large files
            self.s3_client.upload_file(
                file_path,
                self.primary_bucket,
                s3_key,
                ExtraArgs={
                    'StorageClass': 'STANDARD',
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            logger.info(f"Uploaded backup to s3://{self.primary_bucket}/{s3_key}")
            
        except ClientError as e:
            logger.error(f"Failed to upload backup to S3: {e}")
            raise
    
    async def _replicate_to_dr_region(self, file_path: str, s3_key: str):
        """Replicate backup to disaster recovery region"""
        try:
            # Upload to DR bucket
            self.s3_client.upload_file(
                file_path,
                self.dr_bucket,
                s3_key,
                ExtraArgs={
                    'StorageClass': 'STANDARD',
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            logger.info(f"Replicated backup to DR region: s3://{self.dr_bucket}/{s3_key}")
            
        except ClientError as e:
            logger.warning(f"Failed to replicate to DR region: {e}")
    
    async def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        
        async with aiofiles.open(file_path, 'rb') as f:
            async for chunk in f:
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    async def _store_backup_metadata(self, metadata: BackupMetadata):
        """Store backup metadata in Redis"""
        try:
            metadata_dict = {
                'backup_id': metadata.backup_id,
                'backup_type': metadata.backup_type.value,
                'timestamp': metadata.timestamp.isoformat(),
                'size_bytes': metadata.size_bytes,
                'checksum': metadata.checksum,
                'location': metadata.location,
                'retention_until': metadata.retention_until.isoformat(),
                'status': metadata.status.value,
                'database_name': metadata.database_name,
                'table_names': metadata.table_names,
                'compression': metadata.compression,
                'encryption': metadata.encryption,
                'tags': metadata.tags
            }
            
            await self.redis_client.setex(
                f"backup:metadata:{metadata.backup_id}",
                86400 * 90,  # 90 days
                json.dumps(metadata_dict)
            )
            
            # Add to backup index
            await self.redis_client.zadd(
                "backup:index",
                {metadata.backup_id: metadata.timestamp.timestamp()}
            )
            
        except Exception as e:
            logger.error(f"Failed to store backup metadata: {e}")
    
    async def _get_last_backup(
        self,
        backup_type: BackupType,
        database_name: str = None
    ) -> Optional[BackupMetadata]:
        """Get the most recent backup of specified type"""
        try:
            # Get recent backups from index
            recent_backups = await self.redis_client.zrevrange(
                "backup:index", 0, 100, withscores=True
            )
            
            for backup_id, timestamp in recent_backups:
                metadata_json = await self.redis_client.get(
                    f"backup:metadata:{backup_id}"
                )
                
                if metadata_json:
                    data = json.loads(metadata_json)
                    
                    if (data['backup_type'] == backup_type.value and
                        data['status'] == BackupStatus.COMPLETED.value and
                        (not database_name or data['database_name'] == database_name)):
                        
                        return BackupMetadata(
                            backup_id=data['backup_id'],
                            backup_type=BackupType(data['backup_type']),
                            timestamp=datetime.fromisoformat(data['timestamp']),
                            size_bytes=data['size_bytes'],
                            checksum=data['checksum'],
                            location=data['location'],
                            retention_until=datetime.fromisoformat(data['retention_until']),
                            status=BackupStatus(data['status']),
                            database_name=data['database_name'],
                            table_names=data['table_names']
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get last backup: {e}")
            return None
    
    async def _get_wal_files_since(self, timestamp: datetime) -> List[str]:
        """Get WAL files since specified timestamp"""
        # This would query PostgreSQL for WAL files
        # Implementation depends on your WAL archiving setup
        return []
    
    async def create_recovery_plan(
        self,
        recovery_type: RecoveryType,
        target_timestamp: datetime,
        database_name: str = None
    ) -> RecoveryPlan:
        """Create disaster recovery plan"""
        
        recovery_id = f"recovery-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        try:
            # Find required backups
            source_backups = await self._find_recovery_backups(
                target_timestamp, database_name
            )
            
            if not source_backups:
                raise Exception("No suitable backups found for recovery")
            
            # Estimate recovery time
            estimated_duration = await self._estimate_recovery_duration(
                recovery_type, source_backups
            )
            
            # Create recovery steps
            steps = await self._generate_recovery_steps(
                recovery_type, source_backups, target_timestamp
            )
            
            plan = RecoveryPlan(
                recovery_id=recovery_id,
                recovery_type=recovery_type,
                target_timestamp=target_timestamp,
                source_backups=[b.backup_id for b in source_backups],
                estimated_duration=estimated_duration,
                estimated_rto=self.rto_targets["high"],
                estimated_rpo=self.rpo_targets["high"],
                steps=steps
            )
            
            # Store recovery plan
            await self._store_recovery_plan(plan)
            
            logger.info(f"Created recovery plan: {recovery_id}")
            return plan
            
        except Exception as e:
            logger.error(f"Failed to create recovery plan: {e}")
            raise
    
    async def _find_recovery_backups(
        self,
        target_timestamp: datetime,
        database_name: str = None
    ) -> List[BackupMetadata]:
        """Find backups required for recovery to target timestamp"""
        
        backups = []
        
        # Find the latest full backup before target timestamp
        full_backup = None
        recent_backups = await self.redis_client.zrevrange(
            "backup:index", 0, -1, withscores=True
        )
        
        for backup_id, timestamp in recent_backups:
            backup_time = datetime.fromtimestamp(timestamp)
            
            if backup_time <= target_timestamp:
                metadata_json = await self.redis_client.get(
                    f"backup:metadata:{backup_id}"
                )
                
                if metadata_json:
                    data = json.loads(metadata_json)
                    
                    if (data['backup_type'] == BackupType.FULL.value and
                        data['status'] == BackupStatus.COMPLETED.value and
                        (not database_name or data['database_name'] == database_name)):
                        
                        full_backup = BackupMetadata(
                            backup_id=data['backup_id'],
                            backup_type=BackupType(data['backup_type']),
                            timestamp=datetime.fromisoformat(data['timestamp']),
                            size_bytes=data['size_bytes'],
                            checksum=data['checksum'],
                            location=data['location'],
                            retention_until=datetime.fromisoformat(data['retention_until']),
                            status=BackupStatus(data['status']),
                            database_name=data['database_name'],
                            table_names=data['table_names']
                        )
                        break
        
        if not full_backup:
            raise Exception("No full backup found before target timestamp")
        
        backups.append(full_backup)
        
        # Find incremental/transaction log backups after full backup
        for backup_id, timestamp in recent_backups:
            backup_time = datetime.fromtimestamp(timestamp)
            
            if (backup_time > full_backup.timestamp and 
                backup_time <= target_timestamp):
                
                metadata_json = await self.redis_client.get(
                    f"backup:metadata:{backup_id}"
                )
                
                if metadata_json:
                    data = json.loads(metadata_json)
                    
                    if (data['backup_type'] in [BackupType.INCREMENTAL.value, BackupType.TRANSACTION_LOG.value] and
                        data['status'] == BackupStatus.COMPLETED.value and
                        (not database_name or data['database_name'] == database_name)):
                        
                        backup_metadata = BackupMetadata(
                            backup_id=data['backup_id'],
                            backup_type=BackupType(data['backup_type']),
                            timestamp=datetime.fromisoformat(data['timestamp']),
                            size_bytes=data['size_bytes'],
                            checksum=data['checksum'],
                            location=data['location'],
                            retention_until=datetime.fromisoformat(data['retention_until']),
                            status=BackupStatus(data['status']),
                            database_name=data['database_name'],
                            table_names=data['table_names']
                        )
                        backups.append(backup_metadata)
        
        return sorted(backups, key=lambda b: b.timestamp)
    
    async def _estimate_recovery_duration(
        self,
        recovery_type: RecoveryType,
        backups: List[BackupMetadata]
    ) -> int:
        """Estimate recovery duration in seconds"""
        
        # Base time for full restore (assume 1GB per minute)
        total_size_gb = sum(b.size_bytes for b in backups) / (1024**3)
        base_duration = int(total_size_gb * 60)  # 60 seconds per GB
        
        # Adjust based on recovery type
        multipliers = {
            RecoveryType.FULL_RESTORE: 1.0,
            RecoveryType.POINT_IN_TIME: 1.2,  # Extra time for WAL replay
            RecoveryType.PARTIAL_RESTORE: 0.8,  # Faster for partial
            RecoveryType.CROSS_REGION: 2.0   # Extra time for cross-region
        }
        
        return int(base_duration * multipliers.get(recovery_type, 1.0))
    
    async def _generate_recovery_steps(
        self,
        recovery_type: RecoveryType,
        backups: List[BackupMetadata],
        target_timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """Generate detailed recovery steps"""
        
        steps = []
        
        # Step 1: Prepare recovery environment
        steps.append({
            "step": 1,
            "action": "prepare_environment",
            "description": "Prepare recovery environment and download backups",
            "estimated_duration": 300,  # 5 minutes
            "commands": [
                "mkdir -p /tmp/recovery",
                "cd /tmp/recovery"
            ]
        })
        
        # Step 2: Download and verify backups
        for i, backup in enumerate(backups):
            steps.append({
                "step": i + 2,
                "action": "download_backup",
                "description": f"Download and verify backup {backup.backup_id}",
                "backup_id": backup.backup_id,
                "location": backup.location,
                "checksum": backup.checksum,
                "estimated_duration": 180  # 3 minutes per backup
            })
        
        # Step 3: Restore full backup
        full_backup = backups[0]
        steps.append({
            "step": len(backups) + 2,
            "action": "restore_full_backup",
            "description": "Restore full database backup",
            "backup_id": full_backup.backup_id,
            "estimated_duration": int(full_backup.size_bytes / (1024**2) * 2)  # 2 seconds per MB
        })
        
        # Step 4: Apply incremental backups
        incremental_backups = backups[1:]
        for i, backup in enumerate(incremental_backups):
            steps.append({
                "step": len(backups) + 3 + i,
                "action": "apply_incremental",
                "description": f"Apply incremental backup {backup.backup_id}",
                "backup_id": backup.backup_id,
                "estimated_duration": int(backup.size_bytes / (1024**2))  # 1 second per MB
            })
        
        # Step 5: Point-in-time recovery if needed
        if recovery_type == RecoveryType.POINT_IN_TIME:
            steps.append({
                "step": len(steps) + 1,
                "action": "point_in_time_recovery",
                "description": f"Apply point-in-time recovery to {target_timestamp}",
                "target_timestamp": target_timestamp.isoformat(),
                "estimated_duration": 300
            })
        
        # Step 6: Verify recovery
        steps.append({
            "step": len(steps) + 1,
            "action": "verify_recovery",
            "description": "Verify database integrity and connectivity",
            "estimated_duration": 120
        })
        
        return steps
    
    async def _store_recovery_plan(self, plan: RecoveryPlan):
        """Store recovery plan in Redis"""
        try:
            plan_dict = {
                'recovery_id': plan.recovery_id,
                'recovery_type': plan.recovery_type.value,
                'target_timestamp': plan.target_timestamp.isoformat(),
                'source_backups': plan.source_backups,
                'estimated_duration': plan.estimated_duration,
                'estimated_rto': plan.estimated_rto,
                'estimated_rpo': plan.estimated_rpo,
                'steps': plan.steps,
                'dependencies': plan.dependencies
            }
            
            await self.redis_client.setex(
                f"recovery:plan:{plan.recovery_id}",
                86400 * 7,  # 7 days
                json.dumps(plan_dict)
            )
            
        except Exception as e:
            logger.error(f"Failed to store recovery plan: {e}")
    
    async def _initialize_backup_schedules(self):
        """Initialize automated backup schedules"""
        
        # Schedule full backups daily at 2 AM
        asyncio.create_task(self._schedule_full_backups())
        
        # Schedule incremental backups every 4 hours
        asyncio.create_task(self._schedule_incremental_backups())
        
        # Schedule transaction log backups every 15 minutes
        asyncio.create_task(self._schedule_transaction_log_backups())
        
        logger.info("Backup schedules initialized")
    
    async def _schedule_full_backups(self):
        """Schedule daily full backups"""
        while True:
            try:
                now = datetime.now()
                # Calculate next 2 AM
                next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                
                # Wait until next scheduled time
                wait_seconds = (next_run - now).total_seconds()
                await asyncio.sleep(wait_seconds)
                
                # Create full backup
                await self.create_database_backup(BackupType.FULL)
                
            except Exception as e:
                logger.error(f"Scheduled full backup failed: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry
    
    async def _schedule_incremental_backups(self):
        """Schedule incremental backups every 4 hours"""
        while True:
            try:
                await asyncio.sleep(4 * 3600)  # 4 hours
                await self.create_database_backup(BackupType.INCREMENTAL)
                
            except Exception as e:
                logger.error(f"Scheduled incremental backup failed: {e}")
                await asyncio.sleep(1800)  # Wait 30 minutes before retry
    
    async def _schedule_transaction_log_backups(self):
        """Schedule transaction log backups every 15 minutes"""
        while True:
            try:
                await asyncio.sleep(15 * 60)  # 15 minutes
                await self.create_database_backup(BackupType.TRANSACTION_LOG)
                
            except Exception as e:
                logger.error(f"Scheduled transaction log backup failed: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry


# Global instance
disaster_recovery_manager = DisasterRecoveryManager()