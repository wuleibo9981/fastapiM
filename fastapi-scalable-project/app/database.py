"""
数据库连接管理模块
支持多种数据库和连接池管理
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import redis.asyncio as redis
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy基础类
Base = declarative_base()
metadata = MetaData()

# 数据库引擎配置
engine_kwargs = {
    "poolclass": QueuePool,
    "pool_size": settings.database_pool_size,
    "max_overflow": settings.database_max_overflow,
    "pool_timeout": settings.database_pool_timeout,
    "pool_pre_ping": True,  # 连接健康检查
    "pool_recycle": 3600,   # 连接回收时间（1小时）
}

# 同步数据库引擎（用于迁移等操作）
sync_engine = create_engine(
    settings.database_url,
    **engine_kwargs
)

# 异步数据库引擎
async_database_url = settings.database_url
if async_database_url.startswith("sqlite"):
    async_database_url = async_database_url.replace("sqlite://", "sqlite+aiosqlite://")
elif async_database_url.startswith("postgresql"):
    async_database_url = async_database_url.replace("postgresql://", "postgresql+asyncpg://")
elif async_database_url.startswith("mysql"):
    async_database_url = async_database_url.replace("mysql://", "mysql+aiomysql://")

async_engine = create_async_engine(
    async_database_url,
    **engine_kwargs
)

# 会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 同步会话（用于迁移）
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self._async_engine = async_engine
        self._sync_engine = sync_engine
        
    async def create_tables(self):
        """创建数据表"""
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    async def drop_tables(self):
        """删除数据表"""
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            
    async def close(self):
        """关闭数据库连接"""
        await self._async_engine.dispose()
        
    async def health_check(self) -> bool:
        """数据库健康检查"""
        try:
            async with self._async_engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# 全局数据库管理器实例
db_manager = DatabaseManager()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（上下文管理器）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """依赖注入：获取数据库会话"""
    async with get_db_session() as session:
        yield session


class RedisManager:
    """Redis连接管理器"""
    
    def __init__(self):
        self._pool = None
        self._redis = None
        
    async def connect(self):
        """连接Redis"""
        self._pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_pool_size,
            decode_responses=True
        )
        self._redis = redis.Redis(connection_pool=self._pool)
        
    async def disconnect(self):
        """断开Redis连接"""
        if self._redis:
            await self._redis.close()
        if self._pool:
            await self._pool.disconnect()
            
    async def health_check(self) -> bool:
        """Redis健康检查"""
        try:
            await self._redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
            
    async def get_client(self) -> redis.Redis:
        """获取Redis客户端"""
        if not self._redis:
            await self.connect()
        return self._redis


# 全局Redis管理器实例
redis_manager = RedisManager()


async def get_redis() -> redis.Redis:
    """依赖注入：获取Redis客户端"""
    return await redis_manager.get_client()


# 数据库初始化和清理
async def init_database():
    """初始化数据库连接"""
    try:
        await db_manager.create_tables()
        await redis_manager.connect()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_database():
    """关闭数据库连接"""
    try:
        await db_manager.close()
        await redis_manager.disconnect()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
