"""create core tables

Revision ID: 20260603_0001
Revises:
Create Date: 2026-06-03
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260603_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UPDATED_AT_TABLES = (
    "projects",
    "users",
    "role_registry",
    "project_members",
    "member_role_bindings",
    "assets",
    "documents",
    "pages",
    "label_registry",
    "annotation_revisions",
    "annotation_objects",
    "relation_objects",
    "background_jobs",
    "qc_results",
    "export_jobs",
)

DROP_TABLE_ORDER = (
    "relation_objects",
    "qc_results",
    "annotation_objects",
    "annotation_revisions",
    "pages",
    "export_jobs",
    "documents",
    "member_role_bindings",
    "audit_logs",
    "background_jobs",
    "label_registry",
    "assets",
    "project_members",
    "role_registry",
    "users",
    "projects",
)


def id_column(comment: str = "内部主键。") -> sa.Column:
    return sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False, comment=comment)


def timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="创建时间。",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="更新时间，由数据库 trigger 自动刷新。",
        ),
    ]


def upgrade() -> None:
    create_tables()
    create_updated_at_triggers()
    create_audit_log_guard()
    seed_builtin_roles()


def downgrade() -> None:
    drop_audit_log_guard()
    drop_updated_at_triggers()
    for table_name in DROP_TABLE_ORDER:
        op.drop_table(table_name)
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_logs_mutation()")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")


def create_tables() -> None:
    op.create_table(
        "projects",
        id_column("内部主键：BIGINT identity，仅用于数据库关联。"),
        sa.Column("name", sa.Text(), nullable=False, comment="项目名称。"),
        sa.Column("description", sa.Text(), comment="项目说明。"),
        sa.Column(
            "schema_version",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'v1'"),
            comment="项目 schema 版本。",
        ),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_projects"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_projects_name_not_blank"),
        sa.CheckConstraint(
            "btrim(schema_version) <> ''",
            name="ck_projects_schema_version_not_blank",
        ),
        comment="项目表：保存标注项目的基础信息和 schema 版本。",
    )

    op.create_table(
        "users",
        id_column(),
        sa.Column("username", sa.Text(), nullable=False, comment="登录用户名。"),
        sa.Column("email", sa.Text(), comment="邮箱。"),
        sa.Column("display_name", sa.Text(), nullable=False, comment="显示名称。"),
        sa.Column("password_hash", sa.Text(), comment="密码哈希，不保存明文。"),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'pending'"),
            comment="用户状态。",
        ),
        sa.Column(
            "is_system_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="系统管理员标记，不替代项目角色。",
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), comment="最近登录时间。"),
        *timestamp_columns(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), comment="软删除时间。"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.CheckConstraint("btrim(username) <> ''", name="ck_users_username_not_blank"),
        sa.CheckConstraint(
            "btrim(display_name) <> ''",
            name="ck_users_display_name_not_blank",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'disabled', 'pending')",
            name="ck_users_status",
        ),
        comment="用户表：保存平台账号，是审计、创建人、复核人和权限校验的基础事实来源。",
    )
    op.create_index(
        "uq_users_email",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )

    op.create_table(
        "role_registry",
        id_column(),
        sa.Column("code", sa.Text(), nullable=False, comment="角色编码。"),
        sa.Column("display_name", sa.Text(), nullable=False, comment="角色显示名称。"),
        sa.Column("scope", sa.Text(), nullable=False, comment="角色作用域：system / project。"),
        sa.Column("description", sa.Text(), comment="角色说明。"),
        sa.Column(
            "permissions_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="权限 JSON。",
        ),
        sa.Column(
            "is_builtin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="是否内置角色。",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="是否启用。",
        ),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_role_registry"),
        sa.UniqueConstraint("code", name="uq_role_registry_code"),
        sa.UniqueConstraint("id", "scope", name="uq_role_registry_id_scope"),
        sa.CheckConstraint("scope IN ('system', 'project')", name="ck_role_registry_scope"),
        sa.CheckConstraint("btrim(code) <> ''", name="ck_role_registry_code_not_blank"),
        sa.CheckConstraint(
            "btrim(display_name) <> ''",
            name="ck_role_registry_display_name_not_blank",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(permissions_json) = 'object'",
            name="ck_role_registry_permissions_json_object",
        ),
        comment="角色注册表：保存系统内置角色和权限 JSON，是 capability 计算来源之一。",
    )

    op.create_table(
        "project_members",
        id_column(),
        sa.Column("project_id", sa.BigInteger(), nullable=False, comment="项目内部主键。"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="用户内部主键。"),
        sa.Column(
            "member_status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'active'"),
            comment="成员状态。",
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="加入时间。",
        ),
        sa.Column("created_by", sa.BigInteger(), comment="创建人。"),
        *timestamp_columns(),
        sa.Column("removed_at", sa.DateTime(timezone=True), comment="移除时间。"),
        sa.PrimaryKeyConstraint("id", name="pk_project_members"),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_members_project_user"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_project_members_project_id_projects",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_project_members_user_id_users",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_project_members_created_by_users",
        ),
        sa.CheckConstraint(
            "member_status IN ('active', 'disabled', 'invited', 'removed')",
            name="ck_project_members_status",
        ),
        comment="项目成员表：保存用户和项目的成员关系。",
    )
    op.create_index("ix_project_members_project_id", "project_members", ["project_id"])
    op.create_index("ix_project_members_user_id", "project_members", ["user_id"])

    op.create_table(
        "member_role_bindings",
        id_column(),
        sa.Column("project_member_id", sa.BigInteger(), nullable=False, comment="项目成员内部主键。"),
        sa.Column("role_id", sa.BigInteger(), nullable=False, comment="角色内部主键。"),
        sa.Column(
            "role_scope",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'project'"),
            comment="固定为 project，用于禁止绑定系统级角色。",
        ),
        sa.Column("granted_by", sa.BigInteger(), comment="授权人。"),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="授权时间。",
        ),
        sa.Column("revoked_by", sa.BigInteger(), comment="撤销人。"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), comment="撤销时间。"),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'active'"),
            comment="绑定状态。",
        ),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_member_role_bindings"),
        sa.ForeignKeyConstraint(
            ["project_member_id"],
            ["project_members.id"],
            name="fk_member_role_bindings_project_member_id_project_members",
        ),
        sa.ForeignKeyConstraint(
            ["role_id", "role_scope"],
            ["role_registry.id", "role_registry.scope"],
            name="fk_member_role_bindings_role_registry_project",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by"],
            ["users.id"],
            name="fk_member_role_bindings_granted_by_users",
        ),
        sa.ForeignKeyConstraint(
            ["revoked_by"],
            ["users.id"],
            name="fk_member_role_bindings_revoked_by_users",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'revoked')",
            name="ck_member_role_bindings_status",
        ),
        sa.CheckConstraint(
            "role_scope = 'project'",
            name="ck_member_role_bindings_role_scope_project",
        ),
        comment="成员角色绑定表：保存项目成员与项目级角色的授权和撤销记录。",
    )
    op.create_index(
        "uq_member_role_bindings_active_member_role",
        "member_role_bindings",
        ["project_member_id", "role_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index("ix_member_role_bindings_role_id", "member_role_bindings", ["role_id"])

    op.create_table(
        "assets",
        id_column(),
        sa.Column("public_id", sa.Text(), nullable=False, comment="公开资产编号。"),
        sa.Column("asset_type", sa.Text(), nullable=False, comment="资产类型。"),
        sa.Column("storage_path", sa.Text(), nullable=False, comment="受控存储相对路径。"),
        sa.Column("original_filename", sa.Text(), comment="原始文件名。"),
        sa.Column("mime_type", sa.Text(), comment="MIME 类型。"),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, comment="文件大小。"),
        sa.Column("sha256", sa.CHAR(64), nullable=False, comment="文件 SHA-256。"),
        sa.Column("width", sa.Integer(), comment="图像宽度。"),
        sa.Column("height", sa.Integer(), comment="图像高度。"),
        sa.Column("created_by", sa.BigInteger(), comment="创建人。"),
        sa.Column(
            "readonly",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="只读标记。",
        ),
        *timestamp_columns(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), comment="软删除时间。"),
        sa.PrimaryKeyConstraint("id", name="pk_assets"),
        sa.UniqueConstraint("public_id", name="uq_assets_public_id"),
        sa.UniqueConstraint("sha256", name="uq_assets_sha256"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_assets_created_by_users"),
        sa.CheckConstraint("size_bytes >= 0", name="ck_assets_size_bytes"),
        sa.CheckConstraint("width IS NULL OR width > 0", name="ck_assets_width"),
        sa.CheckConstraint("height IS NULL OR height > 0", name="ck_assets_height"),
        sa.CheckConstraint("btrim(public_id) <> ''", name="ck_assets_public_id_not_blank"),
        sa.CheckConstraint("btrim(asset_type) <> ''", name="ck_assets_asset_type_not_blank"),
        sa.CheckConstraint(
            "btrim(storage_path) <> ''",
            name="ck_assets_storage_path_not_blank",
        ),
        comment="文件资产表：保存原始文件、页面图像、标注 JSON、导出文件等文件级元数据。",
    )
    op.create_index("ix_assets_asset_type", "assets", ["asset_type"])

    op.create_table(
        "documents",
        id_column(),
        sa.Column("public_id", sa.Text(), nullable=False, comment="公开文档编号。"),
        sa.Column("project_id", sa.BigInteger(), nullable=False, comment="项目内部主键。"),
        sa.Column("document_code", sa.Text(), comment="项目内业务编号。"),
        sa.Column("document_type", sa.Text(), nullable=False, comment="文档类型。"),
        sa.Column("source_type", sa.Text(), comment="来源类型。"),
        sa.Column("authorization_id", sa.BigInteger(), comment="授权文件资产。"),
        sa.Column(
            "domain_metadata_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="场景扩展元数据。",
        ),
        sa.Column(
            "split",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'train'"),
            comment="数据集划分。",
        ),
        sa.Column(
            "lock_status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'unlocked'"),
            comment="锁定状态。",
        ),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_documents"),
        sa.UniqueConstraint("public_id", name="uq_documents_public_id"),
        sa.UniqueConstraint("id", "project_id", name="uq_documents_id_project"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_documents_project_id_projects"),
        sa.ForeignKeyConstraint(
            ["authorization_id"],
            ["assets.id"],
            name="fk_documents_authorization_id_assets",
        ),
        sa.CheckConstraint(
            "split IN ('train', 'val', 'eval', 'external_auxiliary')",
            name="ck_documents_split",
        ),
        sa.CheckConstraint(
            "lock_status IN ('unlocked', 'locked')",
            name="ck_documents_lock_status",
        ),
        sa.CheckConstraint("btrim(public_id) <> ''", name="ck_documents_public_id_not_blank"),
        sa.CheckConstraint(
            "btrim(document_type) <> ''",
            name="ck_documents_document_type_not_blank",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(domain_metadata_json) = 'object'",
            name="ck_documents_domain_metadata_json_object",
        ),
        comment="文档表：保存原始试卷、PDF 或其他文档级元数据。",
    )
    op.create_index(
        "uq_documents_project_document_code",
        "documents",
        ["project_id", "document_code"],
        unique=True,
        postgresql_where=sa.text("document_code IS NOT NULL"),
    )
    op.create_index("ix_documents_project_id", "documents", ["project_id"])
    op.create_index("ix_documents_split", "documents", ["split"])

    op.create_table(
        "pages",
        id_column("页面内部主键：仅用于数据库关联。"),
        sa.Column("document_id", sa.BigInteger(), nullable=False, comment="文档内部主键。"),
        sa.Column("public_id", sa.Text(), nullable=False, comment="公开稳定页面编号。"),
        sa.Column("page_index", sa.Integer(), nullable=False, comment="文档内页序号。"),
        sa.Column("image_asset_id", sa.BigInteger(), comment="页面图像资产。"),
        sa.Column("width", sa.Integer(), nullable=False, comment="页面宽度。"),
        sa.Column("height", sa.Integer(), nullable=False, comment="页面高度。"),
        sa.Column("capture_method", sa.Text(), comment="采集方式。"),
        sa.Column("visual_difficulty", sa.Text(), comment="视觉难度。"),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'imported'"),
            comment="页面状态。",
        ),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_pages"),
        sa.UniqueConstraint("public_id", name="uq_pages_public_id"),
        sa.UniqueConstraint("id", "document_id", name="uq_pages_id_document"),
        sa.UniqueConstraint("document_id", "page_index", name="uq_pages_document_page_index"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name="fk_pages_document_id_documents"),
        sa.ForeignKeyConstraint(["image_asset_id"], ["assets.id"], name="fk_pages_image_asset_id_assets"),
        sa.CheckConstraint("page_index >= 0", name="ck_pages_page_index"),
        sa.CheckConstraint("width > 0", name="ck_pages_width"),
        sa.CheckConstraint("height > 0", name="ck_pages_height"),
        sa.CheckConstraint(
            "status IN ('imported', 'preannotated', 'annotated', 'reviewed', 'locked')",
            name="ck_pages_status",
        ),
        sa.CheckConstraint("btrim(public_id) <> ''", name="ck_pages_public_id_not_blank"),
        comment="页面表：保存文档页和页面图像的关系。",
    )
    op.create_index("ix_pages_document_id", "pages", ["document_id"])
    op.create_index("ix_pages_status", "pages", ["status"])
    op.create_index("ix_pages_visual_difficulty", "pages", ["visual_difficulty"])

    op.create_table(
        "label_registry",
        id_column(),
        sa.Column("project_id", sa.BigInteger(), comment="所属项目；为空表示全局内置标签。"),
        sa.Column("namespace", sa.Text(), nullable=False, comment="标签命名空间。"),
        sa.Column("name", sa.Text(), nullable=False, comment="标签名称。"),
        sa.Column("display_name", sa.Text(), nullable=False, comment="标签显示名称。"),
        sa.Column(
            "geometry_types_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
            comment="允许的几何类型列表。",
        ),
        sa.Column(
            "attributes_schema_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="标签属性 schema。",
        ),
        sa.Column(
            "exportable_to_pp_doclayout_v3",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="是否可导出为 PP-DocLayoutV3 标签。",
        ),
        sa.Column("default_color", sa.Text(), comment="默认显示颜色。"),
        sa.Column(
            "is_builtin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="是否内置标签。",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="是否启用。",
        ),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_label_registry"),
        sa.UniqueConstraint(
            "project_id",
            "namespace",
            "name",
            name="uq_label_registry_project_namespace_name",
            postgresql_nulls_not_distinct=True,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_label_registry_project_id_projects",
        ),
        sa.CheckConstraint("btrim(namespace) <> ''", name="ck_label_registry_namespace_not_blank"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_label_registry_name_not_blank"),
        sa.CheckConstraint(
            "btrim(display_name) <> ''",
            name="ck_label_registry_display_name_not_blank",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(geometry_types_json) = 'array'",
            name="ck_label_registry_geometry_types_json_array",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(attributes_schema_json) = 'object'",
            name="ck_label_registry_attributes_schema_json_object",
        ),
        comment="标签注册表：保存官方 layout 标签和场景扩展标签。",
    )
    op.create_index("ix_label_registry_project_id", "label_registry", ["project_id"])
    op.create_index(
        "ix_label_registry_namespace_name",
        "label_registry",
        ["namespace", "name"],
    )

    op.create_table(
        "annotation_revisions",
        id_column(),
        sa.Column("public_id", sa.Text(), nullable=False, comment="公开标注版本编号。"),
        sa.Column("project_id", sa.BigInteger(), nullable=False, comment="项目内部主键。"),
        sa.Column("document_id", sa.BigInteger(), nullable=False, comment="文档内部主键。"),
        sa.Column("page_id", sa.BigInteger(), nullable=False, comment="页面内部主键。"),
        sa.Column("revision_no", sa.Integer(), nullable=False, comment="同页递增版本号。"),
        sa.Column("parent_revision_id", sa.BigInteger(), comment="父版本内部主键。"),
        sa.Column("annotation_json_asset_id", sa.BigInteger(), nullable=False, comment="标注 JSON 资产。"),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'draft'"),
            comment="版本状态。",
        ),
        sa.Column(
            "qc_status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'pending'"),
            comment="质检状态。",
        ),
        sa.Column("created_by", sa.BigInteger(), comment="创建人。"),
        *timestamp_columns(),
        sa.Column("change_summary", sa.Text(), comment="变更摘要。"),
        sa.Column("change_reason", sa.Text(), comment="变更原因。"),
        sa.PrimaryKeyConstraint("id", name="pk_annotation_revisions"),
        sa.UniqueConstraint("public_id", name="uq_annotation_revisions_public_id"),
        sa.UniqueConstraint("page_id", "revision_no", name="uq_annotation_revisions_page_revision_no"),
        sa.UniqueConstraint("id", "page_id", name="uq_annotation_revisions_id_page"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_annotation_revisions_project_id_projects"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name="fk_annotation_revisions_document_id_documents"),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], name="fk_annotation_revisions_page_id_pages"),
        sa.ForeignKeyConstraint(
            ["document_id", "project_id"],
            ["documents.id", "documents.project_id"],
            name="fk_annotation_revisions_document_project",
        ),
        sa.ForeignKeyConstraint(
            ["page_id", "document_id"],
            ["pages.id", "pages.document_id"],
            name="fk_annotation_revisions_page_document",
        ),
        sa.ForeignKeyConstraint(
            ["parent_revision_id"],
            ["annotation_revisions.id"],
            name="fk_annotation_revisions_parent_revision_id_annotation_revisions",
        ),
        sa.ForeignKeyConstraint(
            ["parent_revision_id", "page_id"],
            ["annotation_revisions.id", "annotation_revisions.page_id"],
            name="fk_annotation_revisions_parent_same_page",
        ),
        sa.ForeignKeyConstraint(
            ["annotation_json_asset_id"],
            ["assets.id"],
            name="fk_annotation_revisions_annotation_json_asset_id_assets",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_annotation_revisions_created_by_users"),
        sa.CheckConstraint("revision_no > 0", name="ck_annotation_revisions_revision_no"),
        sa.CheckConstraint(
            "status IN ('draft', 'submitted', 'reviewed', 'locked', 'superseded')",
            name="ck_annotation_revisions_status",
        ),
        sa.CheckConstraint(
            "qc_status IN ('pending', 'passed', 'failed', 'warning')",
            name="ck_annotation_revisions_qc_status",
        ),
        sa.CheckConstraint("btrim(public_id) <> ''", name="ck_annotation_revisions_public_id_not_blank"),
        comment="标注版本表：保存每次页面标注提交形成的不可变版本记录。",
    )
    op.create_index("ix_annotation_revisions_project_id", "annotation_revisions", ["project_id"])
    op.create_index("ix_annotation_revisions_document_id", "annotation_revisions", ["document_id"])
    op.create_index("ix_annotation_revisions_page_id", "annotation_revisions", ["page_id"])
    op.create_index(
        "ix_annotation_revisions_page_status_revision_no",
        "annotation_revisions",
        ["page_id", "status", sa.text("revision_no DESC")],
    )

    op.create_table(
        "annotation_objects",
        id_column(),
        sa.Column("revision_id", sa.BigInteger(), nullable=False, comment="标注版本内部主键。"),
        sa.Column("ann_id", sa.Text(), nullable=False, comment="标注对象编号。"),
        sa.Column("label_namespace", sa.Text(), nullable=False, comment="标签命名空间。"),
        sa.Column("label_name", sa.Text(), nullable=False, comment="标签名称。"),
        sa.Column("bbox_xyxy", postgresql.JSONB(), comment="bbox 几何。"),
        sa.Column("quad", postgresql.JSONB(), comment="四点几何。"),
        sa.Column("polygon", postgresql.JSONB(), comment="多边形几何。"),
        sa.Column("read_order", sa.Integer(), comment="阅读顺序索引。"),
        sa.Column(
            "attributes_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="标注对象属性 JSON。",
        ),
        sa.Column(
            "source_refs_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="来源引用 JSON。",
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'active'"),
            comment="对象状态。",
        ),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_annotation_objects"),
        sa.UniqueConstraint("revision_id", "ann_id", name="uq_annotation_objects_revision_ann"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["annotation_revisions.id"],
            name="fk_annotation_objects_revision_id_annotation_revisions",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("read_order IS NULL OR read_order > 0", name="ck_annotation_objects_read_order"),
        sa.CheckConstraint("status IN ('active', 'deleted')", name="ck_annotation_objects_status"),
        sa.CheckConstraint("btrim(ann_id) <> ''", name="ck_annotation_objects_ann_id_not_blank"),
        sa.CheckConstraint("btrim(label_namespace) <> ''", name="ck_annotation_objects_label_namespace_not_blank"),
        sa.CheckConstraint("btrim(label_name) <> ''", name="ck_annotation_objects_label_name_not_blank"),
        sa.CheckConstraint(
            "bbox_xyxy IS NULL OR jsonb_typeof(bbox_xyxy) = 'array'",
            name="ck_annotation_objects_bbox_xyxy_json_array",
        ),
        sa.CheckConstraint(
            "quad IS NULL OR jsonb_typeof(quad) = 'array'",
            name="ck_annotation_objects_quad_json_array",
        ),
        sa.CheckConstraint(
            "polygon IS NULL OR jsonb_typeof(polygon) = 'array'",
            name="ck_annotation_objects_polygon_json_array",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(attributes_json) = 'object'",
            name="ck_annotation_objects_attributes_json_object",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(source_refs_json) = 'object'",
            name="ck_annotation_objects_source_refs_json_object",
        ),
        comment="标注对象索引表：从 annotation revision JSON 抽取，用于查询和导出前索引。",
    )
    op.create_index("ix_annotation_objects_revision_id", "annotation_objects", ["revision_id"])
    op.create_index("ix_annotation_objects_label", "annotation_objects", ["label_namespace", "label_name"])
    op.create_index("ix_annotation_objects_status", "annotation_objects", ["status"])
    op.create_index("ix_annotation_objects_read_order", "annotation_objects", ["read_order"])

    op.create_table(
        "relation_objects",
        id_column(),
        sa.Column("revision_id", sa.BigInteger(), nullable=False, comment="标注版本内部主键。"),
        sa.Column("rel_id", sa.Text(), nullable=False, comment="关系编号。"),
        sa.Column("relation_type", sa.Text(), nullable=False, comment="关系类型。"),
        sa.Column("from_ann_id", sa.Text(), nullable=False, comment="关系起点对象编号。"),
        sa.Column("to_ann_id", sa.Text(), nullable=False, comment="关系终点对象编号。"),
        sa.Column(
            "attributes_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="关系属性 JSON。",
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'active'"),
            comment="关系状态。",
        ),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_relation_objects"),
        sa.UniqueConstraint("revision_id", "rel_id", name="uq_relation_objects_revision_rel"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["annotation_revisions.id"],
            name="fk_relation_objects_revision_id_annotation_revisions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["revision_id", "from_ann_id"],
            ["annotation_objects.revision_id", "annotation_objects.ann_id"],
            name="fk_relation_objects_from_annotation_object",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.ForeignKeyConstraint(
            ["revision_id", "to_ann_id"],
            ["annotation_objects.revision_id", "annotation_objects.ann_id"],
            name="fk_relation_objects_to_annotation_object",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.CheckConstraint("status IN ('active', 'deleted')", name="ck_relation_objects_status"),
        sa.CheckConstraint("btrim(rel_id) <> ''", name="ck_relation_objects_rel_id_not_blank"),
        sa.CheckConstraint("btrim(relation_type) <> ''", name="ck_relation_objects_relation_type_not_blank"),
        sa.CheckConstraint("btrim(from_ann_id) <> ''", name="ck_relation_objects_from_ann_id_not_blank"),
        sa.CheckConstraint("btrim(to_ann_id) <> ''", name="ck_relation_objects_to_ann_id_not_blank"),
        sa.CheckConstraint("from_ann_id <> to_ann_id", name="ck_relation_objects_distinct_ann"),
        sa.CheckConstraint(
            "jsonb_typeof(attributes_json) = 'object'",
            name="ck_relation_objects_attributes_json_object",
        ),
        comment="关系对象索引表：从 annotation revision JSON 抽取的对象关系索引。",
    )
    op.create_index("ix_relation_objects_revision_id", "relation_objects", ["revision_id"])
    op.create_index("ix_relation_objects_relation_type", "relation_objects", ["relation_type"])

    op.create_table(
        "background_jobs",
        id_column(),
        sa.Column("public_id", sa.Text(), nullable=False, comment="公开任务编号。"),
        sa.Column("job_type", sa.Text(), nullable=False, comment="任务类型。"),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'queued'"),
            comment="任务状态。",
        ),
        sa.Column(
            "payload_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="任务载荷 JSON。",
        ),
        sa.Column(
            "result_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="任务结果 JSON。",
        ),
        sa.Column("progress", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0"), comment="任务进度。"),
        sa.Column("created_by", sa.BigInteger(), comment="创建人。"),
        *timestamp_columns(),
        sa.Column("started_at", sa.DateTime(timezone=True), comment="开始时间。"),
        sa.Column("finished_at", sa.DateTime(timezone=True), comment="结束时间。"),
        sa.Column("error_message", sa.Text(), comment="错误信息。"),
        sa.PrimaryKeyConstraint("id", name="pk_background_jobs"),
        sa.UniqueConstraint("public_id", name="uq_background_jobs_public_id"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_background_jobs_created_by_users"),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'canceled')",
            name="ck_background_jobs_status",
        ),
        sa.CheckConstraint("progress >= 0 AND progress <= 100", name="ck_background_jobs_progress"),
        sa.CheckConstraint("btrim(public_id) <> ''", name="ck_background_jobs_public_id_not_blank"),
        sa.CheckConstraint("btrim(job_type) <> ''", name="ck_background_jobs_job_type_not_blank"),
        sa.CheckConstraint(
            "jsonb_typeof(payload_json) = 'object'",
            name="ck_background_jobs_payload_json_object",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(result_json) = 'object'",
            name="ck_background_jobs_result_json_object",
        ),
        comment="后台任务表：保存长任务状态和结果摘要；Redis 只作为队列，不保存业务事实。",
    )
    op.create_index("ix_background_jobs_job_type", "background_jobs", ["job_type"])
    op.create_index("ix_background_jobs_status", "background_jobs", ["status"])

    op.create_table(
        "qc_results",
        id_column(),
        sa.Column("project_id", sa.BigInteger(), nullable=False, comment="项目内部主键。"),
        sa.Column("document_id", sa.BigInteger(), comment="文档内部主键。"),
        sa.Column("page_id", sa.BigInteger(), comment="页面内部主键。"),
        sa.Column("revision_id", sa.BigInteger(), comment="标注版本内部主键。"),
        sa.Column("qc_type", sa.Text(), nullable=False, comment="质检类型。"),
        sa.Column("status", sa.Text(), nullable=False, comment="质检状态。"),
        sa.Column("summary", sa.Text(), comment="质检摘要。"),
        sa.Column(
            "details_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="质检详情 JSON。",
        ),
        *timestamp_columns(),
        sa.Column("created_by_job_id", sa.BigInteger(), comment="产生该结果的后台任务。"),
        sa.PrimaryKeyConstraint("id", name="pk_qc_results"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_qc_results_project_id_projects"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name="fk_qc_results_document_id_documents"),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], name="fk_qc_results_page_id_pages"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["annotation_revisions.id"],
            name="fk_qc_results_revision_id_annotation_revisions",
        ),
        sa.ForeignKeyConstraint(
            ["document_id", "project_id"],
            ["documents.id", "documents.project_id"],
            name="fk_qc_results_document_project",
        ),
        sa.ForeignKeyConstraint(
            ["page_id", "document_id"],
            ["pages.id", "pages.document_id"],
            name="fk_qc_results_page_document",
        ),
        sa.ForeignKeyConstraint(
            ["revision_id", "page_id"],
            ["annotation_revisions.id", "annotation_revisions.page_id"],
            name="fk_qc_results_revision_page",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_job_id"],
            ["background_jobs.id"],
            name="fk_qc_results_created_by_job_id_background_jobs",
        ),
        sa.CheckConstraint(
            "qc_type IN ('schema', 'geometry', 'k12_structure', 'dataset', 'export')",
            name="ck_qc_results_qc_type",
        ),
        sa.CheckConstraint("status IN ('passed', 'warning', 'failed')", name="ck_qc_results_status"),
        sa.CheckConstraint("page_id IS NULL OR document_id IS NOT NULL", name="ck_qc_results_page_requires_document"),
        sa.CheckConstraint("revision_id IS NULL OR page_id IS NOT NULL", name="ck_qc_results_revision_requires_page"),
        sa.CheckConstraint("jsonb_typeof(details_json) = 'object'", name="ck_qc_results_details_json_object"),
        comment="质检结果表：保存 schema、geometry、dataset、export 等 QC 结果。",
    )
    op.create_index("ix_qc_results_project_id", "qc_results", ["project_id"])
    op.create_index("ix_qc_results_revision_id", "qc_results", ["revision_id"])
    op.create_index("ix_qc_results_status", "qc_results", ["status"])

    op.create_table(
        "export_jobs",
        id_column(),
        sa.Column("project_id", sa.BigInteger(), nullable=False, comment="项目内部主键。"),
        sa.Column("public_id", sa.Text(), nullable=False, comment="公开导出编号。"),
        sa.Column("export_type", sa.Text(), nullable=False, comment="导出类型。"),
        sa.Column(
            "export_profile_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="导出配置 JSON。",
        ),
        sa.Column(
            "input_scope_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="导出输入范围 JSON。",
        ),
        sa.Column(
            "source_revisions_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
            comment="来源 revision 列表。",
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'queued'"),
            comment="导出状态。",
        ),
        sa.Column("output_dir", sa.Text(), comment="导出输出目录。"),
        sa.Column("report_asset_id", sa.BigInteger(), comment="导出报告资产。"),
        sa.Column("created_by", sa.BigInteger(), comment="创建人。"),
        *timestamp_columns(),
        sa.Column("started_at", sa.DateTime(timezone=True), comment="开始时间。"),
        sa.Column("finished_at", sa.DateTime(timezone=True), comment="结束时间。"),
        sa.Column("error_message", sa.Text(), comment="错误信息。"),
        sa.PrimaryKeyConstraint("id", name="pk_export_jobs"),
        sa.UniqueConstraint("public_id", name="uq_export_jobs_public_id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_export_jobs_project_id_projects"),
        sa.ForeignKeyConstraint(["report_asset_id"], ["assets.id"], name="fk_export_jobs_report_asset_id_assets"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_export_jobs_created_by_users"),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'canceled')",
            name="ck_export_jobs_status",
        ),
        sa.CheckConstraint("btrim(public_id) <> ''", name="ck_export_jobs_public_id_not_blank"),
        sa.CheckConstraint("btrim(export_type) <> ''", name="ck_export_jobs_export_type_not_blank"),
        sa.CheckConstraint(
            "jsonb_typeof(export_profile_json) = 'object'",
            name="ck_export_jobs_export_profile_json_object",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(input_scope_json) = 'object'",
            name="ck_export_jobs_input_scope_json_object",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(source_revisions_json) = 'array'",
            name="ck_export_jobs_source_revisions_json_array",
        ),
        comment="导出任务表：保存导出请求、状态、范围、输出路径和报告资产。",
    )
    op.create_index("ix_export_jobs_project_id", "export_jobs", ["project_id"])
    op.create_index("ix_export_jobs_status", "export_jobs", ["status"])

    op.create_table(
        "audit_logs",
        id_column(),
        sa.Column("project_id", sa.BigInteger(), comment="项目内部主键。"),
        sa.Column("actor_id", sa.BigInteger(), comment="操作人。"),
        sa.Column("action", sa.Text(), nullable=False, comment="动作编码。"),
        sa.Column("resource_type", sa.Text(), nullable=False, comment="资源类型。"),
        sa.Column("resource_id", sa.Text(), comment="资源编号。"),
        sa.Column("before_json", postgresql.JSONB(), comment="操作前快照 JSON。"),
        sa.Column("after_json", postgresql.JSONB(), comment="操作后快照 JSON。"),
        sa.Column("request_id", sa.Text(), comment="请求 ID。"),
        sa.Column("ip_address", postgresql.INET(), comment="客户端 IP。"),
        sa.Column("user_agent", sa.Text(), comment="User-Agent。"),
        sa.Column("prev_hash", sa.CHAR(64), comment="上一条审计哈希。"),
        sa.Column("entry_hash", sa.CHAR(64), comment="当前审计哈希。"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="创建时间。",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="更新时间。audit_logs 禁止 UPDATE。",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_audit_logs_project_id_projects"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], name="fk_audit_logs_actor_id_users"),
        sa.CheckConstraint("btrim(action) <> ''", name="ck_audit_logs_action_not_blank"),
        sa.CheckConstraint("btrim(resource_type) <> ''", name="ck_audit_logs_resource_type_not_blank"),
        sa.CheckConstraint(
            "before_json IS NULL OR jsonb_typeof(before_json) = 'object'",
            name="ck_audit_logs_before_json_object",
        ),
        sa.CheckConstraint(
            "after_json IS NULL OR jsonb_typeof(after_json) = 'object'",
            name="ck_audit_logs_after_json_object",
        ),
        comment="审计日志表：保存角色变更、成员管理、锁定、回滚、导出和下载等关键操作。",
    )
    op.create_index("ix_audit_logs_project_id", "audit_logs", ["project_id"])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def create_updated_at_triggers() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$;
        """
    )

    for table_name in UPDATED_AT_TABLES:
        trigger_name = f"trg_{table_name}_set_updated_at"
        op.execute(f"DROP TRIGGER IF EXISTS {trigger_name} ON {table_name}")
        op.execute(
            f"""
            CREATE TRIGGER {trigger_name}
            BEFORE UPDATE ON {table_name}
            FOR EACH ROW
            EXECUTE FUNCTION set_updated_at()
            """
        )


def create_audit_log_guard() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_logs_mutation()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs is append-only and cannot be %', TG_OP;
        END;
        $$;
        """
    )
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_prevent_mutation ON audit_logs")
    op.execute(
        """
        CREATE TRIGGER trg_audit_logs_prevent_mutation
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_logs_mutation()
        """
    )


def seed_builtin_roles() -> None:
    op.execute(
        """
        INSERT INTO role_registry (
            code,
            display_name,
            scope,
            description,
            permissions_json,
            is_builtin,
            is_active
        )
        VALUES
            (
                'system_admin',
                '系统管理员',
                'system',
                '平台系统级管理角色，不绑定到项目成员。',
                jsonb_build_object(
                    'capabilities',
                    ARRAY[
                        'can_manage_system_users',
                        'can_view_audit_log'
                    ]
                ),
                true,
                true
            ),
            (
                'viewer',
                '只读查看者',
                'project',
                '可查看项目、文档、页面和标注结果。',
                jsonb_build_object(
                    'capabilities',
                    ARRAY[
                        'can_view_project'
                    ]
                ),
                true,
                true
            ),
            (
                'annotator',
                '标注员',
                'project',
                '可创建和编辑草稿标注版本。',
                jsonb_build_object(
                    'capabilities',
                    ARRAY[
                        'can_view_project',
                        'can_create_annotation_revision',
                        'can_submit_revision'
                    ]
                ),
                true,
                true
            ),
            (
                'reviewer',
                '复核员',
                'project',
                '可查看和复核标注版本。',
                jsonb_build_object(
                    'capabilities',
                    ARRAY[
                        'can_view_project',
                        'can_review_revision'
                    ]
                ),
                true,
                true
            ),
            (
                'data_manager',
                '数据管理员',
                'project',
                '可导入资产、管理文档和页面。',
                jsonb_build_object(
                    'capabilities',
                    ARRAY[
                        'can_view_project',
                        'can_upload_assets',
                        'can_import_pages'
                    ]
                ),
                true,
                true
            ),
            (
                'exporter',
                '导出员',
                'project',
                '可创建导出任务和下载导出产物。',
                jsonb_build_object(
                    'capabilities',
                    ARRAY[
                        'can_view_project',
                        'can_create_export_job',
                        'can_download_export'
                    ]
                ),
                true,
                true
            ),
            (
                'project_admin',
                '项目管理员',
                'project',
                '可管理项目成员、标签、关系、锁定、回滚和项目导出。',
                jsonb_build_object(
                    'capabilities',
                    ARRAY[
                        'can_view_project',
                        'can_upload_assets',
                        'can_import_pages',
                        'can_create_annotation_revision',
                        'can_submit_revision',
                        'can_review_revision',
                        'can_manage_labels',
                        'can_manage_relations',
                        'can_manage_project_members',
                        'can_create_export_job',
                        'can_download_export',
                        'can_lock_revision',
                        'can_unlock_revision',
                        'can_rollback_revision',
                        'can_view_audit_log'
                    ]
                ),
                true,
                true
            )
        ON CONFLICT (code) DO UPDATE SET
            display_name = EXCLUDED.display_name,
            scope = EXCLUDED.scope,
            description = EXCLUDED.description,
            permissions_json = EXCLUDED.permissions_json,
            is_builtin = true,
            is_active = true,
            updated_at = now()
        """
    )


def drop_updated_at_triggers() -> None:
    for table_name in UPDATED_AT_TABLES:
        trigger_name = f"trg_{table_name}_set_updated_at"
        op.execute(f"DROP TRIGGER IF EXISTS {trigger_name} ON {table_name}")


def drop_audit_log_guard() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_prevent_mutation ON audit_logs")
