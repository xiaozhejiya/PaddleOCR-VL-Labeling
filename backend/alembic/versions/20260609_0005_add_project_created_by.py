"""add created_by to projects

Revision ID: 20260609_0005
Revises: 20260608_0004
Create Date: 2026-06-09
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = "20260609_0005"
down_revision: str | None = "20260608_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip()


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建者用户 ID。"),
    )

    bind = op.get_bind()
    existing_project_count = bind.execute(
        text("SELECT COUNT(*) FROM projects WHERE created_by IS NULL")
    ).scalar_one()

    if existing_project_count:
        _load_env_file()
        admin_username = os.getenv("SEED_ADMIN_USERNAME", "admin")
        admin_id = bind.execute(
            text(
                "SELECT id FROM users WHERE username = :admin_username LIMIT 1"
            ),
            {"admin_username": admin_username},
        ).scalar()

        if admin_id is None:
            raise RuntimeError(
                "Migration 20260609_0005 requires an existing admin user to backfill "
                "projects.created_by. Set SEED_ADMIN_PASSWORD and run the admin seed "
                "migration, or create the admin user manually before upgrading."
            )

        bind.execute(
            text(
                "UPDATE projects SET created_by = :admin_id WHERE created_by IS NULL"
            ),
            {"admin_id": admin_id},
        )

    op.create_foreign_key("fk_projects_created_by", "projects", "users", ["created_by"], ["id"])
    op.alter_column("projects", "created_by", nullable=False)


def downgrade() -> None:
    op.drop_constraint("fk_projects_created_by", "projects", type_="foreignkey")
    op.drop_column("projects", "created_by")
