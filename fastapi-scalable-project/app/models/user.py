"""
用户模型
"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from typing import Optional
from datetime import datetime

from .base import BaseModel

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseModel):
    """用户模型"""
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @classmethod
    def get_password_hash(cls, password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)
    
    def check_password(self, plain_password: str) -> bool:
        """检查密码"""
        return self.verify_password(plain_password, self.hashed_password)
    
    def set_password(self, plain_password: str):
        """设置密码"""
        self.hashed_password = self.get_password_hash(plain_password)
    
    @classmethod
    async def get_by_username(cls, db: AsyncSession, username: str) -> Optional["User"]:
        """根据用户名获取用户"""
        result = await db.execute(select(cls).where(cls.username == username))
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: str) -> Optional["User"]:
        """根据邮箱获取用户"""
        result = await db.execute(select(cls).where(cls.email == email))
        return result.scalar_one_or_none()
    
    @classmethod
    async def create_user(
        cls,
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        is_superuser: bool = False
    ) -> "User":
        """创建用户"""
        hashed_password = cls.get_password_hash(password)
        user = cls(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_superuser=is_superuser
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @classmethod
    async def authenticate(
        cls, 
        db: AsyncSession, 
        username: str, 
        password: str
    ) -> Optional["User"]:
        """用户认证"""
        user = await cls.get_by_username(db, username)
        if not user:
            return None
        if not user.check_password(password):
            return None
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        
        return user
    
    async def update_last_login(self, db: AsyncSession):
        """更新最后登录时间"""
        self.last_login = datetime.utcnow()
        await db.commit()
        await db.refresh(self)
    
    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.is_superuser
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
