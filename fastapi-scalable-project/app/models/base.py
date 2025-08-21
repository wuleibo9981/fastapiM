"""
基础模型类
提供通用的数据库操作方法
"""
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import declared_attr
from app.database import Base
from typing import Optional, List, Type, TypeVar, Generic
from datetime import datetime

ModelType = TypeVar("ModelType", bound="BaseModel")


class BaseModel(Base):
    """基础模型类"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @declared_attr
    def __tablename__(cls) -> str:
        """自动生成表名"""
        return cls.__name__.lower() + 's'
    
    @classmethod
    async def get(cls: Type[ModelType], db: AsyncSession, id: int) -> Optional[ModelType]:
        """根据ID获取记录"""
        result = await db.execute(select(cls).where(cls.id == id))
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_multi(
        cls: Type[ModelType], 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ModelType]:
        """获取多条记录"""
        result = await db.execute(select(cls).offset(skip).limit(limit))
        return result.scalars().all()
    
    @classmethod
    async def create(cls: Type[ModelType], db: AsyncSession, **kwargs) -> ModelType:
        """创建记录"""
        obj = cls(**kwargs)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
    
    async def update(self, db: AsyncSession, **kwargs) -> "BaseModel":
        """更新记录"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(self)
        return self
    
    async def delete(self, db: AsyncSession) -> bool:
        """删除记录"""
        await db.delete(self)
        await db.commit()
        return True
    
    @classmethod
    async def count(cls: Type[ModelType], db: AsyncSession) -> int:
        """统计记录数"""
        result = await db.execute(select(func.count(cls.id)))
        return result.scalar()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
