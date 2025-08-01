from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime, timedelta
from backend.models.tenant import Tenant, TenantStatus, TenantPlan
from backend.core.security import generate_tenant_encryption_key


class TenantService:
    async def get_by_id(self, db: AsyncSession, tenant_id: str) -> Optional[Tenant]:
        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        return result.scalar_one_or_none()
    
    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Tenant]:
        result = await db.execute(select(Tenant).where(Tenant.slug == slug))
        return result.scalar_one_or_none()
    
    async def get_by_stripe_customer_id(
        self, 
        db: AsyncSession, 
        customer_id: str
    ) -> Optional[Tenant]:
        result = await db.execute(
            select(Tenant).where(Tenant.stripe_customer_id == customer_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, db: AsyncSession, tenant_data: dict) -> Tenant:
        # Generate unique slug
        base_slug = tenant_data.get("slug", tenant_data["name"].lower().replace(" ", "-"))
        slug = base_slug
        counter = 1
        
        while await self.get_by_slug(db, slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        tenant_data["slug"] = slug
        
        # Generate encryption key
        tenant_data["encryption_key"] = generate_tenant_encryption_key()
        
        # Set trial period
        tenant_data["trial_ends_at"] = datetime.utcnow() + timedelta(days=14)
        
        # Set default features based on plan
        plan = tenant_data.get("plan", TenantPlan.FREE)
        tenant_data["features"] = self._get_plan_features(plan)
        
        tenant = Tenant(**tenant_data)
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        return tenant
    
    async def update(
        self, 
        db: AsyncSession, 
        tenant_id: str, 
        tenant_data: dict
    ) -> Optional[Tenant]:
        await db.execute(
            update(Tenant)
            .where(Tenant.id == tenant_id)
            .values(**tenant_data)
        )
        await db.commit()
        return await self.get_by_id(db, tenant_id)
    
    async def delete(self, db: AsyncSession, tenant_id: str) -> bool:
        result = await db.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await db.commit()
        return result.rowcount > 0
    
    async def activate(self, db: AsyncSession, tenant_id: str) -> Optional[Tenant]:
        return await self.update(db, tenant_id, {"status": TenantStatus.ACTIVE})
    
    async def suspend(self, db: AsyncSession, tenant_id: str) -> Optional[Tenant]:
        return await self.update(db, tenant_id, {"status": TenantStatus.SUSPENDED})
    
    async def cancel(self, db: AsyncSession, tenant_id: str) -> Optional[Tenant]:
        return await self.update(db, tenant_id, {"status": TenantStatus.CANCELLED})
    
    async def upgrade_plan(
        self, 
        db: AsyncSession, 
        tenant_id: str, 
        plan: TenantPlan
    ) -> Optional[Tenant]:
        features = self._get_plan_features(plan)
        limits = self._get_plan_limits(plan)
        
        update_data = {
            "plan": plan,
            "features": features,
            **limits
        }
        
        return await self.update(db, tenant_id, update_data)
    
    async def update_stripe_info(
        self, 
        db: AsyncSession, 
        tenant_id: str, 
        customer_id: str, 
        subscription_id: Optional[str] = None
    ) -> Optional[Tenant]:
        update_data = {"stripe_customer_id": customer_id}
        if subscription_id:
            update_data["stripe_subscription_id"] = subscription_id
        
        return await self.update(db, tenant_id, update_data)
    
    async def get_expired_trials(self, db: AsyncSession) -> List[Tenant]:
        now = datetime.utcnow()
        result = await db.execute(
            select(Tenant).where(
                Tenant.status == TenantStatus.TRIAL,
                Tenant.trial_ends_at < now
            )
        )
        return result.scalars().all()
    
    async def get_active_tenants(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Tenant]:
        result = await db.execute(
            select(Tenant)
            .where(Tenant.status == TenantStatus.ACTIVE)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def search_tenants(
        self, 
        db: AsyncSession, 
        query: str, 
        limit: int = 10
    ) -> List[Tenant]:
        result = await db.execute(
            select(Tenant)
            .where(
                (Tenant.name.ilike(f"%{query}%")) |
                (Tenant.company_name.ilike(f"%{query}%")) |
                (Tenant.contact_email.ilike(f"%{query}%"))
            )
            .limit(limit)
        )
        return result.scalars().all()
    
    def _get_plan_features(self, plan: TenantPlan) -> dict:
        features = {
            TenantPlan.FREE: {
                "custom_branding": False,
                "api_access": False,
                "advanced_analytics": False,
                "data_export": False,
                "team_collaboration": False,
                "priority_support": False,
                "sso": False
            },
            TenantPlan.PRO: {
                "custom_branding": True,
                "api_access": True,
                "advanced_analytics": True,
                "data_export": True,
                "team_collaboration": True,
                "priority_support": True,
                "sso": False
            },
            TenantPlan.ENTERPRISE: {
                "custom_branding": True,
                "api_access": True,
                "advanced_analytics": True,
                "data_export": True,
                "team_collaboration": True,
                "priority_support": True,
                "sso": True,
                "custom_integrations": True,
                "dedicated_support": True,
                "audit_logs": True
            }
        }
        return features.get(plan, features[TenantPlan.FREE])
    
    def _get_plan_limits(self, plan: TenantPlan) -> dict:
        limits = {
            TenantPlan.FREE: {
                "monthly_query_limit": 3,
                "monthly_storage_limit_mb": 100,
                "max_users": 1,
                "max_concurrent_queries": 1
            },
            TenantPlan.PRO: {
                "monthly_query_limit": -1,  # Unlimited
                "monthly_storage_limit_mb": 5000,  # 5GB
                "max_users": 10,
                "max_concurrent_queries": 5
            },
            TenantPlan.ENTERPRISE: {
                "monthly_query_limit": -1,  # Unlimited
                "monthly_storage_limit_mb": -1,  # Unlimited
                "max_users": -1,  # Unlimited
                "max_concurrent_queries": 20
            }
        }
        return limits.get(plan, limits[TenantPlan.FREE])


tenant_service = TenantService()