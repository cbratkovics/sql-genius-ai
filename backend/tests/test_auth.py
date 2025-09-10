from httpx import AsyncClient


class TestAuth:
    """Test authentication endpoints"""
    
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration"""
        response = await client.post("/api/v1/auth/register", json={
            "email": "newuser@test.com",
            "password": "securepassword123",
            "full_name": "New User",
            "company_name": "New Company"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "tenant_id" in data
        assert "message" in data
    
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with duplicate email"""
        response = await client.post("/api/v1/auth/register", json={
            "email": test_user.email,
            "password": "password123",
            "full_name": "Duplicate User"
        })
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login"""
        response = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
    
    async def test_login_invalid_credentials(self, client: AsyncClient, test_user):
        """Test login with invalid credentials"""
        response = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user"""
        response = await client.post("/api/v1/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "password123"
        })
        
        assert response.status_code == 401
    
    async def test_refresh_token_success(self, client: AsyncClient, test_user):
        """Test successful token refresh"""
        # First login to get tokens
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword"
        })
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token"""
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        
        assert response.status_code == 401
    
    async def test_password_reset_request(self, client: AsyncClient, test_user):
        """Test password reset request"""
        response = await client.post("/api/v1/auth/password-reset/request", json={
            "email": test_user.email
        })
        
        assert response.status_code == 200
        assert "reset link has been sent" in response.json()["message"]
    
    async def test_password_reset_nonexistent_email(self, client: AsyncClient):
        """Test password reset for nonexistent email"""
        response = await client.post("/api/v1/auth/password-reset/request", json={
            "email": "nonexistent@test.com"
        })
        
        # Should still return success for security
        assert response.status_code == 200
        assert "reset link has been sent" in response.json()["message"]
    
    async def test_logout(self, client: AsyncClient):
        """Test logout endpoint"""
        response = await client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]