"""
通用Pydantic模型
"""
from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional, Any
from datetime import datetime

DataType = TypeVar('DataType')


class ResponseModel(BaseModel, Generic[DataType]):
    """通用响应模型"""
    code: int = 200
    message: str = "Success"
    data: Optional[DataType] = None
    timestamp: datetime = datetime.utcnow()
    request_id: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[DataType]):
    """分页响应模型"""
    items: List[DataType]
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(
        cls,
        items: List[DataType],
        total: int,
        page: int,
        size: int
    ) -> "PaginatedResponse[DataType]":
        """创建分页响应"""
        pages = (total + size - 1) // size  # 向上取整
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    timestamp: float
    service: str
    version: str
    checks: Optional[dict] = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    code: int
    message: str
    detail: Optional[str] = None
    timestamp: datetime = datetime.utcnow()
    request_id: Optional[str] = None


class SuccessResponse(BaseModel):
    """成功响应模型"""
    message: str = "Operation completed successfully"
    timestamp: datetime = datetime.utcnow()
    request_id: Optional[str] = None
