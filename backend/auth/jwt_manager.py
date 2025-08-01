import asyncio
import jwt
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import redis.asyncio as redis
import json
import logging
from dataclasses import dataclass
from enum import Enum
import uuid
from backend.core.config import settings

logger = logging.getLogger(__name__)


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    ID = "id"
    SERVICE = "service"


@dataclass
class JWTClaims:
    sub: str  # Subject (user ID)
    iss: str  # Issuer
    aud: List[str]  # Audience
    exp: int  # Expiration time
    iat: int  # Issued at
    nbf: int  # Not before
    jti: str  # JWT ID
    token_type: TokenType
    scope: List[str]  # Permissions/scopes
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None


class JWTKeyManager:
    """Manages RSA key pairs with automatic rotation"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.key_size = 2048
        self.algorithm = "RS256"
        self.key_rotation_interval = 86400  # 24 hours
        self.key_retention_period = 172800  # 48 hours
        
    async def initialize(self):
        """Initialize key manager and ensure keys exist"""
        current_key = await self._get_current_key()
        if not current_key:
            await self._generate_new_key_pair()
            logger.info("Generated initial RSA key pair")
        
        # Schedule key rotation
        asyncio.create_task(self._key_rotation_scheduler())
    
    async def _generate_new_key_pair(self) -> str:
        """Generate new RSA key pair and store in Redis"""
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size,
            backend=default_backend()
        )
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        # Get public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        # Generate key ID
        key_id = str(uuid.uuid4())
        
        # Store keys in Redis
        key_data = {
            "key_id": key_id,
            "private_key": private_pem,
            "public_key": public_pem,
            "created_at": datetime.utcnow().isoformat(),
            "algorithm": self.algorithm
        }
        
        # Store current key
        await self.redis_client.setex(
            f"jwt:current_key", 
            self.key_retention_period, 
            json.dumps(key_data)
        )
        
        # Store in key history for verification
        await self.redis_client.setex(
            f"jwt:key:{key_id}",
            self.key_retention_period,
            json.dumps(key_data)
        )
        
        # Update key rotation timestamp
        await self.redis_client.setex(
            "jwt:last_rotation",
            self.key_retention_period,
            datetime.utcnow().isoformat()
        )
        
        logger.info(f"Generated new RSA key pair with ID: {key_id}")
        return key_id
    
    async def _get_current_key(self) -> Optional[Dict]:
        """Get current signing key"""
        try:
            key_data = await self.redis_client.get("jwt:current_key")
            if key_data:
                return json.loads(key_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get current key: {e}")
            return None
    
    async def get_public_key(self, key_id: str) -> Optional[str]:
        """Get public key by key ID for verification"""
        try:
            key_data = await self.redis_client.get(f"jwt:key:{key_id}")
            if key_data:
                return json.loads(key_data)["public_key"]
            return None
        except Exception as e:
            logger.error(f"Failed to get public key {key_id}: {e}")
            return None
    
    async def get_jwks(self) -> Dict:
        """Get JSON Web Key Set for public consumption"""
        try:
            # Get all active keys
            keys = []
            pattern = "jwt:key:*"
            async for key in self.redis_client.scan_iter(match=pattern):
                key_data = await self.redis_client.get(key)
                if key_data:
                    data = json.loads(key_data)
                    
                    # Convert PEM to JWK format
                    public_key = serialization.load_pem_public_key(
                        data["public_key"].encode(),
                        backend=default_backend()
                    )
                    
                    public_numbers = public_key.public_numbers()
                    
                    jwk = {
                        "kty": "RSA",
                        "use": "sig",
                        "kid": data["key_id"],
                        "alg": data["algorithm"],
                        "n": self._int_to_base64url(public_numbers.n),
                        "e": self._int_to_base64url(public_numbers.e)
                    }
                    keys.append(jwk)
            
            return {"keys": keys}
            
        except Exception as e:
            logger.error(f"Failed to generate JWKS: {e}")
            return {"keys": []}
    
    def _int_to_base64url(self, value: int) -> str:
        """Convert integer to base64url encoding"""
        import base64
        byte_length = (value.bit_length() + 7) // 8
        value_bytes = value.to_bytes(byte_length, byteorder='big')
        return base64.urlsafe_b64encode(value_bytes).decode('ascii').rstrip('=')
    
    async def _key_rotation_scheduler(self):
        """Background task for automatic key rotation"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                
                last_rotation = await self.redis_client.get("jwt:last_rotation")
                if last_rotation:
                    last_rotation_time = datetime.fromisoformat(last_rotation)
                    if datetime.utcnow() - last_rotation_time > timedelta(seconds=self.key_rotation_interval):
                        await self._generate_new_key_pair()
                        logger.info("Automatic key rotation completed")
                
            except Exception as e:
                logger.error(f"Key rotation scheduler error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error


class UnifiedAuthService:
    """Enterprise authentication service with advanced features"""
    
    def __init__(self):
        self.key_manager = JWTKeyManager()
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.issuer = f"https://{settings.PROJECT_NAME.lower().replace(' ', '-')}.com"
        self.session_timeout = 28800  # 8 hours
        self.max_sessions_per_user = 5
        
    async def initialize(self):
        """Initialize authentication service"""
        await self.key_manager.initialize()
        logger.info("Unified authentication service initialized")
    
    async def create_tokens(
        self,
        user_id: str,
        tenant_id: str,
        scopes: List[str],
        audience: List[str] = None,
        device_id: str = None,
        ip_address: str = None
    ) -> Dict[str, str]:
        """Create access and refresh tokens"""
        
        session_id = str(uuid.uuid4())
        current_key = await self.key_manager._get_current_key()
        
        if not current_key:
            raise Exception("No signing key available")
        
        now = datetime.utcnow()
        
        # Create access token claims
        access_claims = JWTClaims(
            sub=user_id,
            iss=self.issuer,
            aud=audience or ["api"],
            exp=int((now + timedelta(minutes=15)).timestamp()),
            iat=int(now.timestamp()),
            nbf=int(now.timestamp()),
            jti=str(uuid.uuid4()),
            token_type=TokenType.ACCESS,
            scope=scopes,
            tenant_id=tenant_id,
            session_id=session_id,
            device_id=device_id,
            ip_address=ip_address
        )
        
        # Create refresh token claims
        refresh_claims = JWTClaims(
            sub=user_id,
            iss=self.issuer,
            aud=audience or ["api"],
            exp=int((now + timedelta(days=7)).timestamp()),
            iat=int(now.timestamp()),
            nbf=int(now.timestamp()),
            jti=str(uuid.uuid4()),
            token_type=TokenType.REFRESH,
            scope=["refresh"],
            tenant_id=tenant_id,
            session_id=session_id,
            device_id=device_id,
            ip_address=ip_address
        )
        
        # Sign tokens
        access_token = await self._sign_token(access_claims, current_key)
        refresh_token = await self._sign_token(refresh_claims, current_key)
        
        # Store session
        await self._store_session(session_id, user_id, device_id, ip_address)
        
        # Enforce session limits
        await self._enforce_session_limits(user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 900,  # 15 minutes
            "session_id": session_id
        }
    
    async def _sign_token(self, claims: JWTClaims, key_data: Dict) -> str:
        """Sign JWT token with RSA private key"""
        headers = {
            "alg": key_data["algorithm"],
            "typ": "JWT",
            "kid": key_data["key_id"]
        }
        
        # Convert claims to dict
        payload = {
            "sub": claims.sub,
            "iss": claims.iss,
            "aud": claims.aud,
            "exp": claims.exp,
            "iat": claims.iat,
            "nbf": claims.nbf,
            "jti": claims.jti,
            "token_type": claims.token_type.value,
            "scope": claims.scope
        }
        
        # Add optional claims
        if claims.tenant_id:
            payload["tenant_id"] = claims.tenant_id
        if claims.session_id:
            payload["session_id"] = claims.session_id
        if claims.device_id:
            payload["device_id"] = claims.device_id
        if claims.ip_address:
            payload["ip_address"] = claims.ip_address
        
        # Load private key
        private_key = serialization.load_pem_private_key(
            key_data["private_key"].encode(),
            password=None,
            backend=default_backend()
        )
        
        # Sign token
        return jwt.encode(
            payload,
            private_key,
            algorithm=key_data["algorithm"],
            headers=headers
        )
    
    async def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get("kid")
            
            if not key_id:
                logger.warning("Token missing key ID")
                return None
            
            # Get public key
            public_key_pem = await self.key_manager.get_public_key(key_id)
            if not public_key_pem:
                logger.warning(f"Public key not found for key ID: {key_id}")
                return None
            
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )
            
            # Verify and decode token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                issuer=self.issuer,
                options={"verify_exp": True, "verify_nbf": True}
            )
            
            # Check if session is still valid
            session_id = payload.get("session_id")
            if session_id:
                session_valid = await self._is_session_valid(session_id)
                if not session_valid:
                    logger.warning(f"Invalid session: {session_id}")
                    return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    async def _store_session(
        self,
        session_id: str,
        user_id: str,
        device_id: str = None,
        ip_address: str = None
    ):
        """Store session information in Redis"""
        session_data = {
            "user_id": user_id,
            "device_id": device_id,
            "ip_address": ip_address,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        # Store session
        await self.redis_client.setex(
            f"session:{session_id}",
            self.session_timeout,
            json.dumps(session_data)
        )
        
        # Add to user's active sessions
        await self.redis_client.sadd(f"user_sessions:{user_id}", session_id)
        await self.redis_client.expire(f"user_sessions:{user_id}", self.session_timeout)
    
    async def _is_session_valid(self, session_id: str) -> bool:
        """Check if session is still valid"""
        try:
            session_data = await self.redis_client.get(f"session:{session_id}")
            return session_data is not None
        except Exception:
            return False
    
    async def _enforce_session_limits(self, user_id: str):
        """Enforce maximum sessions per user"""
        try:
            sessions = await self.redis_client.smembers(f"user_sessions:{user_id}")
            
            if len(sessions) > self.max_sessions_per_user:
                # Remove oldest sessions
                session_times = []
                for session_id in sessions:
                    session_data = await self.redis_client.get(f"session:{session_id}")
                    if session_data:
                        data = json.loads(session_data)
                        session_times.append((session_id, data["created_at"]))
                
                # Sort by creation time and remove oldest
                session_times.sort(key=lambda x: x[1])
                sessions_to_remove = session_times[:-self.max_sessions_per_user]
                
                for session_id, _ in sessions_to_remove:
                    await self.revoke_session(session_id)
                    
        except Exception as e:
            logger.error(f"Failed to enforce session limits: {e}")
    
    async def revoke_session(self, session_id: str):
        """Revoke a specific session"""
        try:
            # Get session data to find user
            session_data = await self.redis_client.get(f"session:{session_id}")
            if session_data:
                data = json.loads(session_data)
                user_id = data["user_id"]
                
                # Remove from user's active sessions
                await self.redis_client.srem(f"user_sessions:{user_id}", session_id)
            
            # Delete session
            await self.redis_client.delete(f"session:{session_id}")
            
        except Exception as e:
            logger.error(f"Failed to revoke session {session_id}: {e}")
    
    async def revoke_all_user_sessions(self, user_id: str):
        """Revoke all sessions for a user"""
        try:
            sessions = await self.redis_client.smembers(f"user_sessions:{user_id}")
            
            for session_id in sessions:
                await self.redis_client.delete(f"session:{session_id}")
            
            await self.redis_client.delete(f"user_sessions:{user_id}")
            
        except Exception as e:
            logger.error(f"Failed to revoke all sessions for user {user_id}: {e}")
    
    async def get_jwks_endpoint(self) -> Dict:
        """Get JWKS for public key distribution"""
        return await self.key_manager.get_jwks()


# Global instance
auth_service = UnifiedAuthService()