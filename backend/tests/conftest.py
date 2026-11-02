import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend.core.database import get_db
from backend.core.security import create_access_token, get_password_hash
from backend.main import app
from backend.models.base import Base
from backend.models.tenant import Tenant, TenantPlan, TenantStatus
from backend.models.user import User, UserRole
from backend.services.email import email_service


@pytest_asyncio.fixture
async def db_session():
    """Each test owns a fresh in-memory database, including application commits."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def override_get_db(db_session):
    async def test_db():
        yield db_session

    app.dependency_overrides[get_db] = test_db
    try:
        yield
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mail_outbox(monkeypatch):
    """Replace actual mail delivery and retain messages for behavior assertions."""
    messages = []

    async def deliver(to_email, subject, html_content, text_content=None):
        messages.append({"to_email": to_email, "subject": subject, "html": html_content})
        return True

    monkeypatch.setattr(email_service, "send_email", deliver)
    return messages


@pytest_asyncio.fixture
async def test_tenant(db_session):
    """Create a test tenant"""
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name="Test Company",
        slug="test-company",
        contact_email="admin@test.com",
        company_name="Test Company Inc.",
        plan=TenantPlan.PRO,
        status=TenantStatus.ACTIVE
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def test_user(db_session, test_tenant):
    """Create a test user"""
    user = User(
        id=str(uuid.uuid4()),
        email="user@test.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword"),
        tenant_id=test_tenant.id,
        role=UserRole.USER,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin_user(db_session, test_tenant):
    """Create a test admin user"""
    user = User(
        id=str(uuid.uuid4()),
        email="admin@test.com",
        username="testadmin",
        full_name="Test Admin",
        hashed_password=get_password_hash("adminpassword"),
        tenant_id=test_tenant.id,
        role=UserRole.TENANT_ADMIN,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def user_token(test_user):
    """Create an access token for test user"""
    return create_access_token(subject=test_user.id)


@pytest.fixture
def admin_token(test_admin_user):
    """Create an access token for test admin user"""
    return create_access_token(subject=test_admin_user.id)


@pytest_asyncio.fixture
async def client(override_get_db):
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers(user_token):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture 
def admin_auth_headers(admin_token):
    """Create admin authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing"""
    return """company,segment,monthly_spend,conversion_rate,employees,region
TechCorp,Enterprise,45000,0.12,500,North
DataInc,Mid-Market,15000,0.08,150,South
CloudCo,Enterprise,65000,0.15,800,West
StartupX,Mid-Market,8000,0.06,50,East
BigFirm,Enterprise,85000,0.18,1200,North"""


@pytest.fixture
def sample_query_request():
    """Sample query request data"""
    return {
        "natural_language_query": "Show me the total monthly spend by segment",
        "file_id": None
    }
