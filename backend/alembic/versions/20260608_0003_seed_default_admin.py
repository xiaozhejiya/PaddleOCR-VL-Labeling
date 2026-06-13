"""seed default admin user

Revision ID: 20260608_0003
Revises: 20260603_0002
Create Date: 2026-06-08
"""

import logging
import os
from pathlib import Path
from typing import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "20260608_0003"
down_revision: str | None = "20260603_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

logger = logging.getLogger(__name__)


def _load_env_file() -> None:
    """从 backend/.env 加载环境变量（如果尚未设置）。"""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip()


def upgrade() -> None:
    import base64
    import hashlib
    import secrets

    _load_env_file()

    username = os.getenv("SEED_ADMIN_USERNAME", "admin")
    password = os.getenv("SEED_ADMIN_PASSWORD")
    if not password:
        logger.warning(
            "Skipping default admin seed because SEED_ADMIN_PASSWORD is not set."
        )
        return

    salt = secrets.token_urlsafe(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 210_000)
    password_hash = (
        f"pbkdf2_sha256$210000${salt}$"
        f"{base64.urlsafe_b64encode(digest).decode('ascii').rstrip('=')}"
    )

    op.get_bind().execute(
        text("""
        INSERT INTO users (username, display_name, password_hash, status, is_system_admin)
        VALUES (:username, '管理员', :password_hash, 'active', true)
        ON CONFLICT (username) DO NOTHING
        """),
        {"username": username, "password_hash": password_hash},
    )


def downgrade() -> None:
    username = os.getenv("SEED_ADMIN_USERNAME", "admin")
    op.get_bind().execute(
        text("DELETE FROM users WHERE username = :username AND is_system_admin = true"),
        {"username": username},
    )
