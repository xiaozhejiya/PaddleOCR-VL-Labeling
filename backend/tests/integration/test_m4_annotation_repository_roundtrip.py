from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import (
    AnnotationObject,
    Asset,
    Document,
    Page,
    Project,
    RelationObject,
    User,
)
import app.db.models.core  # noqa: F401
from app.services.annotation_service import (
    create_annotation_revision,
    get_annotation_revision,
)
from app.storage.annotation_json import AnnotationJsonStorage


TEST_DATABASE_URL = os.environ.get("K12_TEST_DATABASE_URL")


pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="需要设置 K12_TEST_DATABASE_URL 才运行真实 PostgreSQL repository 集成测试。",
)


def sample_annotation_json() -> dict[str, object]:
    return {
        "schema_version": "k12_annotation_v0.1",
        "page_id": "page_public_001",
        "k12_annotations": [
            {
                "id": "ann_question_001",
                "type": "question_block",
                "label_namespace": "k12",
                "geometry": {"bbox_xyxy": [10, 20, 110, 120]},
                "read_order": 1,
                "attributes": {"question_number": "1"},
                "source_refs": [{"type": "human"}],
                "status": "draft",
            },
            {
                "id": "ann_option_001",
                "type": "option_block",
                "label_namespace": "k12",
                "geometry": {"bbox_xyxy": [20, 130, 80, 170]},
                "read_order": 2,
                "attributes": {"option_label": "A"},
                "source_refs": [],
                "status": "draft",
            },
        ],
        "relations": [
            {
                "id": "rel_question_option_001",
                "type": "question_contains_option",
                "from_id": "ann_question_001",
                "to_id": "ann_option_001",
                "attributes": {},
                "status": "active",
            }
        ],
    }


def test_m4_annotation_revision_roundtrip_uses_real_sqlalchemy_repository(
    tmp_path: Path,
) -> None:
    assert TEST_DATABASE_URL is not None
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    schema_name = f"test_m4_{uuid4().hex}"

    with engine.connect() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
        connection.execute(text(f'SET search_path TO "{schema_name}"'))
        try:
            Base.metadata.create_all(connection)
            db = Session(bind=connection, expire_on_commit=False)
            _seed_page(db)

            revision = create_annotation_revision(
                db=db,
                page_public_id="page_public_001",
                annotation_json=sample_annotation_json(),
                created_by=99,
                storage=AnnotationJsonStorage(tmp_path),
            )
            result = get_annotation_revision(
                db=db,
                revision_public_id=revision.public_id,
                storage=AnnotationJsonStorage(tmp_path),
            )

            assert result["revision"].public_id == revision.public_id
            assert (
                result["annotation_json"]["history"][-1]["revision_id"]
                == revision.public_id
            )
            assert db.scalars(select(AnnotationObject)).all()[0].source_refs_json == [
                {"type": "human"}
            ]
            assert len(db.scalars(select(AnnotationObject)).all()) == 2
            assert len(db.scalars(select(RelationObject)).all()) == 1
        finally:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
            connection.commit()


def _seed_page(db: Session) -> None:
    db.add(
        User(
            id=99,
            username="annotator",
            display_name="标注员",
            status="active",
        )
    )
    db.add(Project(id=10, name="测试项目", schema_version="v1", created_by=99))
    db.add(
        Asset(
            id=1,
            public_id="asset_image_001",
            asset_type="page_image",
            storage_path="raw/assets/aa/asset_image_001.original.png",
            original_filename="paper.png",
            mime_type="image/png",
            size_bytes=128,
            sha256="a" * 64,
            width=200,
            height=300,
            created_by=99,
            readonly=True,
        )
    )
    db.add(
        Document(
            id=20,
            public_id="doc_public_001",
            project_id=10,
            document_type="uploaded_image",
            source_type="upload",
            domain_metadata_json={},
            split="train",
            lock_status="unlocked",
        )
    )
    db.add(
        Page(
            id=30,
            document_id=20,
            public_id="page_public_001",
            page_index=0,
            image_asset_id=1,
            width=200,
            height=300,
            capture_method="upload",
            visual_difficulty="medium",
            status="imported",
        )
    )
    db.commit()
