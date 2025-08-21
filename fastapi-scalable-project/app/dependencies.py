"""
依赖注入模块
提供各种服务的依赖注入
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from typing import Optional, AsyncGenerator
import redis.asyncio as redis
from datetime import datetime, timedelta

from app.database import get_db, get_redis
from app.config import settings
from app.models.user import User
from app.schemas.user import UserInDB

# JWT安全方案
security = HTTPBearer()


class AuthenticationError(HTTPException):
    """认证异常"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """授权异常"""
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def verify_token(token: str) -> dict:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise AuthenticationError()
        return payload
    except JWTError:
        raise AuthenticationError()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> UserInDB:
    """获取当前用户"""
    payload = await verify_token(credentials.credentials)
    username = payload.get("sub")
    
    # 从数据库获取用户信息
    user = await User.get_by_username(db, username)
    if user is None:
        raise AuthenticationError()
    
    return UserInDB.from_orm(user)


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: UserInDB = Depends(get_current_active_user)
) -> UserInDB:
    """获取当前管理员用户"""
    if not current_user.is_superuser:
        raise AuthorizationError()
    return current_user


class RateLimiter:
    """限流器"""
    
    def __init__(self, requests: int = 100, window: int = 60):
        self.requests = requests
        self.window = window
    
    async def __call__(
        self,
        request: Request,
        redis_client: redis.Redis = Depends(get_redis)
    ):
        """限流检查"""
        if not settings.rate_limit_enabled:
            return
        
        # 获取客户端IP
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        # 检查当前请求数
        current_requests = await redis_client.get(key)
        if current_requests is None:
            # 首次请求，设置计数器
            await redis_client.setex(key, self.window, 1)
        else:
            current_requests = int(current_requests)
            if current_requests >= self.requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            # 增加计数器
            await redis_client.incr(key)


# 预定义的限流器
default_rate_limiter = RateLimiter(
    requests=settings.rate_limit_requests,
    window=settings.rate_limit_window
)

strict_rate_limiter = RateLimiter(requests=10, window=60)
loose_rate_limiter = RateLimiter(requests=1000, window=60)


class ServiceDependency:
    """服务依赖注入基类"""
    
    def __init__(self):
        self._instance = None
    
    async def get_instance(self):
        """获取服务实例"""
        if self._instance is None:
            self._instance = await self._create_instance()
        return self._instance
    
    async def _create_instance(self):
        """创建服务实例（子类实现）"""
        raise NotImplementedError


class CacheService(ServiceDependency):
    """缓存服务"""
    
    async def _create_instance(self):
        return await get_redis()


class NotificationService(ServiceDependency):
    """通知服务"""
    
    async def _create_instance(self):
        # 这里可以集成邮件、短信、推送等服务
        from app.services.notification import NotificationManager
        return NotificationManager()


# 服务实例
cache_service = CacheService()
notification_service = NotificationService()


async def get_cache_service() -> redis.Redis:
    """获取缓存服务"""
    return await cache_service.get_instance()


async def get_notification_service():
    """获取通知服务"""
    return await notification_service.get_instance()


class PaginationParams:
    """分页参数"""
    
    def __init__(self, page: int = 1, size: int = 20):
        self.page = max(1, page)
        self.size = min(100, max(1, size))  # 限制最大页面大小
        self.offset = (self.page - 1) * self.size
        self.limit = self.size


def get_pagination_params(page: int = 1, size: int = 20) -> PaginationParams:
    """获取分页参数"""
    return PaginationParams(page, size)


# 健康检查依赖
async def health_check_db(db: AsyncSession = Depends(get_db)) -> bool:
    """数据库健康检查"""
    try:
        await db.execute("SELECT 1")
        return True
    except Exception:
        return False


async def health_check_redis(redis_client: redis.Redis = Depends(get_redis)) -> bool:
    """Redis健康检查"""
    try:
        await redis_client.ping()
        return True
    except Exception:
        return False
