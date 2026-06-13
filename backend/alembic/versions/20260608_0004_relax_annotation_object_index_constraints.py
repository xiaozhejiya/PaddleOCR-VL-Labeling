from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision: str = "20260608_0004"
down_revision: str | None = "20260608_0003"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_annotation_objects_status",
        "annotation_objects",
        type_="check",
    )
    op.create_check_constraint(
        "ck_annotation_objects_status",
        "annotation_objects",
        "status IN ('draft', 'active', 'deleted')",
    )
    op.drop_constraint(
        "ck_annotation_objects_source_refs_json_object",
        "annotation_objects",
        type_="check",
    )
    op.create_check_constraint(
        "ck_annotation_objects_source_refs_json_container",
        "annotation_objects",
        "jsonb_typeof(source_refs_json) IN ('object', 'array')",
    )
    op.alter_column(
        "annotation_objects",
        "source_refs_json",
        server_default=sa.text("'[]'::jsonb"),
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_annotation_objects_source_refs_json_container",
        "annotation_objects",
        type_="check",
    )
    op.create_check_constraint(
        "ck_annotation_objects_source_refs_json_object",
        "annotation_objects",
        "jsonb_typeof(source_refs_json) = 'object'",
    )
    op.drop_constraint(
        "ck_annotation_objects_status",
        "annotation_objects",
        type_="check",
    )
    op.create_check_constraint(
        "ck_annotation_objects_status",
        "annotation_objects",
        "status IN ('active', 'deleted')",
    )
    op.alter_column(
        "annotation_objects",
        "source_refs_json",
        server_default=sa.text("'{}'::jsonb"),
    )
