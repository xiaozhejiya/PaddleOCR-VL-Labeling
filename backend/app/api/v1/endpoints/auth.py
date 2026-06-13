from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    clear_auth_cookie,
    create_access_token,
    get_current_user,
    set_auth_cookie,
    verify_password,
)
from app.db.models import User
from app.db.session import get_db_session
from app.schemas.auth import AuthenticatedUser, LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, summary="用户登录")
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db_session),
) -> LoginResponse:
    user = db.scalar(
        select(User).where(
            User.username == payload.username,
            User.status == "active",
            User.deleted_at.is_(None),
        )
    )
    # 登录失败统一返回泛化错误，避免通过响应差异暴露用户名是否存在、
    # 密码是否正确、账号是否停用或是否已软删除。
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    settings = get_settings()
    access_token = create_access_token(user_id=user.id)
    set_auth_cookie(response, access_token)
    return LoginResponse(
        expires_in=settings.jwt_expire_minutes * 60,
        user=AuthenticatedUser(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            is_system_admin=user.is_system_admin,
        ),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
    summary="用户登出",
)
def logout(response: Response) -> Response:
    clear_auth_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=AuthenticatedUser, summary="获取当前用户")
def read_current_user(current_user: User = Depends(get_current_user)) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=current_user.id,
        username=current_user.username,
        display_name=current_user.display_name,
        is_system_admin=current_user.is_system_admin,
    )
