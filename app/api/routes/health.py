"""
健康检查API路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
import time
import psutil
from typing import Dict, Any

from app.database import get_db, get_redis
from app.dependencies import health_check_db, health_check_redis
from app.schemas.common import HealthCheckResponse, ResponseModel
from app.config import settings

router = APIRouter()


@router.get("/", response_model=HealthCheckResponse)
async def health_check():
    """基础健康检查"""
    return HealthCheckResponse(
        status="healthy",
        timestamp=time.time(),
        service=settings.service_name,
        version=settings.app_version
    )


@router.get("/detailed", response_model=ResponseModel[Dict[str, Any]])
async def detailed_health_check(
    db_healthy: bool = Depends(health_check_db),
    redis_healthy: bool = Depends(health_check_redis)
):
    """详细健康检查"""
    
    # 系统信息
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # 检查结果
    checks = {
        "database": {
            "status": "healthy" if db_healthy else "unhealthy",
            "healthy": db_healthy
        },
        "redis": {
            "status": "healthy" if redis_healthy else "unhealthy",
            "healthy": redis_healthy
        },
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        }
    }
    
    # 整体健康状态
    overall_healthy = db_healthy and redis_healthy and cpu_percent < 90 and memory.percent < 90
    
    health_data = {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": time.time(),
        "service": settings.service_name,
        "version": settings.app_version,
        "checks": checks
    }
    
    return ResponseModel(
        message="健康检查完成",
        data=health_data
    )


@router.get("/liveness")
async def liveness_probe():
    """存活探针（Kubernetes）"""
    return {"status": "alive", "timestamp": time.time()}


@router.get("/readiness")
async def readiness_probe(
    db_healthy: bool = Depends(health_check_db),
    redis_healthy: bool = Depends(health_check_redis)
):
    """就绪探针（Kubernetes）"""
    ready = db_healthy and redis_healthy
    
    if not ready:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )
    
    return {
        "status": "ready",
        "timestamp": time.time(),
        "checks": {
            "database": db_healthy,
            "redis": redis_healthy
        }
    }


@router.get("/metrics")
async def get_metrics():
    """获取Prometheus指标"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    
    if not settings.metrics_enabled:
        return {"message": "Metrics disabled"}
    
    metrics_data = generate_latest()
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
