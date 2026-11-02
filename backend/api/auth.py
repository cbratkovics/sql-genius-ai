from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from pydantic import AfterValidator, BaseModel, EmailStr
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import validate_password_length
from backend.services.auth import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, AfterValidator(validate_password_length)]
    full_name: str
    company_name: str | None = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: Annotated[str, AfterValidator(validate_password_length)]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenResponse(RefreshTokenResponse):
    user: dict


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    ip_address = http_request.client.host if http_request.client else None
    
    try:
        result = await auth_service.login(
            db, 
            request.email, 
            request.password,
            ip_address
        )
        return result
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        ) from exc


@router.post("/register")
async def register(
    request: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        result = await auth_service.register(
            db,
            request.email,
            request.password,
            request.full_name,
            request.company_name
        )
        return result
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        ) from exc


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        result = await auth_service.verify_email(db, token)
        return result
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        ) from exc


@router.post("/password-reset/request")
async def request_password_reset(
    request: PasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        result = await auth_service.request_password_reset(db, request.email)
        return result
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        ) from exc


@router.post("/password-reset/confirm")
async def reset_password(
    request: PasswordResetConfirm,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        result = await auth_service.reset_password(
            db, 
            request.token, 
            request.new_password
        )
        return result
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        ) from exc


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        result = await auth_service.refresh_token(db, request.refresh_token)
        return result
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        ) from exc


@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out"}