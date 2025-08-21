"""
认证相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.database import get_db
from app.dependencies import (
    create_access_token,
    get_current_user,
    get_current_active_user,
    default_rate_limiter
)
from app.models.user import User
from app.schemas.user import Token, UserLogin, UserCreate, User as UserSchema, PasswordChange
from app.schemas.common import ResponseModel, SuccessResponse
from app.config import settings

router = APIRouter()


@router.post("/login", response_model=ResponseModel[Token])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(default_rate_limiter)
):
    """用户登录"""
    user = await User.authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    token_data = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )
    
    return ResponseModel(
        message="登录成功",
        data=token_data
    )


@router.post("/register", response_model=ResponseModel[UserSchema])
async def register(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(default_rate_limiter)
):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = await User.get_by_username(db, user_create.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = await User.get_by_email(db, user_create.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建用户
    user = await User.create_user(
        db=db,
        username=user_create.username,
        email=user_create.email,
        password=user_create.password,
        full_name=user_create.full_name
    )
    
    return ResponseModel(
        message="注册成功",
        data=UserSchema.from_orm(user)
    )


@router.get("/me", response_model=ResponseModel[UserSchema])
async def get_current_user_info(
    current_user: UserSchema = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return ResponseModel(
        message="获取用户信息成功",
        data=current_user
    )


@router.put("/change-password", response_model=SuccessResponse)
async def change_password(
    password_change: PasswordChange,
    current_user: UserSchema = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    # 获取完整的用户信息
    user = await User.get_by_username(db, current_user.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证当前密码
    if not user.check_password(password_change.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 更新密码
    user.set_password(password_change.new_password)
    await db.commit()
    
    return SuccessResponse(message="密码修改成功")


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    current_user: UserSchema = Depends(get_current_active_user)
):
    """用户登出"""
    # 在实际应用中，这里可以将token加入黑名单
    # 或者在Redis中标记token为无效
    return SuccessResponse(message="登出成功")


@router.post("/refresh", response_model=ResponseModel[Token])
async def refresh_token(
    current_user: UserSchema = Depends(get_current_user)
):
    """刷新访问令牌"""
    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    
    token_data = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )
    
    return ResponseModel(
        message="令牌刷新成功",
        data=token_data
    )
