from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from backend.models.user import User, UserRole
from backend.core.security import get_password_hash


class UserService:
    async def get_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    async def get_by_tenant(
        self, 
        db: AsyncSession, 
        tenant_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        result = await db.execute(
            select(User)
            .where(User.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, db: AsyncSession, user_data: dict) -> User:
        # Ensure unique username
        base_username = user_data.get("username", user_data["email"].split("@")[0])
        username = base_username
        counter = 1
        
        while await self.get_by_username(db, username):
            username = f"{base_username}{counter}"
            counter += 1
        
        user_data["username"] = username
        
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    async def update(
        self, 
        db: AsyncSession, 
        user_id: str, 
        user_data: dict
    ) -> Optional[User]:
        # Hash password if provided
        if "password" in user_data:
            user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**user_data)
        )
        await db.commit()
        return await self.get_by_id(db, user_id)
    
    async def delete(self, db: AsyncSession, user_id: str) -> bool:
        result = await db.execute(delete(User).where(User.id == user_id))
        await db.commit()
        return result.rowcount > 0
    
    async def activate(self, db: AsyncSession, user_id: str) -> Optional[User]:
        return await self.update(db, user_id, {"is_active": True})
    
    async def deactivate(self, db: AsyncSession, user_id: str) -> Optional[User]:
        return await self.update(db, user_id, {"is_active": False})
    
    async def verify_email(self, db: AsyncSession, user_id: str) -> Optional[User]:
        return await self.update(db, user_id, {"is_verified": True})
    
    async def update_role(
        self, 
        db: AsyncSession, 
        user_id: str, 
        role: UserRole
    ) -> Optional[User]:
        return await self.update(db, user_id, {"role": role})
    
    async def update_permissions(
        self, 
        db: AsyncSession, 
        user_id: str, 
        permissions: List[str]
    ) -> Optional[User]:
        return await self.update(db, user_id, {"permissions": permissions})
    
    async def increment_query_count(
        self, 
        db: AsyncSession, 
        user_id: str
    ) -> Optional[User]:
        user = await self.get_by_id(db, user_id)
        if user:
            user.total_queries += 1
            user.queries_this_month += 1
            user.last_query_at = datetime.utcnow()
            await db.commit()
            await db.refresh(user)
        return user
    
    async def reset_monthly_queries(self, db: AsyncSession, tenant_id: str):
        await db.execute(
            update(User)
            .where(User.tenant_id == tenant_id)
            .values(queries_this_month=0)
        )
        await db.commit()
    
    async def search_users(
        self, 
        db: AsyncSession, 
        tenant_id: str, 
        query: str, 
        limit: int = 10
    ) -> List[User]:
        result = await db.execute(
            select(User)
            .where(
                User.tenant_id == tenant_id,
                (User.full_name.ilike(f"%{query}%")) |
                (User.email.ilike(f"%{query}%")) |
                (User.username.ilike(f"%{query}%"))
            )
            .limit(limit)
        )
        return result.scalars().all()


user_service = UserService()