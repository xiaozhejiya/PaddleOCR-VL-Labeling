"""M4 标注 revision 服务测试。

覆盖事项：
1. revision JSON 保存前要校验 bbox，并为矩形 bbox 自动派生 quad / polygon。
2. 保存 revision 后要从整页 JSON 重建 annotation_objects 和 relation_objects 索引。
3. read_order 随 revision JSON 保存，并进入 annotation_objects.read_order 索引。
4. 同一页面连续保存时 revision_no 递增，历史 revision JSON 不被覆盖。
5. 非法 bbox 必须在写文件和建索引前被拒绝。
"""

from __future__ import annotations

import importlib
import importlib.util
import json
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


def load_annotation_service() -> Any:
    module_name = "app.services.annotation_service"
    if importlib.util.find_spec(module_name) is None:
        pytest.fail("M4 未实现：缺少 app.services.annotation_service")
    return importlib.import_module(module_name)


def sample_annotation_json(*, bbox: list[int] | None = None) -> dict[str, Any]:
    question_bbox = bbox or [10, 20, 110, 120]
    return {
        "schema_version": "k12_annotation_v0.1",
        "page_id": "page_public_001",
        "k12_annotations": [
            {
                "id": "ann_question_001",
                "type": "question_block",
                "label_namespace": "k12",
                "geometry": {"bbox_xyxy": question_bbox},
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


def test_build_revision_indexes_derives_geometry_and_read_order() -> None:
    annotation_service = load_annotation_service()

    result = annotation_service.build_revision_indexes(
        annotation_json=sample_annotation_json(),
        page_width=200,
        page_height=300,
    )

    normalized_question = result.annotation_json["k12_annotations"][0]
    assert normalized_question["geometry"]["quad"] == [
        [10, 20],
        [110, 20],
        [110, 120],
        [10, 120],
    ]
    assert normalized_question["geometry"]["polygon"] == [
        [10, 20],
        [110, 20],
        [110, 120],
        [10, 120],
    ]
    assert normalized_question["geometry"]["geometry_source"] == "auto_generated"

    assert result.annotation_objects[0] == {
        "ann_id": "ann_question_001",
        "label_namespace": "k12",
        "label_name": "question_block",
        "bbox_xyxy": [10, 20, 110, 120],
        "quad": [[10, 20], [110, 20], [110, 120], [10, 120]],
        "polygon": [[10, 20], [110, 20], [110, 120], [10, 120]],
        "read_order": 1,
        "attributes_json": {"question_number": "1"},
        "source_refs_json": [{"type": "human"}],
        "status": "draft",
    }
    assert result.relation_objects == [
        {
            "rel_id": "rel_question_option_001",
            "relation_type": "question_contains_option",
            "from_ann_id": "ann_question_001",
            "to_ann_id": "ann_option_001",
            "attributes_json": {},
            "status": "active",
        }
    ]


def test_build_revision_indexes_rejects_out_of_bounds_bbox() -> None:
    annotation_service = load_annotation_service()

    with pytest.raises(annotation_service.InvalidAnnotationError, match="bbox"):
        annotation_service.build_revision_indexes(
            annotation_json=sample_annotation_json(bbox=[-1, 20, 110, 120]),
            page_width=200,
            page_height=300,
        )


def test_build_revision_indexes_rejects_duplicate_annotation_ids() -> None:
    annotation_service = load_annotation_service()
    annotation_json = sample_annotation_json()
    annotation_json["k12_annotations"][1]["id"] = "ann_question_001"

    with pytest.raises(annotation_service.InvalidAnnotationError, match="重复"):
        annotation_service.build_revision_indexes(
            annotation_json=annotation_json,
            page_width=200,
            page_height=300,
        )


def test_build_revision_indexes_requires_k12_annotations_field() -> None:
    annotation_service = load_annotation_service()
    annotation_json = sample_annotation_json()
    annotation_json.pop("k12_annotations")
    annotation_json["relations"] = []

    with pytest.raises(
        annotation_service.InvalidAnnotationError,
        match="k12_annotations",
    ):
        annotation_service.build_revision_indexes(
            annotation_json=annotation_json,
            page_width=200,
            page_height=300,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("attributes", [], "attributes"),
        ("attributes", "", "attributes"),
        ("source_refs", "", "source_refs"),
        ("source_refs", 0, "source_refs"),
    ],
)
def test_build_revision_indexes_rejects_explicit_bad_optional_container_types(
    field: str,
    value: Any,
    message: str,
) -> None:
    annotation_service = load_annotation_service()
    annotation_json = sample_annotation_json()
    annotation_json["k12_annotations"][0][field] = value

    with pytest.raises(annotation_service.InvalidAnnotationError, match=message):
        annotation_service.build_revision_indexes(
            annotation_json=annotation_json,
            page_width=200,
            page_height=300,
        )


@pytest.mark.parametrize(
    "bbox",
    [
        [10, 20, 10, 120],
        [10, 20, "110", 120],
        [10, 20, 110],
        [10, 20, 201, 120],
    ],
)
def test_build_revision_indexes_rejects_malformed_bbox(bbox: list[Any]) -> None:
    annotation_service = load_annotation_service()

    with pytest.raises(annotation_service.InvalidAnnotationError, match="bbox"):
        annotation_service.build_revision_indexes(
            annotation_json=sample_annotation_json(bbox=bbox),
            page_width=200,
            page_height=300,
        )


@pytest.mark.parametrize("read_order", [0, -1, "1", True])
def test_build_revision_indexes_rejects_invalid_read_order(read_order: Any) -> None:
    annotation_service = load_annotation_service()
    annotation_json = sample_annotation_json()
    annotation_json["k12_annotations"][0]["read_order"] = read_order

    with pytest.raises(annotation_service.InvalidAnnotationError, match="read_order"):
        annotation_service.build_revision_indexes(
            annotation_json=annotation_json,
            page_width=200,
            page_height=300,
        )


def test_build_revision_indexes_rejects_duplicate_read_order() -> None:
    annotation_service = load_annotation_service()
    annotation_json = sample_annotation_json()
    annotation_json["k12_annotations"][1]["read_order"] = 1

    with pytest.raises(annotation_service.InvalidAnnotationError, match="read_order"):
        annotation_service.build_revision_indexes(
            annotation_json=annotation_json,
            page_width=200,
            page_height=300,
        )


def test_build_revision_indexes_rejects_polygon_outside_page() -> None:
    annotation_service = load_annotation_service()
    annotation_json = sample_annotation_json()
    annotation_json["k12_annotations"][0]["geometry"]["polygon"] = [
        [10, 20],
        [110, 20],
        [110, 301],
        [10, 120],
    ]

    with pytest.raises(annotation_service.InvalidAnnotationError, match="polygon"):
        annotation_service.build_revision_indexes(
            annotation_json=annotation_json,
            page_width=200,
            page_height=300,
        )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda value: value["relations"][0].update({"to_id": "ann_missing"}),
            "不存在",
        ),
        (
            lambda value: value["relations"][0].update({"to_id": "ann_question_001"}),
            "不能是同一个",
        ),
        (
            lambda value: value["relations"].append(deepcopy(value["relations"][0])),
            "重复",
        ),
    ],
)
def test_build_revision_indexes_rejects_invalid_relations(
    mutate: Any,
    message: str,
) -> None:
    annotation_service = load_annotation_service()
    annotation_json = sample_annotation_json()
    mutate(annotation_json)

    with pytest.raises(annotation_service.InvalidAnnotationError, match=message):
        annotation_service.build_revision_indexes(
            annotation_json=annotation_json,
            page_width=200,
            page_height=300,
        )


@dataclass
class StoredJsonAsset:
    public_id: str
    storage_path: str
    sha256: str
    size_bytes: int


class RecordingAnnotationJsonStorage:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.writes: list[StoredJsonAsset] = []

    def write_revision_json(
        self,
        *,
        revision_public_id: str,
        annotation_json: dict[str, Any],
    ) -> StoredJsonAsset:
        content = json.dumps(
            annotation_json,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        storage_path = f"annotations/{revision_public_id}.json"
        target_path = self.root / storage_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        assert not target_path.exists(), "历史 revision JSON 不能被覆盖"
        target_path.write_bytes(content)
        asset = StoredJsonAsset(
            public_id=f"asset_{revision_public_id}",
            storage_path=storage_path,
            sha256=sha256(content).hexdigest(),
            size_bytes=len(content),
        )
        self.writes.append(asset)
        return asset

    def read_revision_json(self, storage_path: str) -> dict[str, Any]:
        return json.loads((self.root / storage_path).read_text(encoding="utf-8"))

    def remove_revision_json(self, storage_path: str) -> None:
        (self.root / storage_path).unlink(missing_ok=True)


class RecordingAnnotationRepository:
    def __init__(self) -> None:
        self.latest_revision_no = 0
        self.revisions: list[Any] = []
        self.object_indexes: dict[str, list[dict[str, Any]]] = {}
        self.relation_indexes: dict[str, list[dict[str, Any]]] = {}
        self.revision_assets: dict[str, StoredJsonAsset] = {}

    def get_page_context_by_public_id(self, _db: object, page_public_id: str) -> Any:
        assert page_public_id == "page_public_001"
        return {
            "page_id": 30,
            "page_public_id": page_public_id,
            "document_id": 20,
            "project_id": 10,
            "width": 200,
            "height": 300,
        }

    def get_latest_revision_no(self, _db: object, *, page_id: int) -> int:
        assert page_id == 30
        return self.latest_revision_no

    def create_revision(self, _db: object, **kwargs: Any) -> Any:
        self.latest_revision_no = kwargs["revision_no"]
        revision = type("RevisionRecord", (), kwargs)()
        self.revisions.append(revision)
        self.revision_assets[revision.public_id] = kwargs["annotation_json_asset"]
        return revision

    def rebuild_indexes(
        self,
        _db: object,
        *,
        revision_public_id: str,
        annotation_objects: list[dict[str, Any]],
        relation_objects: list[dict[str, Any]],
    ) -> None:
        self.object_indexes[revision_public_id] = annotation_objects
        self.relation_indexes[revision_public_id] = relation_objects

    def get_latest_revision(self, _db: object, *, page_public_id: str) -> Any:
        assert page_public_id == "page_public_001"
        return self.revisions[-1] if self.revisions else None

    def get_revision_asset(
        self, _db: object, *, revision: Any
    ) -> StoredJsonAsset | None:
        return self.revision_assets.get(revision.public_id)


def test_create_revision_appends_json_asset_and_increments_revision_no(
    tmp_path: Path,
) -> None:
    annotation_service = load_annotation_service()
    repository = RecordingAnnotationRepository()
    storage = RecordingAnnotationJsonStorage(tmp_path)

    first = annotation_service.create_annotation_revision(
        db=object(),
        page_public_id="page_public_001",
        annotation_json=sample_annotation_json(),
        created_by=99,
        repository=repository,
        storage=storage,
        change_summary="首次标注",
    )
    second_json = sample_annotation_json()
    second_json["k12_annotations"][0]["attributes"]["question_number"] = "2"
    second = annotation_service.create_annotation_revision(
        db=object(),
        page_public_id="page_public_001",
        annotation_json=second_json,
        created_by=99,
        repository=repository,
        storage=storage,
        change_summary="继续标注",
        base_revision_id=first.public_id,
    )

    assert first.revision_no == 1
    assert second.revision_no == 2
    assert first.public_id != second.public_id
    assert len(storage.writes) == 2
    assert storage.writes[0].storage_path != storage.writes[1].storage_path
    assert (tmp_path / storage.writes[0].storage_path).exists()
    assert (tmp_path / storage.writes[1].storage_path).exists()

    first_objects = repository.object_indexes[first.public_id]
    second_objects = repository.object_indexes[second.public_id]
    assert first_objects[0]["read_order"] == 1
    assert second_objects[0]["attributes_json"]["question_number"] == "2"
    assert (
        repository.get_latest_revision(object(), page_public_id="page_public_001")
        is second
    )
    second_revision_json = storage.read_revision_json(storage.writes[1].storage_path)
    assert [item["revision_no"] for item in second_revision_json["history"]] == [1, 2]
    assert second_revision_json["history"][0]["revision_id"] == first.public_id
    assert second_revision_json["history"][1]["parent_revision_id"] == first.public_id


def test_create_revision_ignores_client_supplied_history_when_appending_revision_chain(
    tmp_path: Path,
) -> None:
    annotation_service = load_annotation_service()
    repository = RecordingAnnotationRepository()
    storage = RecordingAnnotationJsonStorage(tmp_path)

    first = annotation_service.create_annotation_revision(
        db=object(),
        page_public_id="page_public_001",
        annotation_json=sample_annotation_json(),
        created_by=99,
        repository=repository,
        storage=storage,
    )
    forged_second_json = sample_annotation_json()
    forged_second_json["history"] = [
        {
            "revision_id": "rev_fake_001",
            "revision_no": 999,
            "parent_revision_id": "rev_fake_000",
        }
    ]

    second = annotation_service.create_annotation_revision(
        db=object(),
        page_public_id="page_public_001",
        annotation_json=forged_second_json,
        created_by=99,
        repository=repository,
        storage=storage,
        base_revision_id=first.public_id,
    )

    second_revision_json = storage.read_revision_json(storage.writes[1].storage_path)
    assert [item["revision_id"] for item in second_revision_json["history"]] == [
        first.public_id,
        second.public_id,
    ]


def test_create_revision_rejects_missing_base_revision_when_latest_exists(
    tmp_path: Path,
) -> None:
    annotation_service = load_annotation_service()
    repository = RecordingAnnotationRepository()
    storage = RecordingAnnotationJsonStorage(tmp_path)
    first = annotation_service.create_annotation_revision(
        db=object(),
        page_public_id="page_public_001",
        annotation_json=sample_annotation_json(),
        created_by=99,
        repository=repository,
        storage=storage,
    )

    with pytest.raises(
        annotation_service.RevisionConflictError, match="base_revision_id"
    ):
        annotation_service.create_annotation_revision(
            db=object(),
            page_public_id="page_public_001",
            annotation_json=sample_annotation_json(),
            created_by=99,
            repository=repository,
            storage=storage,
        )

    assert first in repository.revisions
    assert len(storage.writes) == 1


def test_create_revision_rejects_stale_base_revision_before_writing_json(
    tmp_path: Path,
) -> None:
    annotation_service = load_annotation_service()
    repository = RecordingAnnotationRepository()
    storage = RecordingAnnotationJsonStorage(tmp_path)
    first = annotation_service.create_annotation_revision(
        db=object(),
        page_public_id="page_public_001",
        annotation_json=sample_annotation_json(),
        created_by=99,
        repository=repository,
        storage=storage,
    )
    second = annotation_service.create_annotation_revision(
        db=object(),
        page_public_id="page_public_001",
        annotation_json=sample_annotation_json(),
        created_by=99,
        repository=repository,
        storage=storage,
        base_revision_id=first.public_id,
    )

    with pytest.raises(annotation_service.RevisionConflictError, match="latest"):
        annotation_service.create_annotation_revision(
            db=object(),
            page_public_id="page_public_001",
            annotation_json=sample_annotation_json(),
            created_by=99,
            repository=repository,
            storage=storage,
            base_revision_id=first.public_id,
        )

    assert second is repository.revisions[-1]
    assert len(storage.writes) == 2


def test_create_revision_rejects_invalid_bbox_before_writing_json(
    tmp_path: Path,
) -> None:
    annotation_service = load_annotation_service()
    repository = RecordingAnnotationRepository()
    storage = RecordingAnnotationJsonStorage(tmp_path)

    with pytest.raises(annotation_service.InvalidAnnotationError, match="bbox"):
        annotation_service.create_annotation_revision(
            db=object(),
            page_public_id="page_public_001",
            annotation_json=sample_annotation_json(bbox=[10, 20, 500, 120]),
            created_by=99,
            repository=repository,
            storage=storage,
            change_summary="非法 bbox",
        )

    assert storage.writes == []
    assert repository.revisions == []
    assert repository.object_indexes == {}


def test_create_revision_rejects_payload_page_id_mismatch_before_writing_json(
    tmp_path: Path,
) -> None:
    annotation_service = load_annotation_service()
    repository = RecordingAnnotationRepository()
    storage = RecordingAnnotationJsonStorage(tmp_path)
    annotation_json = sample_annotation_json()
    annotation_json["page_id"] = "page_other_001"

    with pytest.raises(annotation_service.InvalidAnnotationError, match="page_id"):
        annotation_service.create_annotation_revision(
            db=object(),
            page_public_id="page_public_001",
            annotation_json=annotation_json,
            created_by=99,
            repository=repository,
            storage=storage,
            change_summary="页面不一致",
        )

    assert storage.writes == []
    assert repository.revisions == []
    assert repository.object_indexes == {}


class FailingAnnotationRepository(RecordingAnnotationRepository):
    def create_revision(self, _db: object, **_kwargs: Any) -> Any:
        raise RuntimeError("revision insert failed")


def test_create_revision_removes_written_json_when_database_write_fails(
    tmp_path: Path,
) -> None:
    annotation_service = load_annotation_service()
    repository = FailingAnnotationRepository()
    storage = RecordingAnnotationJsonStorage(tmp_path)

    with pytest.raises(RuntimeError, match="revision insert failed"):
        annotation_service.create_annotation_revision(
            db=object(),
            page_public_id="page_public_001",
            annotation_json=sample_annotation_json(),
            created_by=99,
            repository=repository,
            storage=storage,
            change_summary="数据库失败",
        )

    assert len(storage.writes) == 1
    assert not (tmp_path / storage.writes[0].storage_path).exists()
    assert repository.object_indexes == {}


class EmptyLatestRevisionRepository:
    def get_latest_revision(self, _db: object, *, page_public_id: str) -> None:
        assert page_public_id == "page_public_001"
        return None


def test_get_latest_annotation_revision_rejects_page_without_revision() -> None:
    annotation_service = load_annotation_service()

    with pytest.raises(
        annotation_service.AnnotationRevisionNotFoundError,
        match="还没有标注版本",
    ):
        annotation_service.get_latest_annotation_revision(
            db=object(),
            page_public_id="page_public_001",
            repository=EmptyLatestRevisionRepository(),
            storage=object(),
        )
