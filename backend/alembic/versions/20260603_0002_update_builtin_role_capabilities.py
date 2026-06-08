"""更新内置角色能力码

Revision ID: 20260603_0002
Revises: 20260603_0001
Create Date: 2026-06-03
"""

from typing import Sequence

from alembic import op

revision: str = "20260603_0002"
down_revision: str | None = "20260603_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# M2 初始种子只影响新建数据库；已有环境必须通过数据迁移把角色能力码更新为
# 文档约定的 can_* 形式，否则项目权限判定会找不到对应能力。
ROLE_CAPABILITIES: dict[str, list[str]] = {
    "system_admin": [
        "can_manage_system_users",
        "can_view_audit_log",
    ],
    "viewer": [
        "can_view_project",
    ],
    "annotator": [
        "can_view_project",
        "can_create_annotation_revision",
        "can_submit_revision",
    ],
    "reviewer": [
        "can_view_project",
        "can_review_revision",
    ],
    "data_manager": [
        "can_view_project",
        "can_upload_assets",
        "can_import_pages",
    ],
    "exporter": [
        "can_view_project",
        "can_create_export_job",
        "can_download_export",
    ],
    "project_admin": [
        "can_view_project",
        "can_upload_assets",
        "can_import_pages",
        "can_create_annotation_revision",
        "can_submit_revision",
        "can_review_revision",
        "can_manage_labels",
        "can_manage_relations",
        "can_manage_project_members",
        "can_create_export_job",
        "can_download_export",
        "can_lock_revision",
        "can_unlock_revision",
        "can_rollback_revision",
        "can_view_audit_log",
    ],
}

# downgrade 恢复旧短码，保证本地库和测试库的数据迁移可以按 Alembic 约定回滚。
LEGACY_ROLE_CAPABILITIES: dict[str, list[str]] = {
    "system_admin": ["system.admin"],
    "viewer": ["project.read", "document.read", "page.read", "annotation.read"],
    "annotator": ["project.read", "annotation.read", "annotation.write"],
    "reviewer": [
        "project.read",
        "annotation.read",
        "annotation.review",
        "annotation.lock",
    ],
    "data_manager": ["project.read", "asset.write", "document.write", "page.write"],
    "exporter": ["project.read", "export.create", "export.download"],
    "project_admin": ["project.admin", "member.manage", "role.bind"],
}


def upgrade() -> None:
    update_role_capabilities(ROLE_CAPABILITIES)


def downgrade() -> None:
    update_role_capabilities(LEGACY_ROLE_CAPABILITIES)


def update_role_capabilities(role_capabilities: dict[str, list[str]]) -> None:
    """原地重写内置角色的能力数组。"""

    for role_code, capabilities in role_capabilities.items():
        quoted_capabilities = ", ".join(_quote_literal(item) for item in capabilities)
        op.execute(
            f"""
            UPDATE role_registry
            SET
                permissions_json = jsonb_build_object(
                    'capabilities',
                    jsonb_build_array({quoted_capabilities})
                ),
                updated_at = now()
            WHERE code = {_quote_literal(role_code)}
            """
        )


def _quote_literal(value: str) -> str:
    # 当前值都是硬编码迁移字面量；仍然做 SQL 字面量转义，避免未来能力码包含
    # 单引号时拼出的迁移 SQL 失效。
    return "'" + value.replace("'", "''") + "'"
