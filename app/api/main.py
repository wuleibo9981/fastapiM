"""
主API路由
汇总所有API路由
"""
from fastapi import APIRouter
from app.api.routes import auth, users, health

api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(health.router, prefix="/health", tags=["健康检查"])
