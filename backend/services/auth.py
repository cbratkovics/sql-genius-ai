from typing import Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from backend.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    generate_password_reset_token,
    verify_password_reset_token,
    generate_email_verification_token,
    verify_email_verification_token
)
from backend.models.user import User
from backend.models.tenant import Tenant
from backend.services.user import user_service
from backend.services.tenant import tenant_service
from backend.services.email import email_service


class AuthService:
    async def authenticate_user(
        self, 
        db: AsyncSession, 
        email: str, 
        password: str
    ) -> Optional[User]:
        user = await user_service.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    async def login(
        self, 
        db: AsyncSession, 
        email: str, 
        password: str,
        ip_address: Optional[str] = None
    ) -> dict:
        user = await self.authenticate_user(db, email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please verify your email first"
            )
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip_address
        user.failed_login_attempts = 0
        await db.commit()
        
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "tenant_id": user.tenant_id
            }
        }
    
    async def register(
        self, 
        db: AsyncSession,
        email: str,
        password: str,
        full_name: str,
        company_name: Optional[str] = None
    ) -> dict:
        # Check if user already exists
        existing_user = await user_service.get_by_email(db, email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create tenant first
        tenant_data = {
            "name": company_name or f"{full_name}'s Workspace",
            "slug": f"tenant-{hash(email) % 100000}",
            "contact_email": email,
            "company_name": company_name
        }
        tenant = await tenant_service.create(db, tenant_data)
        
        # Create user
        user_data = {
            "email": email,
            "username": email.split("@")[0],
            "full_name": full_name,
            "hashed_password": get_password_hash(password),
            "tenant_id": tenant.id,
            "role": "tenant_admin"
        }
        user = await user_service.create(db, user_data)
        
        # Send verification email
        verification_token = generate_email_verification_token(email)
        await email_service.send_verification_email(
            email, 
            full_name, 
            verification_token
        )
        
        return {
            "message": "Registration successful. Please check your email to verify your account.",
            "user_id": user.id,
            "tenant_id": tenant.id
        }
    
    async def verify_email(self, db: AsyncSession, token: str) -> dict:
        email = verify_email_verification_token(token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        user = await user_service.get_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        user.is_verified = True
        await db.commit()
        
        return {"message": "Email verified successfully"}
    
    async def request_password_reset(
        self, 
        db: AsyncSession, 
        email: str
    ) -> dict:
        user = await user_service.get_by_email(db, email)
        if not user:
            return {"message": "If the email exists, a reset link has been sent"}
        
        reset_token = generate_password_reset_token(email)
        await email_service.send_password_reset_email(
            email, 
            user.full_name, 
            reset_token
        )
        
        return {"message": "If the email exists, a reset link has been sent"}
    
    async def reset_password(
        self, 
        db: AsyncSession, 
        token: str, 
        new_password: str
    ) -> dict:
        email = verify_password_reset_token(token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        user = await user_service.get_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.hashed_password = get_password_hash(new_password)
        await db.commit()
        
        return {"message": "Password reset successfully"}
    
    async def refresh_token(self, db: AsyncSession, refresh_token: str) -> dict:
        try:
            from jose import jwt
            from backend.core.config import settings
            
            payload = jwt.decode(
                refresh_token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            user_id = payload.get("sub")
            token_type = payload.get("type")
            
            if token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
                
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user = await user_service.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        access_token = create_access_token(subject=user.id)
        new_refresh_token = create_refresh_token(subject=user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }


auth_service = AuthService()