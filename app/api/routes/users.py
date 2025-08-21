"""
用户管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import (
    get_current_active_user,
    get_current_admin_user,
    get_pagination_params,
    PaginationParams,
    default_rate_limiter
)
from app.models.user import User
from app.schemas.user import (
    User as UserSchema,
    UserCreate,
    UserUpdate,
    UserProfile
)
from app.schemas.common import ResponseModel, PaginatedResponse, SuccessResponse

router = APIRouter()


@router.get("/", response_model=ResponseModel[PaginatedResponse[UserProfile]])
async def get_users(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: UserSchema = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表（管理员权限）"""
    users = await User.get_multi(db, skip=pagination.offset, limit=pagination.limit)
    total = await User.count(db)
    
    user_profiles = [UserProfile.from_orm(user) for user in users]
    paginated_data = PaginatedResponse.create(
        items=user_profiles,
        total=total,
        page=pagination.page,
        size=pagination.size
    )
    
    return ResponseModel(
        message="获取用户列表成功",
        data=paginated_data
    )


@router.get("/{user_id}", response_model=ResponseModel[UserProfile])
async def get_user(
    user_id: int,
    current_user: UserSchema = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定用户信息（管理员权限）"""
    user = await User.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return ResponseModel(
        message="获取用户信息成功",
        data=UserProfile.from_orm(user)
    )


@router.post("/", response_model=ResponseModel[UserSchema])
async def create_user(
    user_create: UserCreate,
    current_user: UserSchema = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(default_rate_limiter)
):
    """创建用户（管理员权限）"""
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
        message="用户创建成功",
        data=UserSchema.from_orm(user)
    )


@router.put("/{user_id}", response_model=ResponseModel[UserSchema])
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: UserSchema = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户信息（管理员权限）"""
    user = await User.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查邮箱是否被其他用户使用
    if user_update.email:
        existing_email = await User.get_by_email(db, user_update.email)
        if existing_email and existing_email.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
    
    # 更新用户信息
    update_data = user_update.dict(exclude_unset=True)
    if 'password' in update_data:
        user.set_password(update_data.pop('password'))
    
    updated_user = await user.update(db, **update_data)
    
    return ResponseModel(
        message="用户信息更新成功",
        data=UserSchema.from_orm(updated_user)
    )


@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: int,
    current_user: UserSchema = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除用户（管理员权限）"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户"
        )
    
    user = await User.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    await user.delete(db)
    
    return SuccessResponse(message="用户删除成功")


@router.put("/profile", response_model=ResponseModel[UserProfile])
async def update_profile(
    profile_update: UserUpdate,
    current_user: UserSchema = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新个人资料"""
    user = await User.get_by_username(db, current_user.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查邮箱是否被其他用户使用
    if profile_update.email:
        existing_email = await User.get_by_email(db, profile_update.email)
        if existing_email and existing_email.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
    
    # 更新个人资料（排除敏感字段）
    update_data = profile_update.dict(exclude_unset=True, exclude={'password', 'is_active'})
    updated_user = await user.update(db, **update_data)
    
    return ResponseModel(
        message="个人资料更新成功",
        data=UserProfile.from_orm(updated_user)
    )


@router.get("/search/", response_model=ResponseModel[List[UserProfile]])
async def search_users(
    q: str = Query(..., min_length=2, description="搜索关键词"),
    current_user: UserSchema = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """搜索用户（管理员权限）"""
    from sqlalchemy import or_
    from sqlalchemy.future import select
    
    # 构建搜索查询
    query = select(User).where(
        or_(
            User.username.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
            User.full_name.ilike(f"%{q}%")
        )
    ).limit(20)  # 限制搜索结果数量
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    user_profiles = [UserProfile.from_orm(user) for user in users]
    
    return ResponseModel(
        message=f"搜索到 {len(user_profiles)} 个用户",
        data=user_profiles
    )
