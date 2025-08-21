"""
用户相关Pydantic模型
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be no more than 50 characters long')
        if not v.isalnum() and '_' not in v:
            raise ValueError('Username can only contain letters, numbers and underscores')
        return v


class UserCreate(UserBase):
    """创建用户模型"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 100:
            raise ValueError('Password must be no more than 100 characters long')
        return v


class UserUpdate(BaseModel):
    """更新用户模型"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
            if len(v) > 100:
                raise ValueError('Password must be no more than 100 characters long')
        return v


class User(UserBase):
    """用户响应模型"""
    id: int
    is_superuser: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserInDB(User):
    """数据库中的用户模型"""
    hashed_password: str


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str


class Token(BaseModel):
    """令牌模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """令牌数据模型"""
    username: Optional[str] = None


class PasswordChange(BaseModel):
    """密码修改模型"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        if len(v) > 100:
            raise ValueError('New password must be no more than 100 characters long')
        return v


class UserProfile(BaseModel):
    """用户档案模型"""
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
