import pytest
from httpx import AsyncClient


class TestUsers:
    """Test user management endpoints"""
    
    async def test_get_current_user(self, client: AsyncClient, auth_headers, test_user):
        """Test getting current user profile"""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert data["full_name"] == test_user.full_name
        assert data["role"] == test_user.role.value
    
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication"""
        response = await client.get("/api/v1/users/me")
        
        assert response.status_code == 401
    
    async def test_update_current_user(self, client: AsyncClient, auth_headers):
        """Test updating current user profile"""
        update_data = {
            "full_name": "Updated Name",
            "phone_number": "555-1234",
            "department": "Engineering"
        }
        
        response = await client.put("/api/v1/users/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
    
    async def test_list_tenant_users_as_admin(self, client: AsyncClient, admin_auth_headers, test_user):
        """Test listing tenant users as admin"""
        response = await client.get("/api/v1/users/", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    async def test_list_tenant_users_as_regular_user(self, client: AsyncClient, auth_headers):
        """Test listing tenant users as regular user (should fail)"""
        response = await client.get("/api/v1/users/", headers=auth_headers)
        
        assert response.status_code == 403
    
    async def test_create_user_as_admin(self, client: AsyncClient, admin_auth_headers):
        """Test creating user as admin"""
        user_data = {
            "email": "newemployee@test.com",
            "username": "newemployee",
            "full_name": "New Employee",
            "role": "user",
            "password": "temppassword123"
        }
        
        response = await client.post("/api/v1/users/", json=user_data, headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["is_verified"] == True  # Admin-created users are auto-verified
    
    async def test_create_user_duplicate_email(self, client: AsyncClient, admin_auth_headers, test_user):
        """Test creating user with duplicate email"""
        user_data = {
            "email": test_user.email,
            "username": "duplicate",
            "full_name": "Duplicate User",
            "role": "user",
            "password": "password123"
        }
        
        response = await client.post("/api/v1/users/", json=user_data, headers=admin_auth_headers)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    async def test_get_user_as_admin(self, client: AsyncClient, admin_auth_headers, test_user):
        """Test getting specific user as admin"""
        response = await client.get(f"/api/v1/users/{test_user.id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
    
    async def test_get_nonexistent_user(self, client: AsyncClient, admin_auth_headers):
        """Test getting nonexistent user"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/users/{fake_id}", headers=admin_auth_headers)
        
        assert response.status_code == 404
    
    async def test_update_user_as_admin(self, client: AsyncClient, admin_auth_headers, test_user):
        """Test updating user as admin"""
        update_data = {
            "full_name": "Admin Updated Name",
            "department": "Updated Department"
        }
        
        response = await client.put(
            f"/api/v1/users/{test_user.id}", 
            json=update_data, 
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Admin Updated Name"
    
    async def test_delete_user_as_admin(self, client: AsyncClient, admin_auth_headers, db_session, test_tenant):
        """Test deleting user as admin"""
        from backend.models.user import User, UserRole
        from backend.core.security import get_password_hash
        import uuid
        
        # Create a user to delete
        user_to_delete = User(
            id=str(uuid.uuid4()),
            email="delete@test.com", 
            username="deleteme",
            full_name="Delete Me",
            hashed_password=get_password_hash("password"),
            tenant_id=test_tenant.id,
            role=UserRole.USER,
            is_active=True,
            is_verified=True
        )
        db_session.add(user_to_delete)
        await db_session.commit()
        await db_session.refresh(user_to_delete)
        
        response = await client.delete(f"/api/v1/users/{user_to_delete.id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
    
    async def test_delete_self_forbidden(self, client: AsyncClient, admin_auth_headers, test_admin_user):
        """Test that admin cannot delete themselves"""
        response = await client.delete(f"/api/v1/users/{test_admin_user.id}", headers=admin_auth_headers)
        
        assert response.status_code == 400
        assert "Cannot delete yourself" in response.json()["detail"]