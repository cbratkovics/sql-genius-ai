from typing import Dict, List, Set, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import redis.asyncio as redis
import json
import logging
from datetime import datetime
from backend.core.config import settings

logger = logging.getLogger(__name__)


class ResourceType(str, Enum):
    USER = "user"
    TENANT = "tenant"
    QUERY = "query"
    FILE = "file"
    DASHBOARD = "dashboard"
    API_KEY = "api_key"
    BILLING = "billing"
    ANALYTICS = "analytics"
    SYSTEM = "system"


class Action(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MANAGE = "manage"
    ADMIN = "admin"


class Effect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class Permission:
    """Fine-grained permission definition"""
    resource_type: ResourceType
    action: Action
    effect: Effect = Effect.ALLOW
    conditions: Dict[str, Any] = field(default_factory=dict)
    resource_ids: Optional[List[str]] = None
    
    def __str__(self) -> str:
        resource_part = f"{self.resource_type.value}"
        if self.resource_ids:
            resource_part += f":{','.join(self.resource_ids)}"
        return f"{self.effect.value}:{resource_part}:{self.action.value}"


@dataclass
class Role:
    """Role with permissions and metadata"""
    name: str
    description: str
    permissions: List[Permission] = field(default_factory=list)
    inherits_from: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_system_role: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RBACService:
    """Enterprise Role-Based Access Control service"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.cache_ttl = 3600  # 1 hour
        self.system_roles = self._define_system_roles()
        
    async def initialize(self):
        """Initialize RBAC system with default roles"""
        await self._create_system_roles()
        logger.info("RBAC service initialized")
    
    def _define_system_roles(self) -> Dict[str, Role]:
        """Define system-level roles"""
        return {
            "super_admin": Role(
                name="super_admin",
                description="System administrator with full access",
                permissions=[
                    Permission(ResourceType.SYSTEM, Action.ADMIN),
                    Permission(ResourceType.TENANT, Action.MANAGE),
                    Permission(ResourceType.USER, Action.MANAGE),
                    Permission(ResourceType.BILLING, Action.MANAGE),
                    Permission(ResourceType.ANALYTICS, Action.READ),
                ],
                is_system_role=True
            ),
            
            "tenant_admin": Role(
                name="tenant_admin",
                description="Tenant administrator",
                permissions=[
                    Permission(ResourceType.USER, Action.MANAGE, conditions={"same_tenant": True}),
                    Permission(ResourceType.QUERY, Action.MANAGE, conditions={"same_tenant": True}),
                    Permission(ResourceType.FILE, Action.MANAGE, conditions={"same_tenant": True}),
                    Permission(ResourceType.DASHBOARD, Action.MANAGE, conditions={"same_tenant": True}),
                    Permission(ResourceType.API_KEY, Action.MANAGE, conditions={"same_tenant": True}),
                    Permission(ResourceType.BILLING, Action.READ, conditions={"same_tenant": True}),
                    Permission(ResourceType.ANALYTICS, Action.READ, conditions={"same_tenant": True}),
                ],
                is_system_role=True
            ),
            
            "user": Role(
                name="user",
                description="Standard user",
                permissions=[
                    Permission(ResourceType.QUERY, Action.CREATE, conditions={"same_tenant": True}),
                    Permission(ResourceType.QUERY, Action.READ, conditions={"owner_or_shared": True}),
                    Permission(ResourceType.QUERY, Action.UPDATE, conditions={"owner": True}),
                    Permission(ResourceType.QUERY, Action.DELETE, conditions={"owner": True}),
                    Permission(ResourceType.FILE, Action.CREATE, conditions={"same_tenant": True}),
                    Permission(ResourceType.FILE, Action.READ, conditions={"owner_or_shared": True}),
                    Permission(ResourceType.FILE, Action.UPDATE, conditions={"owner": True}),
                    Permission(ResourceType.FILE, Action.DELETE, conditions={"owner": True}),
                    Permission(ResourceType.DASHBOARD, Action.CREATE, conditions={"same_tenant": True}),
                    Permission(ResourceType.DASHBOARD, Action.READ, conditions={"owner_or_shared": True}),
                    Permission(ResourceType.DASHBOARD, Action.UPDATE, conditions={"owner": True}),
                ],
                is_system_role=True
            ),
            
            "viewer": Role(
                name="viewer",
                description="Read-only user",
                permissions=[
                    Permission(ResourceType.QUERY, Action.READ, conditions={"shared": True}),
                    Permission(ResourceType.FILE, Action.READ, conditions={"shared": True}),
                    Permission(ResourceType.DASHBOARD, Action.READ, conditions={"shared": True}),
                ],
                is_system_role=True
            ),
            
            "analyst": Role(
                name="analyst",
                description="Data analyst with advanced query permissions",
                inherits_from=["user"],
                permissions=[
                    Permission(ResourceType.QUERY, Action.EXECUTE, conditions={"advanced_queries": True}),
                    Permission(ResourceType.ANALYTICS, Action.READ, conditions={"same_tenant": True}),
                ],
                is_system_role=True
            ),
            
            "api_user": Role(
                name="api_user",
                description="API access user",
                permissions=[
                    Permission(ResourceType.QUERY, Action.CREATE, conditions={"api_access": True}),
                    Permission(ResourceType.QUERY, Action.READ, conditions={"api_access": True}),
                    Permission(ResourceType.FILE, Action.CREATE, conditions={"api_access": True}),
                    Permission(ResourceType.FILE, Action.READ, conditions={"api_access": True}),
                ],
                is_system_role=True
            )
        }
    
    async def _create_system_roles(self):
        """Create system roles in Redis"""
        for role_name, role in self.system_roles.items():
            await self._store_role(role)
    
    async def create_role(
        self,
        name: str,
        description: str,
        permissions: List[Permission] = None,
        inherits_from: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Role:
        """Create a custom role"""
        try:
            # Check if role already exists
            existing_role = await self.get_role(name)
            if existing_role:
                raise ValueError(f"Role '{name}' already exists")
            
            role = Role(
                name=name,
                description=description,
                permissions=permissions or [],
                inherits_from=inherits_from or [],
                metadata=metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            await self._store_role(role)
            logger.info(f"Created role: {name}")
            return role
            
        except Exception as e:
            logger.error(f"Failed to create role {name}: {e}")
            raise
    
    async def get_role(self, role_name: str) -> Optional[Role]:
        """Get role by name"""
        try:
            role_data = await self.redis_client.get(f"rbac:role:{role_name}")
            if not role_data:
                return None
            
            data = json.loads(role_data)
            return self._deserialize_role(data)
            
        except Exception as e:
            logger.error(f"Failed to get role {role_name}: {e}")
            return None
    
    async def update_role(self, role_name: str, **updates) -> Optional[Role]:
        """Update role"""
        try:
            role = await self.get_role(role_name)
            if not role:
                return None
            
            if role.is_system_role:
                raise ValueError("Cannot update system role")
            
            # Update fields
            for field, value in updates.items():
                if hasattr(role, field):
                    setattr(role, field, value)
            
            role.updated_at = datetime.utcnow()
            await self._store_role(role)
            
            # Invalidate user permission caches
            await self._invalidate_user_caches_for_role(role_name)
            
            logger.info(f"Updated role: {role_name}")
            return role
            
        except Exception as e:
            logger.error(f"Failed to update role {role_name}: {e}")
            raise
    
    async def delete_role(self, role_name: str) -> bool:
        """Delete custom role"""
        try:
            role = await self.get_role(role_name)
            if not role:
                return False
            
            if role.is_system_role:
                raise ValueError("Cannot delete system role")
            
            # Check if role is assigned to any users
            users_with_role = await self._get_users_with_role(role_name)
            if users_with_role:
                raise ValueError(f"Role is assigned to {len(users_with_role)} users")
            
            await self.redis_client.delete(f"rbac:role:{role_name}")
            logger.info(f"Deleted role: {role_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete role {role_name}: {e}")
            raise
    
    async def assign_role_to_user(self, user_id: str, role_name: str, tenant_id: str = None):
        """Assign role to user"""
        try:
            # Verify role exists
            role = await self.get_role(role_name)
            if not role:
                raise ValueError(f"Role '{role_name}' does not exist")
            
            # Get current user roles
            user_roles = await self._get_user_roles(user_id)
            
            # Add role assignment
            assignment = {
                "role": role_name,
                "tenant_id": tenant_id,
                "assigned_at": datetime.utcnow().isoformat(),
                "assigned_by": None  # Would get from context
            }
            
            user_roles.append(assignment)
            
            # Store updated roles
            await self.redis_client.set(
                f"rbac:user_roles:{user_id}",
                json.dumps(user_roles)
            )
            
            # Invalidate user permission cache
            await self._invalidate_user_cache(user_id)
            
            logger.info(f"Assigned role {role_name} to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to assign role {role_name} to user {user_id}: {e}")
            raise
    
    async def revoke_role_from_user(self, user_id: str, role_name: str, tenant_id: str = None):
        """Revoke role from user"""
        try:
            user_roles = await self._get_user_roles(user_id)
            
            # Remove role assignment
            user_roles = [
                r for r in user_roles 
                if not (r["role"] == role_name and r.get("tenant_id") == tenant_id)
            ]
            
            # Store updated roles
            await self.redis_client.set(
                f"rbac:user_roles:{user_id}",
                json.dumps(user_roles)
            )
            
            # Invalidate user permission cache
            await self._invalidate_user_cache(user_id)
            
            logger.info(f"Revoked role {role_name} from user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to revoke role {role_name} from user {user_id}: {e}")
            raise
    
    async def check_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        action: Action,
        resource_id: str = None,
        context: Dict[str, Any] = None
    ) -> bool:
        """Check if user has permission for action on resource"""
        try:
            # Get user permissions (cached)
            permissions = await self._get_user_permissions(user_id)
            
            # Check permissions
            return self._evaluate_permissions(
                permissions, resource_type, action, resource_id, context or {}
            )
            
        except Exception as e:
            logger.error(f"Permission check failed for user {user_id}: {e}")
            return False
    
    async def get_user_permissions(self, user_id: str) -> List[Permission]:
        """Get all permissions for user"""
        try:
            return await self._get_user_permissions(user_id)
        except Exception as e:
            logger.error(f"Failed to get permissions for user {user_id}: {e}")
            return []
    
    async def _get_user_permissions(self, user_id: str) -> List[Permission]:
        """Get user permissions with caching"""
        try:
            # Check cache first
            cached_permissions = await self.redis_client.get(f"rbac:user_permissions:{user_id}")
            if cached_permissions:
                data = json.loads(cached_permissions)
                return [self._deserialize_permission(p) for p in data]
            
            # Get user roles
            user_roles = await self._get_user_roles(user_id)
            
            # Collect permissions from all roles
            all_permissions = []
            processed_roles = set()
            
            for role_assignment in user_roles:
                role_name = role_assignment["role"]
                await self._collect_role_permissions(
                    role_name, all_permissions, processed_roles
                )
            
            # Cache permissions
            serialized_permissions = [self._serialize_permission(p) for p in all_permissions]
            await self.redis_client.setex(
                f"rbac:user_permissions:{user_id}",
                self.cache_ttl,
                json.dumps(serialized_permissions)
            )
            
            return all_permissions
            
        except Exception as e:
            logger.error(f"Failed to get user permissions for {user_id}: {e}")
            return []
    
    async def _collect_role_permissions(
        self,
        role_name: str,
        permissions: List[Permission],
        processed_roles: Set[str]
    ):
        """Recursively collect permissions from role hierarchy"""
        if role_name in processed_roles:
            return
        
        processed_roles.add(role_name)
        
        role = await self.get_role(role_name)
        if not role:
            return
        
        # Add role's direct permissions
        permissions.extend(role.permissions)
        
        # Recursively add inherited permissions
        for inherited_role in role.inherits_from:
            await self._collect_role_permissions(inherited_role, permissions, processed_roles)
    
    def _evaluate_permissions(
        self,
        permissions: List[Permission],
        resource_type: ResourceType,
        action: Action,
        resource_id: str = None,
        context: Dict[str, Any] = None
    ) -> bool:
        """Evaluate permissions against request"""
        context = context or {}
        
        # Separate allow and deny permissions
        allow_permissions = [p for p in permissions if p.effect == Effect.ALLOW]
        deny_permissions = [p for p in permissions if p.effect == Effect.DENY]
        
        # Check deny permissions first (explicit deny overrides allow)
        for permission in deny_permissions:
            if self._permission_matches(permission, resource_type, action, resource_id, context):
                return False
        
        # Check allow permissions
        for permission in allow_permissions:
            if self._permission_matches(permission, resource_type, action, resource_id, context):
                return True
        
        return False
    
    def _permission_matches(
        self,
        permission: Permission,
        resource_type: ResourceType,
        action: Action,
        resource_id: str = None,
        context: Dict[str, Any] = None
    ) -> bool:
        """Check if permission matches the request"""
        # Check resource type
        if permission.resource_type != resource_type:
            return False
        
        # Check action (ADMIN action grants all actions)
        if permission.action != action and permission.action != Action.ADMIN:
            return False
        
        # Check resource IDs if specified
        if permission.resource_ids and resource_id:
            if resource_id not in permission.resource_ids:
                return False
        
        # Evaluate conditions
        return self._evaluate_conditions(permission.conditions, context)
    
    def _evaluate_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate permission conditions"""
        if not conditions:
            return True
        
        for condition_key, condition_value in conditions.items():
            if condition_key == "same_tenant":
                if condition_value and context.get("user_tenant_id") != context.get("resource_tenant_id"):
                    return False
            
            elif condition_key == "owner":
                if condition_value and context.get("user_id") != context.get("resource_owner_id"):
                    return False
            
            elif condition_key == "owner_or_shared":
                user_id = context.get("user_id")
                owner_id = context.get("resource_owner_id")
                shared_with = context.get("resource_shared_with", [])
                
                if condition_value and user_id != owner_id and user_id not in shared_with:
                    return False
            
            elif condition_key == "shared":
                user_id = context.get("user_id")
                shared_with = context.get("resource_shared_with", [])
                
                if condition_value and user_id not in shared_with:
                    return False
            
            elif condition_key == "api_access":
                if condition_value and not context.get("is_api_request", False):
                    return False
            
            elif condition_key == "advanced_queries":
                if condition_value and not context.get("has_advanced_features", False):
                    return False
        
        return True
    
    async def _get_user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user role assignments"""
        try:
            roles_data = await self.redis_client.get(f"rbac:user_roles:{user_id}")
            if roles_data:
                return json.loads(roles_data)
            return []
        except Exception as e:
            logger.error(f"Failed to get user roles for {user_id}: {e}")
            return []
    
    async def _store_role(self, role: Role):
        """Store role in Redis"""
        try:
            role_data = self._serialize_role(role)
            await self.redis_client.set(
                f"rbac:role:{role.name}",
                json.dumps(role_data)
            )
        except Exception as e:
            logger.error(f"Failed to store role {role.name}: {e}")
            raise
    
    def _serialize_role(self, role: Role) -> Dict[str, Any]:
        """Serialize role to dict"""
        return {
            "name": role.name,
            "description": role.description,
            "permissions": [self._serialize_permission(p) for p in role.permissions],
            "inherits_from": role.inherits_from,
            "metadata": role.metadata,
            "is_system_role": role.is_system_role,
            "created_at": role.created_at.isoformat() if role.created_at else None,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None
        }
    
    def _deserialize_role(self, data: Dict[str, Any]) -> Role:
        """Deserialize role from dict"""
        return Role(
            name=data["name"],
            description=data["description"],
            permissions=[self._deserialize_permission(p) for p in data["permissions"]],
            inherits_from=data["inherits_from"],
            metadata=data["metadata"],
            is_system_role=data["is_system_role"],
            created_at=datetime.fromisoformat(data["created_at"]) if data["created_at"] else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data["updated_at"] else None
        )
    
    def _serialize_permission(self, permission: Permission) -> Dict[str, Any]:
        """Serialize permission to dict"""
        return {
            "resource_type": permission.resource_type.value,
            "action": permission.action.value,
            "effect": permission.effect.value,
            "conditions": permission.conditions,
            "resource_ids": permission.resource_ids
        }
    
    def _deserialize_permission(self, data: Dict[str, Any]) -> Permission:
        """Deserialize permission from dict"""
        return Permission(
            resource_type=ResourceType(data["resource_type"]),
            action=Action(data["action"]),
            effect=Effect(data["effect"]),
            conditions=data["conditions"],
            resource_ids=data["resource_ids"]
        )
    
    async def _invalidate_user_cache(self, user_id: str):
        """Invalidate user permission cache"""
        await self.redis_client.delete(f"rbac:user_permissions:{user_id}")
    
    async def _invalidate_user_caches_for_role(self, role_name: str):
        """Invalidate caches for all users with specific role"""
        try:
            users_with_role = await self._get_users_with_role(role_name)
            for user_id in users_with_role:
                await self._invalidate_user_cache(user_id)
        except Exception as e:
            logger.error(f"Failed to invalidate caches for role {role_name}: {e}")
    
    async def _get_users_with_role(self, role_name: str) -> List[str]:
        """Get list of users with specific role"""
        try:
            users = []
            pattern = "rbac:user_roles:*"
            
            async for key in self.redis_client.scan_iter(match=pattern):
                user_id = key.split(":")[-1]
                user_roles = await self._get_user_roles(user_id)
                
                if any(r["role"] == role_name for r in user_roles):
                    users.append(user_id)
            
            return users
            
        except Exception as e:
            logger.error(f"Failed to get users with role {role_name}: {e}")
            return []


# Global instance
rbac_service = RBACService()