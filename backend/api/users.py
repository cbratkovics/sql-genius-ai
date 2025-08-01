from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from backend.core.database import get_db
from backend.core.deps import get_current_active_user, get_current_tenant, get_tenant_admin
from backend.models.user import User, UserRole
from backend.services.user import user_service


router = APIRouter(prefix="/users", tags=["Users"])


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: str
    last_login_at: Optional[str]
    total_queries: int
    queries_this_month: int
    
    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


class UserCreateRequest(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    role: UserRole = UserRole.USER
    password: str


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
        last_login_at=current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        total_queries=current_user.total_queries,
        queries_this_month=current_user.queries_this_month
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    update_data = user_update.model_dump(exclude_unset=True)
    updated_user = await user_service.update(db, current_user.id, update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        username=updated_user.username,
        full_name=updated_user.full_name,
        role=updated_user.role,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at.isoformat() if updated_user.created_at else None,
        last_login_at=updated_user.last_login_at.isoformat() if updated_user.last_login_at else None,
        total_queries=updated_user.total_queries,
        queries_this_month=updated_user.queries_this_month
    )


@router.get("/", response_model=List[UserResponse])
async def list_tenant_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_tenant_admin),
    current_tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    users = await user_service.get_by_tenant(
        db, 
        current_tenant.id, 
        skip=skip, 
        limit=limit
    )
    
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at.isoformat() if user.created_at else None,
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
            total_queries=user.total_queries,
            queries_this_month=user.queries_this_month
        )
        for user in users
    ]


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreateRequest,
    current_user: User = Depends(get_tenant_admin),
    current_tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    # Check if user already exists
    existing_user = await user_service.get_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_dict = user_data.model_dump()
    user_dict["tenant_id"] = current_tenant.id
    user_dict["is_verified"] = True  # Admin-created users are auto-verified
    
    created_user = await user_service.create(db, user_dict)
    
    return UserResponse(
        id=created_user.id,
        email=created_user.email,
        username=created_user.username,
        full_name=created_user.full_name,
        role=created_user.role,
        is_active=created_user.is_active,
        is_verified=created_user.is_verified,
        created_at=created_user.created_at.isoformat() if created_user.created_at else None,
        last_login_at=created_user.last_login_at.isoformat() if created_user.last_login_at else None,
        total_queries=created_user.total_queries,
        queries_this_month=created_user.queries_this_month
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_tenant_admin),
    current_tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    user = await user_service.get_by_id(db, user_id)
    
    if not user or user.tenant_id != current_tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        total_queries=user.total_queries,
        queries_this_month=user.queries_this_month
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdateRequest,
    current_user: User = Depends(get_tenant_admin),
    current_tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    user = await user_service.get_by_id(db, user_id)
    
    if not user or user.tenant_id != current_tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = user_update.model_dump(exclude_unset=True)
    updated_user = await user_service.update(db, user_id, update_data)
    
    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        username=updated_user.username,
        full_name=updated_user.full_name,
        role=updated_user.role,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at.isoformat() if updated_user.created_at else None,
        last_login_at=updated_user.last_login_at.isoformat() if updated_user.last_login_at else None,
        total_queries=updated_user.total_queries,
        queries_this_month=updated_user.queries_this_month
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_tenant_admin),
    current_tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    user = await user_service.get_by_id(db, user_id)
    
    if not user or user.tenant_id != current_tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    success = await user_service.delete(db, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
    
    return {"message": "User deleted successfully"}