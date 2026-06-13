from pathlib import Path

from app.db.base import Base
import app.db.models.core  # noqa: F401


BACKEND_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = BACKEND_ROOT / "alembic" / "versions" / "20260603_0001_create_core_tables.py"
ROLE_MIGRATION_PATH = (
    BACKEND_ROOT
    / "alembic"
    / "versions"
    / "20260603_0002_update_builtin_role_capabilities.py"
)
SEED_ADMIN_MIGRATION_PATH = (
    BACKEND_ROOT
    / "alembic"
    / "versions"
    / "20260608_0003_seed_default_admin.py"
)
RELAX_ANNOTATION_OBJECTS_MIGRATION_PATH = (
    BACKEND_ROOT
    / "alembic"
    / "versions"
    / "20260608_0004_relax_annotation_object_index_constraints.py"
)
PROJECT_CREATED_BY_MIGRATION_PATH = (
    BACKEND_ROOT
    / "alembic"
    / "versions"
    / "20260609_0005_add_project_created_by.py"
)
SCHEMA_SQL_PATH = BACKEND_ROOT / "sql" / "schema" / "001_create_core_tables.sql"


def test_m2_models_register_expected_table_count() -> None:
    assert len(Base.metadata.tables) == 16


def test_initial_migration_is_static_snapshot() -> None:
    source = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "Base.metadata" not in source
    assert "import app.db.models" not in source
    assert "op.create_table(" in source


def test_builtin_role_seed_uses_documented_capabilities() -> None:
    sources = [
        MIGRATION_PATH.read_text(encoding="utf-8"),
        SCHEMA_SQL_PATH.read_text(encoding="utf-8"),
    ]
    legacy_capability_markers = [
        "system.admin",
        "project.read",
        "annotation.write",
        "export.create",
        "role.bind",
        "member.manage",
    ]
    required_capability_markers = [
        "can_view_project",
        "can_create_annotation_revision",
        "can_submit_revision",
        "can_review_revision",
        "can_manage_project_members",
        "can_create_export_job",
        "can_download_export",
        "can_lock_revision",
        "can_unlock_revision",
        "can_rollback_revision",
        "can_view_audit_log",
        "can_manage_system_users",
    ]

    for source in sources:
        for marker in legacy_capability_markers:
            assert marker not in source
        for marker in required_capability_markers:
            assert marker in source


def test_role_capability_data_migration_updates_existing_databases() -> None:
    source = ROLE_MIGRATION_PATH.read_text(encoding="utf-8")

    assert 'revision: str = "20260603_0002"' in source
    assert 'down_revision: str | None = "20260603_0001"' in source
    assert "UPDATE role_registry" in source
    assert "can_upload_assets" in source
    assert "project.read" in source


def test_post_m2_migrations_use_unique_linear_revision_chain() -> None:
    seed_source = SEED_ADMIN_MIGRATION_PATH.read_text(encoding="utf-8")
    relax_source = RELAX_ANNOTATION_OBJECTS_MIGRATION_PATH.read_text(encoding="utf-8")
    created_by_source = PROJECT_CREATED_BY_MIGRATION_PATH.read_text(encoding="utf-8")

    assert 'revision: str = "20260608_0003"' in seed_source
    assert 'down_revision: str | None = "20260603_0002"' in seed_source
    assert 'revision: str = "20260608_0004"' in relax_source
    assert 'down_revision: str | None = "20260608_0003"' in relax_source
    assert 'revision: str = "20260609_0005"' in created_by_source
    assert 'down_revision: str | None = "20260608_0004"' in created_by_source


def test_project_created_by_migration_avoids_hard_coded_admin_id() -> None:
    source = PROJECT_CREATED_BY_MIGRATION_PATH.read_text(encoding="utf-8")

    assert "WHERE username = :admin_username" in source
    assert "UPDATE projects SET created_by = :admin_id" in source
    assert "created_by = 1" not in source
