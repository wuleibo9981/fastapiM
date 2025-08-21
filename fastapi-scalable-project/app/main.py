"""
FastAPI应用主入口
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.config import settings
from app.database import init_database, close_database
from app.middleware import setup_middleware
from app.api.main import api_router
from app.services.discovery import service_discovery


# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("Starting FastAPI application...")
    
    try:
        # 初始化数据库
        await init_database()
        logger.info("Database initialized")
        
        # 注册服务到服务发现
        if await service_discovery.register_service():
            logger.info("Service registered to discovery")
        else:
            logger.warning("Failed to register service to discovery")
        
        logger.info("Application startup completed")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down FastAPI application...")
    
    try:
        # 从服务发现注销服务
        await service_discovery.deregister_service()
        logger.info("Service deregistered from discovery")
        
        # 关闭数据库连接
        await close_database()
        logger.info("Database connections closed")
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error(f"Application shutdown error: {e}")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="支持多节点扩展的FastAPI项目框架",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# 设置中间件
app = setup_middleware(app)

# 包含API路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "FastAPI Scalable Project",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs_url": "/docs" if settings.debug else "disabled"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.app_version,
        "environment": settings.environment
    }


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """404异常处理"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Resource not found",
            "path": str(request.url.path),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


if __name__ == "__main__":
    # 开发环境直接运行
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
        log_level=settings.log_level.lower()
    )
