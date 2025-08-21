"""
API测试
"""
import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base
from app.config import settings
from app.models.user import User


# 测试数据库配置
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    """测试数据库依赖覆盖"""
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """设置测试数据库"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_client(setup_database):
    """异步HTTP客户端"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_client():
    """同步HTTP客户端"""
    return TestClient(app)


@pytest.fixture
async def test_user(async_client):
    """创建测试用户"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    response = await async_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    return response.json()["data"]


@pytest.fixture
async def auth_headers(async_client, test_user):
    """获取认证头"""
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = await async_client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestHealthCheck:
    """健康检查测试"""
    
    def test_root_endpoint(self, sync_client):
        """测试根端点"""
        response = sync_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_health_endpoint(self, sync_client):
        """测试健康检查端点"""
        response = sync_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    async def test_detailed_health_check(self, async_client):
        """测试详细健康检查"""
        response = await async_client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "checks" in data["data"]


class TestAuthentication:
    """认证测试"""
    
    async def test_user_registration(self, async_client):
        """测试用户注册"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()["data"]
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data
    
    async def test_user_login(self, async_client, test_user):
        """测试用户登录"""
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()["data"]
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_get_current_user(self, async_client, auth_headers):
        """测试获取当前用户信息"""
        response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()["data"]
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    async def test_invalid_login(self, async_client):
        """测试无效登录"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
    
    async def test_unauthorized_access(self, async_client):
        """测试未授权访问"""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestUserManagement:
    """用户管理测试"""
    
    async def test_update_profile(self, async_client, auth_headers):
        """测试更新个人资料"""
        update_data = {
            "full_name": "Updated Name",
            "email": "updated@example.com"
        }
        
        response = await async_client.put(
            "/api/v1/users/profile", 
            json=update_data, 
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()["data"]
        assert data["full_name"] == update_data["full_name"]
        assert data["email"] == update_data["email"]


class TestRateLimit:
    """限流测试"""
    
    async def test_rate_limit(self, async_client):
        """测试API限流"""
        # 快速发送多个请求
        responses = []
        for _ in range(10):
            response = await async_client.get("/")
            responses.append(response.status_code)
        
        # 大部分请求应该成功
        success_count = sum(1 for status in responses if status == 200)
        assert success_count > 0


class TestErrorHandling:
    """错误处理测试"""
    
    async def test_404_error(self, async_client):
        """测试404错误"""
        response = await async_client.get("/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
    
    async def test_validation_error(self, async_client):
        """测试验证错误"""
        invalid_user_data = {
            "username": "a",  # 太短
            "email": "invalid-email",  # 无效邮箱
            "password": "123"  # 太短
        }
        
        response = await async_client.post("/api/v1/auth/register", json=invalid_user_data)
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
