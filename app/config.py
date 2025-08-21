"""
配置管理模块
支持多环境配置和动态配置更新
"""
from typing import Optional, List
from pydantic import BaseSettings, validator
from functools import lru_cache
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    app_name: str = "FastAPI Scalable App"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # 数据库配置
    database_url: Optional[str] = None
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    redis_pool_size: int = 10
    
    # JWT配置
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS配置
    allowed_hosts: List[str] = ["*"]
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # 服务发现配置
    consul_host: str = "localhost"
    consul_port: int = 8500
    service_name: str = "fastapi-service"
    service_id: Optional[str] = None
    health_check_interval: int = 10
    
    # 监控配置
    metrics_enabled: bool = True
    prometheus_port: int = 9090
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    
    # 限流配置
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # 任务队列配置
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    @validator("database_url", pre=True)
    def build_database_url(cls, v: Optional[str]) -> str:
        """构建数据库连接URL"""
        if v:
            return v
        # 默认使用SQLite（开发环境）
        return "sqlite:///./app.db"
    
    @validator("service_id", pre=True)
    def build_service_id(cls, v: Optional[str], values: dict) -> str:
        """构建服务ID"""
        if v:
            return v
        import socket
        hostname = socket.gethostname()
        port = values.get("port", 8000)
        return f"{values.get('service_name', 'fastapi-service')}-{hostname}-{port}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class DevelopmentSettings(Settings):
    """开发环境配置"""
    debug: bool = True
    log_level: str = "DEBUG"
    database_url: str = "sqlite:///./dev.db"


class ProductionSettings(Settings):
    """生产环境配置"""
    debug: bool = False
    log_level: str = "INFO"
    workers: int = 4
    # 生产环境必须设置安全的secret_key
    
    @validator("secret_key")
    def validate_secret_key(cls, v: str) -> str:
        if v == "your-secret-key-change-in-production":
            raise ValueError("Must set a secure secret key in production")
        return v


class TestSettings(Settings):
    """测试环境配置"""
    database_url: str = "sqlite:///./test.db"
    redis_url: str = "redis://localhost:6379/15"  # 使用不同的Redis数据库


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()


# 全局配置实例
settings = get_settings()
