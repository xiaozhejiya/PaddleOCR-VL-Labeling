from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from numbers import Real
from typing import Any, Protocol

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.annotations import SqlAlchemyAnnotationRepository
from app.storage.annotation_json import AnnotationJsonStorage, StoredJsonAsset
from app.utils.ids import new_public_id

logger = logging.getLogger(__name__)


class InvalidAnnotationError(ValueError):
    """标注 JSON 不满足 M4 基础 schema 或几何约束。"""


class PageNotFoundError(ValueError):
    """页面不存在。"""


class AnnotationRevisionNotFoundError(ValueError):
    """页面还没有标注版本。"""


class RevisionConflictError(ValueError):
    """提交基于的 revision 已不是当前 latest，调用方需要重新加载或合并。"""


class AnnotationRepositoryProtocol(Protocol):
    def get_page_context_by_public_id(
        self, db: object, page_public_id: str
    ) -> dict[str, Any] | None: ...

    def get_latest_revision_no(self, db: object, *, page_id: int) -> int: ...

    def get_latest_revision(self, db: object, *, page_public_id: str) -> Any | None: ...

    def get_revision_by_public_id(
        self, db: object, *, revision_public_id: str
    ) -> Any | None: ...

    def get_revision_asset(self, db: object, *, revision: Any) -> Any | None: ...

    def list_revisions(
        self,
        db: object,
        *,
        page_public_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Any], int]: ...

    def create_revision(self, db: object, **kwargs: Any) -> Any: ...

    def rebuild_indexes(
        self,
        db: object,
        *,
        revision_public_id: str,
        annotation_objects: list[dict[str, Any]],
        relation_objects: list[dict[str, Any]],
    ) -> None: ...


class AnnotationJsonStorageProtocol(Protocol):
    def write_revision_json(
        self,
        *,
        revision_public_id: str,
        annotation_json: dict[str, Any],
    ) -> StoredJsonAsset: ...

    def read_revision_json(self, storage_path: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class RevisionIndexBuildResult:
    annotation_json: dict[str, Any]
    annotation_objects: list[dict[str, Any]]
    relation_objects: list[dict[str, Any]]


DEFAULT_REPOSITORY = SqlAlchemyAnnotationRepository()


def build_revision_indexes(
    *,
    annotation_json: dict[str, Any],
    page_width: int,
    page_height: int,
) -> RevisionIndexBuildResult:
    """校验整页 annotation JSON，并抽取数据库索引行。"""

    normalized_json = deepcopy(annotation_json)
    annotations = _require_list(normalized_json, "k12_annotations")
    relations = normalized_json.get("relations", [])
    if not isinstance(relations, list):
        raise InvalidAnnotationError("relations 必须是数组。")

    seen_ann_ids: set[str] = set()
    seen_read_orders: set[int] = set()
    annotation_objects: list[dict[str, Any]] = []
    for index, annotation in enumerate(annotations):
        if not isinstance(annotation, dict):
            raise InvalidAnnotationError(f"k12_annotations[{index}] 必须是对象。")
        ann_id = _require_text(annotation, "id", f"k12_annotations[{index}].id")
        if ann_id in seen_ann_ids:
            raise InvalidAnnotationError(f"标注对象 id 重复：{ann_id}")
        seen_ann_ids.add(ann_id)

        label_namespace = _require_text(
            annotation,
            "label_namespace",
            f"k12_annotations[{index}].label_namespace",
        )
        label_name = _read_label_name(annotation, index)
        geometry = _require_geometry(annotation, index)
        had_quad = geometry.get("quad") is not None
        had_polygon = geometry.get("polygon") is not None
        bbox = _normalize_bbox(
            geometry.get("bbox_xyxy"),
            page_width=page_width,
            page_height=page_height,
            field=f"k12_annotations[{index}].geometry.bbox_xyxy",
        )
        if bbox is not None:
            geometry["bbox_xyxy"] = bbox
            geometry.setdefault("quad", _bbox_to_polygon(bbox))
            geometry.setdefault("polygon", _bbox_to_polygon(bbox))
            if "geometry_source" not in geometry:
                geometry["geometry_source"] = (
                    "manual" if (had_quad or had_polygon) else "auto_generated"
                )
        elif "geometry_source" not in geometry and (had_quad or had_polygon):
            geometry["geometry_source"] = "manual"

        quad = _normalize_polygon_like(
            geometry.get("quad"),
            expected_points=4,
            field=f"k12_annotations[{index}].geometry.quad",
            page_width=page_width,
            page_height=page_height,
        )
        polygon = _normalize_polygon_like(
            geometry.get("polygon"),
            expected_points=None,
            field=f"k12_annotations[{index}].geometry.polygon",
            page_width=page_width,
            page_height=page_height,
        )
        if quad is not None:
            geometry["quad"] = quad
        if polygon is not None:
            geometry["polygon"] = polygon
        if bbox is None and quad is None and polygon is None:
            raise InvalidAnnotationError("标注对象必须至少包含 bbox、quad 或 polygon。")

        read_order = _normalize_read_order(annotation.get("read_order"), index)
        if read_order is not None:
            if read_order in seen_read_orders:
                raise InvalidAnnotationError(f"read_order 重复：{read_order}")
            seen_read_orders.add(read_order)
        attributes = _optional_mapping(
            annotation,
            key="attributes",
            default={},
            message="attributes 必须是对象。",
        )
        source_refs = _optional_container(
            annotation,
            key="source_refs",
            default=[],
            message="source_refs 必须是数组或对象。",
        )
        status = annotation.get("status") or "active"
        if status not in {"draft", "active", "deleted"}:
            raise InvalidAnnotationError(
                "标注对象 status 只能是 draft / active / deleted。"
            )

        annotation_objects.append(
            {
                "ann_id": ann_id,
                "label_namespace": label_namespace,
                "label_name": label_name,
                "bbox_xyxy": bbox,
                "quad": geometry.get("quad"),
                "polygon": geometry.get("polygon"),
                "read_order": read_order,
                "attributes_json": attributes,
                "source_refs_json": source_refs,
                "status": status,
            }
        )

    relation_objects = _build_relation_indexes(relations, seen_ann_ids)
    return RevisionIndexBuildResult(
        annotation_json=normalized_json,
        annotation_objects=annotation_objects,
        relation_objects=relation_objects,
    )


def get_page_detail(
    *,
    db: Session,
    page_public_id: str,
    repository: SqlAlchemyAnnotationRepository | None = None,
) -> dict[str, Any]:
    repo = repository or DEFAULT_REPOSITORY
    page_context = repo.get_page_context_by_public_id(db, page_public_id)
    if page_context is None:
        raise PageNotFoundError(f"页面不存在：{page_public_id}")
    return page_context


def get_latest_annotation_revision(
    *,
    db: Session,
    page_public_id: str,
    repository: SqlAlchemyAnnotationRepository | None = None,
    storage: AnnotationJsonStorage | None = None,
) -> dict[str, Any]:
    repo = repository or DEFAULT_REPOSITORY
    json_storage = storage or AnnotationJsonStorage()
    revision = repo.get_latest_revision(db, page_public_id=page_public_id)
    if revision is None:
        raise AnnotationRevisionNotFoundError(f"页面还没有标注版本：{page_public_id}")
    asset = repo.get_revision_asset(db, revision=revision)
    if asset is None:
        raise AnnotationRevisionNotFoundError("标注 revision JSON 资产不存在。")
    return {
        "revision": revision,
        "asset": asset,
        "annotation_json": json_storage.read_revision_json(asset.storage_path),
    }


def get_annotation_revision(
    *,
    db: Session,
    revision_public_id: str,
    repository: AnnotationRepositoryProtocol | None = None,
    storage: AnnotationJsonStorage | None = None,
) -> dict[str, Any]:
    repo = repository or DEFAULT_REPOSITORY
    json_storage = storage or AnnotationJsonStorage()
    revision = repo.get_revision_by_public_id(db, revision_public_id=revision_public_id)
    if revision is None:
        raise AnnotationRevisionNotFoundError(f"标注版本不存在：{revision_public_id}")
    asset = repo.get_revision_asset(db, revision=revision)
    if asset is None:
        raise AnnotationRevisionNotFoundError("标注 revision JSON 资产不存在。")
    return {
        "revision": revision,
        "asset": asset,
        "annotation_json": json_storage.read_revision_json(asset.storage_path),
    }


def list_annotation_revisions(
    *,
    db: Session,
    page_public_id: str,
    limit: int = 50,
    offset: int = 0,
    repository: AnnotationRepositoryProtocol | None = None,
) -> tuple[list[Any], int]:
    repo = repository or DEFAULT_REPOSITORY
    return repo.list_revisions(db, page_public_id=page_public_id, limit=limit, offset=offset)


def create_annotation_revision(
    *,
    db: Session,
    page_public_id: str,
    annotation_json: dict[str, Any],
    created_by: int,
    repository: AnnotationRepositoryProtocol | None = None,
    storage: AnnotationJsonStorageProtocol | None = None,
    change_summary: str | None = None,
    change_reason: str | None = None,
    base_revision_id: str | None = None,
) -> Any:
    """创建新的页面标注 revision，并重建对象和关系索引。

    事务顺序：先读取页面上下文和最新版本号，再在内存中完成 schema/geometry
    校验；只有校验通过后才写 revision JSON 和数据库索引，避免非法 bbox
    留下历史文件或半成品索引。
    """

    repo = repository or DEFAULT_REPOSITORY
    json_storage = storage or AnnotationJsonStorage()
    page_context = repo.get_page_context_by_public_id(db, page_public_id)
    if page_context is None:
        raise PageNotFoundError(f"页面不存在：{page_public_id}")
    _ensure_payload_page_matches_path(
        annotation_json=annotation_json,
        page_public_id=page_public_id,
    )

    build_result = build_revision_indexes(
        annotation_json=annotation_json,
        page_width=int(page_context["width"]),
        page_height=int(page_context["height"]),
    )
    latest_revision = repo.get_latest_revision(db, page_public_id=page_public_id)
    _ensure_base_revision_matches_latest(
        latest_revision=latest_revision,
        base_revision_id=base_revision_id,
    )
    latest_annotation_json = _read_latest_annotation_json(
        db=db,
        latest_revision=latest_revision,
        repository=repo,
        storage=json_storage,
    )
    latest_revision_no = repo.get_latest_revision_no(
        db, page_id=int(page_context["page_id"])
    )
    revision_no = latest_revision_no + 1
    revision_public_id = new_public_id("rev")
    revision_json = _with_revision_history(
        annotation_json=build_result.annotation_json,
        page_context=page_context,
        revision_public_id=revision_public_id,
        revision_no=revision_no,
        latest_revision=latest_revision,
        latest_annotation_json=latest_annotation_json,
        created_by=created_by,
        change_summary=change_summary,
        change_reason=change_reason,
    )
    stored_asset: StoredJsonAsset | None = None
    try:
        stored_asset = json_storage.write_revision_json(
            revision_public_id=revision_public_id,
            annotation_json=revision_json,
        )
        revision = repo.create_revision(
            db,
            public_id=revision_public_id,
            project_id=int(page_context["project_id"]),
            document_id=int(page_context["document_id"]),
            page_id=int(page_context["page_id"]),
            revision_no=revision_no,
            parent_revision_id=getattr(latest_revision, "id", None),
            annotation_json_asset=stored_asset,
            created_by=created_by,
            change_summary=change_summary,
            change_reason=change_reason,
        )
        repo.rebuild_indexes(
            db,
            revision_public_id=revision.public_id,
            annotation_objects=build_result.annotation_objects,
            relation_objects=build_result.relation_objects,
        )
        if hasattr(db, "commit"):
            db.commit()
        return revision
    except IntegrityError as exc:
        logger.debug("IntegrityError: %s", exc, exc_info=True)
        if hasattr(db, "rollback"):
            db.rollback()
        if stored_asset is not None and hasattr(json_storage, "remove_revision_json"):
            json_storage.remove_revision_json(stored_asset.storage_path)
        raise RevisionConflictError(
            "标注版本已被其他请求更新，请重新加载后再保存。"
        ) from exc
    except Exception:
        logger.debug("Unexpected exception", exc_info=True)
        if hasattr(db, "rollback"):
            db.rollback()
        if stored_asset is not None and hasattr(json_storage, "remove_revision_json"):
            json_storage.remove_revision_json(stored_asset.storage_path)
        raise


def _with_revision_history(
    *,
    annotation_json: dict[str, Any],
    page_context: dict[str, Any],
    revision_public_id: str,
    revision_no: int,
    latest_revision: Any | None,
    latest_annotation_json: dict[str, Any] | None,
    created_by: int,
    change_summary: str | None,
    change_reason: str | None,
) -> dict[str, Any]:
    revision_json = deepcopy(annotation_json)
    revision_json["page_id"] = page_context["page_public_id"]
    revision_json.setdefault("document_id", page_context.get("document_public_id"))
    revision_json.setdefault("project_id", str(page_context.get("project_id")))
    revision_json.setdefault("image", {})
    if isinstance(revision_json["image"], dict):
        revision_json["image"].setdefault("width", page_context["width"])
        revision_json["image"].setdefault("height", page_context["height"])
        revision_json["image"].setdefault(
            "asset_id", page_context.get("image_asset_public_id")
        )
        revision_json["image"].setdefault("sha256", page_context.get("image_sha256"))

    history = _read_history_from_annotation_json(latest_annotation_json)
    history.append(
        {
            "revision_id": revision_public_id,
            "revision_no": revision_no,
            "parent_revision_id": getattr(latest_revision, "public_id", None),
            "created_by": created_by,
            "created_at": datetime.now(UTC).isoformat(),
            "change_summary": change_summary,
            "change_reason": change_reason,
        }
    )
    revision_json["history"] = history
    return revision_json


def _read_latest_annotation_json(
    *,
    db: Session,
    latest_revision: Any | None,
    repository: AnnotationRepositoryProtocol,
    storage: AnnotationJsonStorageProtocol,
) -> dict[str, Any] | None:
    if latest_revision is None:
        return None

    latest_asset = repository.get_revision_asset(db, revision=latest_revision)
    if latest_asset is None:
        raise AnnotationRevisionNotFoundError("当前 latest revision JSON 资产不存在。")
    return storage.read_revision_json(latest_asset.storage_path)


def _read_history_from_annotation_json(
    annotation_json: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if annotation_json is None:
        return []

    raw_history = annotation_json.get("history")
    if not isinstance(raw_history, list):
        return []
    return deepcopy([item for item in raw_history if isinstance(item, dict)])


def _ensure_payload_page_matches_path(
    *,
    annotation_json: dict[str, Any],
    page_public_id: str,
) -> None:
    payload_page_id = annotation_json.get("page_id")
    if payload_page_id is None:
        return
    if not isinstance(payload_page_id, str) or payload_page_id.strip() == "":
        raise InvalidAnnotationError("annotation_json.page_id 必须是非空字符串。")
    if payload_page_id != page_public_id:
        raise InvalidAnnotationError("annotation_json.page_id 与 API page_id 不一致。")


def _ensure_base_revision_matches_latest(
    *,
    latest_revision: Any | None,
    base_revision_id: str | None,
) -> None:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"[DEBUG] _ensure_base_revision_matches_latest: latest_revision={latest_revision}, base_revision_id={base_revision_id}")

    if latest_revision is None:
        if base_revision_id is not None:
            raise RevisionConflictError("页面当前没有 revision，不能基于历史版本保存。")
        return
    latest_public_id = getattr(latest_revision, "public_id", None)
    logger.warning(f"[DEBUG] latest_public_id={latest_public_id}, base_revision_id={base_revision_id}, match={base_revision_id == latest_public_id}")
    if base_revision_id is None:
        raise RevisionConflictError("保存已有标注页时必须提交 base_revision_id。")
    if base_revision_id != latest_public_id:
        raise RevisionConflictError(
            "base_revision_id 不是当前 latest，请重新加载后再保存。"
        )


def _require_list(value: dict[str, Any], field: str) -> list[Any]:
    if field not in value:
        raise InvalidAnnotationError(f"{field} 必须存在并且是数组。")
    items = value[field]
    if not isinstance(items, list):
        raise InvalidAnnotationError(f"{field} 必须是数组。")
    return items


def _require_text(value: dict[str, Any], key: str, field: str) -> str:
    raw = value.get(key)
    if not isinstance(raw, str) or raw.strip() == "":
        raise InvalidAnnotationError(f"{field} 必须是非空字符串。")
    return raw


def _optional_mapping(
    value: dict[str, Any],
    *,
    key: str,
    default: dict[str, Any],
    message: str,
) -> dict[str, Any]:
    if key not in value or value[key] is None:
        return default
    raw = value[key]
    if not isinstance(raw, dict):
        raise InvalidAnnotationError(message)
    return raw


def _optional_container(
    value: dict[str, Any],
    *,
    key: str,
    default: list[Any] | dict[str, Any],
    message: str,
) -> list[Any] | dict[str, Any]:
    if key not in value or value[key] is None:
        return default
    raw = value[key]
    if not isinstance(raw, (list, dict)):
        raise InvalidAnnotationError(message)
    return raw


def _read_label_name(annotation: dict[str, Any], index: int) -> str:
    raw = annotation.get("type") or annotation.get("label_name")
    if not isinstance(raw, str) or raw.strip() == "":
        raise InvalidAnnotationError(f"k12_annotations[{index}] 缺少标签名称。")
    return raw


def _require_geometry(annotation: dict[str, Any], index: int) -> dict[str, Any]:
    geometry = annotation.get("geometry")
    if not isinstance(geometry, dict):
        raise InvalidAnnotationError(f"k12_annotations[{index}].geometry 必须是对象。")
    return geometry


def _normalize_bbox(
    value: Any,
    *,
    page_width: int,
    page_height: int,
    field: str,
) -> list[int | float] | None:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != 4:
        raise InvalidAnnotationError(f"{field} bbox 必须是四元数组。")
    if not all(isinstance(item, Real) and not isinstance(item, bool) for item in value):
        raise InvalidAnnotationError(f"{field} bbox 坐标必须是数字。")
    xmin, ymin, xmax, ymax = value
    if xmin < 0 or ymin < 0 or xmax > page_width or ymax > page_height:
        raise InvalidAnnotationError(f"{field} bbox 超出页面范围。")
    if xmin >= xmax or ymin >= ymax:
        raise InvalidAnnotationError(
            f"{field} bbox 必须满足 xmin < xmax 且 ymin < ymax。"
        )
    return [xmin, ymin, xmax, ymax]


def _bbox_to_polygon(bbox: list[int | float]) -> list[list[int | float]]:
    xmin, ymin, xmax, ymax = bbox
    return [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]]


def _normalize_polygon_like(
    value: Any,
    *,
    expected_points: int | None,
    field: str,
    page_width: int,
    page_height: int,
) -> list[list[int | float]] | None:
    if value is None:
        return None
    min_points = expected_points or 3
    if not isinstance(value, list) or len(value) < min_points:
        raise InvalidAnnotationError(f"{field} 点数量不足。")
    if expected_points is not None and len(value) != expected_points:
        raise InvalidAnnotationError(f"{field} 必须包含 {expected_points} 个点。")
    normalized: list[list[int | float]] = []
    for point in value:
        if not isinstance(point, list) or len(point) != 2:
            raise InvalidAnnotationError(f"{field} 每个点必须是 [x, y]。")
        x, y = point
        if (
            not isinstance(x, Real)
            or isinstance(x, bool)
            or not isinstance(y, Real)
            or isinstance(y, bool)
        ):
            raise InvalidAnnotationError(f"{field} 坐标必须是数字。")
        if x < 0 or y < 0 or x > page_width or y > page_height:
            raise InvalidAnnotationError(f"{field} 超出页面范围。")
        normalized.append([x, y])
    return normalized


def _normalize_read_order(value: Any, index: int) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidAnnotationError(
            f"k12_annotations[{index}].read_order 必须是正整数。"
        )
    return value


def _build_relation_indexes(
    relations: list[Any],
    ann_ids: set[str],
) -> list[dict[str, Any]]:
    relation_objects: list[dict[str, Any]] = []
    seen_rel_ids: set[str] = set()
    for index, relation in enumerate(relations):
        if not isinstance(relation, dict):
            raise InvalidAnnotationError(f"relations[{index}] 必须是对象。")
        rel_id = _read_relation_text(relation, ("id", "rel_id"), index, "id")
        if rel_id in seen_rel_ids:
            raise InvalidAnnotationError(f"关系 id 重复：{rel_id}")
        seen_rel_ids.add(rel_id)
        relation_type = _read_relation_text(
            relation, ("type", "relation_type"), index, "type"
        )
        from_ann_id = _read_relation_text(
            relation, ("from_id", "from_ann_id"), index, "from_id"
        )
        to_ann_id = _read_relation_text(
            relation, ("to_id", "to_ann_id"), index, "to_id"
        )
        if from_ann_id not in ann_ids or to_ann_id not in ann_ids:
            raise InvalidAnnotationError("关系引用的标注对象不存在。")
        if from_ann_id == to_ann_id:
            raise InvalidAnnotationError("关系起点和终点不能是同一个标注对象。")
        attributes = _optional_mapping(
            relation,
            key="attributes",
            default={},
            message="关系 attributes 必须是对象。",
        )
        status = relation.get("status") or "active"
        if status not in {"active", "deleted"}:
            raise InvalidAnnotationError("关系 status 只能是 active / deleted。")
        relation_objects.append(
            {
                "rel_id": rel_id,
                "relation_type": relation_type,
                "from_ann_id": from_ann_id,
                "to_ann_id": to_ann_id,
                "attributes_json": attributes,
                "status": status,
            }
        )
    return relation_objects


def _read_relation_text(
    relation: dict[str, Any],
    keys: tuple[str, ...],
    index: int,
    display_key: str,
) -> str:
    for key in keys:
        raw = relation.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw
    raise InvalidAnnotationError(f"relations[{index}].{display_key} 必须是非空字符串。")
