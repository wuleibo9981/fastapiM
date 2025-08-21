"""
中间件模块
包含各种请求处理中间件
"""
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge
import time
import uuid
import logging
import structlog
from typing import Callable
import traceback

from app.config import settings

# 日志配置
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus指标
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Active HTTP requests'
)

ERROR_COUNT = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'error_type']
)


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始
        start_time = time.time()
        
        # 构建日志上下文
        log_context = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
        }
        
        # 记录请求开始日志
        logger.info("Request started", **log_context)
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 更新日志上下文
            log_context.update({
                "status_code": response.status_code,
                "process_time": process_time,
            })
            
            # 记录请求完成日志
            if response.status_code >= 400:
                logger.warning("Request completed with error", **log_context)
            else:
                logger.info("Request completed successfully", **log_context)
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 更新日志上下文
            log_context.update({
                "error": str(e),
                "error_type": type(e).__name__,
                "process_time": process_time,
                "traceback": traceback.format_exc(),
            })
            
            # 记录错误日志
            logger.error("Request failed with exception", **log_context)
            
            # 返回错误响应
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id},
                headers={"X-Request-ID": request_id}
            )


class MetricsMiddleware(BaseHTTPMiddleware):
    """Prometheus指标中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.metrics_enabled:
            return await call_next(request)
        
        # 增加活跃请求计数
        ACTIVE_REQUESTS.inc()
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            duration = time.time() - start_time
            
            # 获取路由路径（用于指标标签）
            endpoint = request.url.path
            if hasattr(request.state, "route"):
                endpoint = request.state.route.path
            
            # 记录指标
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # 记录错误指标
            endpoint = request.url.path
            ERROR_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                error_type=type(e).__name__
            ).inc()
            raise
            
        finally:
            # 减少活跃请求计数
            ACTIVE_REQUESTS.dec()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """健康检查中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 对健康检查端点进行快速响应
        if request.url.path in ["/health", "/health/", "/healthz"]:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "healthy",
                    "timestamp": time.time(),
                    "service": settings.service_name,
                    "version": settings.app_version
                }
            )
        
        return await call_next(request)


def setup_middleware(app):
    """设置应用中间件"""
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    
    # 受信任主机中间件
    if settings.allowed_hosts != ["*"]:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts
        )
    
    # 自定义中间件（按顺序添加）
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(HealthCheckMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    return app
