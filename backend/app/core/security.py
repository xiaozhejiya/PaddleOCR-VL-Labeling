"""认证、密码哈希和项目能力判定工具。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings, is_missing_or_placeholder
from app.db.models import MemberRoleBinding, ProjectMember, RoleRegistry, User
from app.db.models.project import Project
from app.db.session import get_db_session

JWT_ALGORITHM = "HS256"
PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 210_000

# 关闭 FastAPI 默认的 403 映射，让缺失或非法 Bearer 凭证统一落到
# API 明确约定的 401 认证失败边界。
bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(*, user_id: int) -> str:
    """为已通过认证的有效用户生成签名访问令牌。"""

    settings = get_settings()
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user_id),
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    return _encode_jwt(payload)


def decode_access_token(token: str) -> dict[str, Any]:
    """校验 JWT 完整性和过期时间后，再返回可信声明。"""

    header, payload, signature = _split_token(token)
    signing_input = f"{header}.{payload}".encode("ascii")
    expected_signature = _sign(signing_input)
    # HMAC 签名匹配前，header 和 payload 都不可信；token 内的 alg 字段不能
    # 反向控制校验算法，当前只接受服务端固定的 HS256。
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        )

    header_data = _json_b64decode(header)
    if header_data.get("alg") != JWT_ALGORITHM or header_data.get("typ") != "JWT":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        )

    payload_data = _json_b64decode(payload)
    expires_at = payload_data.get("exp")
    if not isinstance(expires_at, int) or expires_at <= int(datetime.now(UTC).timestamp()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired.",
        )
    return payload_data


def hash_password(password: str) -> str:
    """把明文密码哈希为带算法、迭代次数和盐值的 PBKDF2 存储串。"""

    salt = secrets.token_urlsafe(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_HASH_ITERATIONS,
    )
    return (
        f"{PASSWORD_HASH_ALGORITHM}${PASSWORD_HASH_ITERATIONS}${salt}$"
        f"{base64.urlsafe_b64encode(digest).decode('ascii').rstrip('=')}"
    )


def verify_password(password: str, password_hash: str | None) -> bool:
    """校验明文密码，并用常量时间比较降低时序侧信道风险。"""

    if not password_hash:
        return False
    try:
        algorithm, iterations_raw, salt, expected_raw = password_hash.split("$", 3)
        iterations = int(iterations_raw)
    except ValueError:
        return False
    if algorithm != PASSWORD_HASH_ALGORITHM:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    actual = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return hmac.compare_digest(actual, expected_raw)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db_session),
) -> User:
    """把 Cookie 会话或 Bearer token 解析为有效且未软删除的当前用户。"""

    token = request.cookies.get(get_settings().auth_cookie_name)
    if token is None and credentials is not None and credentials.scheme.lower() == "bearer":
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token.",
        )
    payload = decode_access_token(token)
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdigit():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        )

    user = db.scalar(
        select(User).where(
            User.id == int(subject),
            User.status == "active",
            User.deleted_at.is_(None),
        )
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not active.",
        )
    return user


def set_auth_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.auth_cookie_name,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/",
    )


def require_project_capability(capability: str) -> Callable[..., User]:
    """为 project_id 来自路径参数的接口构造项目能力依赖。"""

    def dependency(
        project_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db_session),
    ) -> User:
        capabilities = get_project_capabilities(
            db,
            user_id=current_user.id,
            project_id=project_id,
        )
        if capability not in capabilities:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied.",
            )
        return current_user

    return dependency


def ensure_project_capability(
    db: Session,
    *,
    user_id: int,
    project_id: int,
    capability: str,
) -> None:
    """为 project_id 不在路径参数中的接口显式校验项目能力。"""

    # 项目创建者自动拥有所有项目能力
    project = db.get(Project, project_id)
    if project and project.created_by == user_id:
        return

    capabilities = get_project_capabilities(
        db,
        user_id=user_id,
        project_id=project_id,
    )
    if capability not in capabilities:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied.",
        )


def get_project_capabilities(db: Session, *, user_id: int, project_id: int) -> set[str]:
    """从有效项目成员和角色绑定中合并项目级能力集合。"""

    # 项目操作只从项目成员关系和有效的项目级角色推导权限，不把系统级角色隐式
    # 合并进来；否则项目访问决策会变得难以审计，也容易误授权。
    stmt = (
        select(RoleRegistry.permissions_json)
        .join(MemberRoleBinding, MemberRoleBinding.role_id == RoleRegistry.id)
        .join(ProjectMember, ProjectMember.id == MemberRoleBinding.project_member_id)
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.member_status == "active",
            MemberRoleBinding.status == "active",
            RoleRegistry.scope == "project",
            RoleRegistry.is_active.is_(True),
        )
    )
    capabilities: set[str] = set()
    for permissions_json in db.scalars(stmt):
        capability_items = permissions_json.get("capabilities", [])
        if isinstance(capability_items, list):
            # permissions_json 来自 JSONB 数据，只接受字符串能力码，避免异常种子
            # 数据把非字符串值误解释为可用权限。
            capabilities.update(item for item in capability_items if isinstance(item, str))
    return capabilities


def get_jwt_secret_key() -> str:
    """读取 JWT 签名密钥；缺失或仍是占位值时直接失败关闭。"""

    settings = get_settings()
    if is_missing_or_placeholder(settings.jwt_secret_key):
        raise RuntimeError("JWT_SECRET_KEY is not configured.")
    return settings.jwt_secret_key.strip()


def _encode_jwt(payload: dict[str, Any]) -> str:
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    header_raw = _json_b64encode(header)
    payload_raw = _json_b64encode(payload)
    signing_input = f"{header_raw}.{payload_raw}".encode("ascii")
    signature = _sign(signing_input)
    return f"{header_raw}.{payload_raw}.{signature}"


def _sign(signing_input: bytes) -> str:
    digest = hmac.new(
        get_jwt_secret_key().encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    return _bytes_b64encode(digest)


def _split_token(token: str) -> tuple[str, str, str]:
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        )
    return parts[0], parts[1], parts[2]


def _json_b64encode(value: dict[str, Any]) -> str:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _bytes_b64encode(raw)


def _json_b64decode(value: str) -> dict[str, Any]:
    try:
        raw = base64.urlsafe_b64decode(_restore_padding(value))
        decoded = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        ) from exc
    if not isinstance(decoded, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        )
    return decoded


def _bytes_b64encode(value: bytes) -> str:
    # JWT 紧凑序列化要求使用不带补位符的 base64url。
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _restore_padding(value: str) -> bytes:
    # Python 解码器需要补位符，因此只在解码边界恢复 padding。
    return (value + "=" * (-len(value) % 4)).encode("ascii")
