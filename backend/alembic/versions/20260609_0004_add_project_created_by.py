"""add created_by to projects

Revision ID: 20260609_0004
Revises: 20260608_0003
Create Date: 2026-06-09
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260609_0004"
down_revision: str | None = "20260608_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 先添加可空字段
    op.add_column(
        "projects",
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建者用户 ID。"),
    )
    # 设置已有项目的 created_by 为管理员用户（假设 id=1）
    op.execute("UPDATE projects SET created_by = 1 WHERE created_by IS NULL")
    # 添加外键约束
    op.create_foreign_key("fk_projects_created_by", "projects", "users", ["created_by"], ["id"])
    # 设置为非空
    op.alter_column("projects", "created_by", nullable=False)


def downgrade() -> None:
    op.drop_constraint("fk_projects_created_by", "projects", type_="foreignkey")
    op.drop_column("projects", "created_by")
