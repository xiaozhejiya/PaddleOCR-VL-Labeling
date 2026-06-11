from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(..., title="用户名", description="登录用户名。")
    password: str = Field(..., title="密码", description="登录密码。")


class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., title="用户内部编号", description="用户数据库内部主键。")
    username: str = Field(..., title="用户名", description="登录用户名。")
    display_name: str = Field(..., title="显示名称", description="用户显示名称。")
    is_system_admin: bool = Field(default=False, title="系统管理员", description="是否为系统管理员。")


class LoginResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expires_in: int = Field(..., title="过期秒数", description="访问令牌有效期。")
    user: AuthenticatedUser = Field(..., title="当前用户")
