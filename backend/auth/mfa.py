import pyotp
import qrcode
import io
import base64
from typing import Dict, Optional, List
import redis.asyncio as redis
import json
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from backend.core.config import settings
from backend.services.email import email_service

logger = logging.getLogger(__name__)


class MFAMethod(str, Enum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODES = "backup_codes"
    WEBAUTHN = "webauthn"


class MFAStatus(str, Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    PENDING_SETUP = "pending_setup"
    LOCKED = "locked"


@dataclass
class MFAChallenge:
    challenge_id: str
    user_id: str
    method: MFAMethod
    challenge_data: Dict
    expires_at: datetime
    attempts: int = 0
    max_attempts: int = 3


class MultiFactorAuthService:
    """Enterprise multi-factor authentication service"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.challenge_timeout = 300  # 5 minutes
        self.backup_codes_count = 10
        self.rate_limit_window = 900  # 15 minutes
        self.max_attempts_per_window = 5
        
    async def setup_totp(self, user_id: str, user_email: str) -> Dict[str, str]:
        """Setup TOTP for a user"""
        try:
            # Generate secret
            secret = pyotp.random_base32()
            
            # Create provisioning URI
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=user_email,
                issuer_name="SQL Genius AI"
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            qr_code_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Store temporary secret (not activated until verified)
            await self.redis_client.setex(
                f"mfa:totp_setup:{user_id}",
                600,  # 10 minutes
                json.dumps({
                    "secret": secret,
                    "created_at": datetime.utcnow().isoformat()
                })
            )
            
            return {
                "secret": secret,
                "provisioning_uri": provisioning_uri,
                "qr_code": f"data:image/png;base64,{qr_code_base64}",
                "backup_codes": await self._generate_backup_codes(user_id)
            }
            
        except Exception as e:
            logger.error(f"TOTP setup failed for user {user_id}: {e}")
            raise Exception("Failed to setup TOTP")
    
    async def verify_totp_setup(self, user_id: str, token: str) -> bool:
        """Verify TOTP setup and activate MFA"""
        try:
            # Get temporary secret
            setup_data = await self.redis_client.get(f"mfa:totp_setup:{user_id}")
            if not setup_data:
                return False
            
            data = json.loads(setup_data)
            secret = data["secret"]
            
            # Verify token
            totp = pyotp.TOTP(secret)
            if not totp.verify(token, valid_window=1):
                return False
            
            # Activate TOTP
            await self._store_mfa_method(user_id, MFAMethod.TOTP, {
                "secret": secret,
                "enabled": True
            })
            
            # Clean up temporary data
            await self.redis_client.delete(f"mfa:totp_setup:{user_id}")
            
            logger.info(f"TOTP activated for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"TOTP verification failed for user {user_id}: {e}")
            return False
    
    async def create_mfa_challenge(
        self, 
        user_id: str, 
        preferred_method: Optional[MFAMethod] = None
    ) -> Optional[MFAChallenge]:
        """Create MFA challenge for user"""
        try:
            # Check rate limiting
            if not await self._check_rate_limit(user_id):
                logger.warning(f"MFA rate limit exceeded for user {user_id}")
                return None
            
            # Get user's MFA methods
            methods = await self.get_user_mfa_methods(user_id)
            if not methods:
                return None
            
            # Select method
            method = preferred_method if preferred_method in methods else methods[0]
            
            challenge_id = secrets.token_urlsafe(32)
            challenge_data = {}
            
            if method == MFAMethod.TOTP:
                challenge_data = {"message": "Enter your authenticator code"}
                
            elif method == MFAMethod.EMAIL:
                code = self._generate_verification_code()
                challenge_data = {"code": code, "message": "Check your email for verification code"}
                
                # Send email
                await self._send_email_challenge(user_id, code)
                
            elif method == MFAMethod.SMS:
                code = self._generate_verification_code()
                challenge_data = {"code": code, "message": "Check your phone for verification code"}
                
                # In production, integrate with SMS service
                logger.info(f"SMS code for {user_id}: {code}")
            
            # Create challenge
            challenge = MFAChallenge(
                challenge_id=challenge_id,
                user_id=user_id,
                method=method,
                challenge_data=challenge_data,
                expires_at=datetime.utcnow() + timedelta(seconds=self.challenge_timeout)
            )
            
            # Store challenge
            await self.redis_client.setex(
                f"mfa:challenge:{challenge_id}",
                self.challenge_timeout,
                json.dumps({
                    "user_id": user_id,
                    "method": method.value,
                    "challenge_data": challenge_data,
                    "expires_at": challenge.expires_at.isoformat(),
                    "attempts": 0
                })
            )
            
            return challenge
            
        except Exception as e:
            logger.error(f"Failed to create MFA challenge for user {user_id}: {e}")
            return None
    
    async def verify_mfa_challenge(self, challenge_id: str, response: str) -> bool:
        """Verify MFA challenge response"""
        try:
            # Get challenge
            challenge_data = await self.redis_client.get(f"mfa:challenge:{challenge_id}")
            if not challenge_data:
                return False
            
            challenge = json.loads(challenge_data)
            user_id = challenge["user_id"]
            method = MFAMethod(challenge["method"])
            
            # Check expiration
            expires_at = datetime.fromisoformat(challenge["expires_at"])
            if datetime.utcnow() > expires_at:
                await self.redis_client.delete(f"mfa:challenge:{challenge_id}")
                return False
            
            # Check attempts
            if challenge["attempts"] >= 3:
                await self.redis_client.delete(f"mfa:challenge:{challenge_id}")
                return False
            
            # Verify based on method
            verified = False
            
            if method == MFAMethod.TOTP:
                verified = await self._verify_totp(user_id, response)
                
            elif method in [MFAMethod.EMAIL, MFAMethod.SMS]:
                expected_code = challenge["challenge_data"]["code"]
                verified = response == expected_code
                
            elif method == MFAMethod.BACKUP_CODES:
                verified = await self._verify_backup_code(user_id, response)
            
            if verified:
                # Clean up challenge
                await self.redis_client.delete(f"mfa:challenge:{challenge_id}")
                
                # Log successful verification
                await self._log_mfa_event(user_id, method, "success")
                return True
            else:
                # Increment attempts
                challenge["attempts"] += 1
                await self.redis_client.setex(
                    f"mfa:challenge:{challenge_id}",
                    self.challenge_timeout,
                    json.dumps(challenge)
                )
                
                # Log failed attempt
                await self._log_mfa_event(user_id, method, "failed")
                return False
                
        except Exception as e:
            logger.error(f"MFA verification failed for challenge {challenge_id}: {e}")
            return False
    
    async def _verify_totp(self, user_id: str, token: str) -> bool:
        """Verify TOTP token"""
        try:
            method_data = await self.redis_client.get(f"mfa:method:{user_id}:totp")
            if not method_data:
                return False
            
            data = json.loads(method_data)
            if not data.get("enabled", False):
                return False
            
            secret = data["secret"]
            totp = pyotp.TOTP(secret)
            
            return totp.verify(token, valid_window=1)
            
        except Exception as e:
            logger.error(f"TOTP verification failed for user {user_id}: {e}")
            return False
    
    async def _verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verify and consume backup code"""
        try:
            codes_data = await self.redis_client.get(f"mfa:backup_codes:{user_id}")
            if not codes_data:
                return False
            
            codes = json.loads(codes_data)
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            
            if code_hash in codes["codes"] and not codes["codes"][code_hash]["used"]:
                # Mark code as used
                codes["codes"][code_hash]["used"] = True
                codes["codes"][code_hash]["used_at"] = datetime.utcnow().isoformat()
                
                # Update stored codes
                await self.redis_client.set(
                    f"mfa:backup_codes:{user_id}",
                    json.dumps(codes)
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Backup code verification failed for user {user_id}: {e}")
            return False
    
    async def get_user_mfa_methods(self, user_id: str) -> List[MFAMethod]:
        """Get enabled MFA methods for user"""
        try:
            methods = []
            
            # Check TOTP
            totp_data = await self.redis_client.get(f"mfa:method:{user_id}:totp")
            if totp_data:
                data = json.loads(totp_data)
                if data.get("enabled", False):
                    methods.append(MFAMethod.TOTP)
            
            # Check backup codes
            codes_data = await self.redis_client.get(f"mfa:backup_codes:{user_id}")
            if codes_data:
                codes = json.loads(codes_data)
                # Check if any unused codes exist
                unused_codes = [c for c in codes["codes"].values() if not c["used"]]
                if unused_codes:
                    methods.append(MFAMethod.BACKUP_CODES)
            
            return methods
            
        except Exception as e:
            logger.error(f"Failed to get MFA methods for user {user_id}: {e}")
            return []
    
    async def _generate_backup_codes(self, user_id: str) -> List[str]:
        """Generate backup codes for user"""
        try:
            codes = []
            codes_data = {"codes": {}, "created_at": datetime.utcnow().isoformat()}
            
            for _ in range(self.backup_codes_count):
                code = self._generate_backup_code()
                codes.append(code)
                
                code_hash = hashlib.sha256(code.encode()).hexdigest()
                codes_data["codes"][code_hash] = {
                    "used": False,
                    "created_at": datetime.utcnow().isoformat()
                }
            
            # Store backup codes
            await self.redis_client.set(
                f"mfa:backup_codes:{user_id}",
                json.dumps(codes_data)
            )
            
            return codes
            
        except Exception as e:
            logger.error(f"Failed to generate backup codes for user {user_id}: {e}")
            return []
    
    def _generate_backup_code(self) -> str:
        """Generate a single backup code"""
        return f"{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}"
    
    def _generate_verification_code(self) -> str:
        """Generate 6-digit verification code"""
        return f"{secrets.randbelow(1000000):06d}"
    
    async def _send_email_challenge(self, user_id: str, code: str):
        """Send email with MFA code"""
        try:
            # In production, get user email from database
            user_email = f"user{user_id}@example.com"  # Placeholder
            
            subject = "SQL Genius AI - Verification Code"
            html_content = f"""
            <h2>Verification Code</h2>
            <p>Your verification code is: <strong>{code}</strong></p>
            <p>This code will expire in 5 minutes.</p>
            <p>If you didn't request this code, please contact support.</p>
            """
            
            await email_service.send_email(user_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send email challenge: {e}")
    
    async def _check_rate_limit(self, user_id: str) -> bool:
        """Check MFA rate limiting"""
        try:
            key = f"mfa:rate_limit:{user_id}"
            current_count = await self.redis_client.get(key)
            
            if current_count is None:
                await self.redis_client.setex(key, self.rate_limit_window, 1)
                return True
            
            count = int(current_count)
            if count >= self.max_attempts_per_window:
                return False
            
            await self.redis_client.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed for user {user_id}: {e}")
            return False
    
    async def _store_mfa_method(self, user_id: str, method: MFAMethod, data: Dict):
        """Store MFA method configuration"""
        try:
            await self.redis_client.set(
                f"mfa:method:{user_id}:{method.value}",
                json.dumps({
                    **data,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                })
            )
        except Exception as e:
            logger.error(f"Failed to store MFA method {method} for user {user_id}: {e}")
    
    async def _log_mfa_event(self, user_id: str, method: MFAMethod, result: str):
        """Log MFA event for auditing"""
        try:
            event = {
                "user_id": user_id,
                "method": method.value,
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "ip_address": None  # Would get from request context
            }
            
            # Store in audit log
            await self.redis_client.lpush(
                f"mfa:audit:{user_id}",
                json.dumps(event)
            )
            
            # Keep only last 100 events
            await self.redis_client.ltrim(f"mfa:audit:{user_id}", 0, 99)
            
        except Exception as e:
            logger.error(f"Failed to log MFA event: {e}")
    
    async def disable_mfa(self, user_id: str, method: MFAMethod) -> bool:
        """Disable specific MFA method"""
        try:
            await self.redis_client.delete(f"mfa:method:{user_id}:{method.value}")
            
            if method == MFAMethod.TOTP:
                await self.redis_client.delete(f"mfa:backup_codes:{user_id}")
            
            logger.info(f"MFA method {method} disabled for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable MFA method {method} for user {user_id}: {e}")
            return False
    
    async def get_mfa_status(self, user_id: str) -> Dict[str, any]:
        """Get MFA status for user"""
        try:
            methods = await self.get_user_mfa_methods(user_id)
            
            return {
                "enabled": len(methods) > 0,
                "methods": [method.value for method in methods],
                "backup_codes_available": MFAMethod.BACKUP_CODES in methods
            }
            
        except Exception as e:
            logger.error(f"Failed to get MFA status for user {user_id}: {e}")
            return {"enabled": False, "methods": [], "backup_codes_available": False}


# Global instance
mfa_service = MultiFactorAuthService()