from __future__ import annotations

import pytest
from fastapi import HTTPException, status

from app.api.v1.endpoints import projects as projects_endpoint


class DummyScalarResult:
    def __init__(self, items: list[object]):
        self._items = items

    def all(self) -> list[object]:
        return self._items


class DummyDb:
    def __init__(self, project: object | None, labels: list[object] | None = None):
        self._project = project
        self._labels = labels or []

    def get(self, _model: object, _id: int):
        return self._project

    def scalars(self, _stmt: object) -> DummyScalarResult:
        return DummyScalarResult(self._labels)


def test_list_project_labels_returns_404_for_missing_project() -> None:
    db = DummyDb(project=None)
    current_user = type("User", (), {"id": 1, "is_system_admin": False})()

    with pytest.raises(HTTPException) as exc_info:
        projects_endpoint.list_project_labels(project_id=1, db=db, current_user=current_user)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


def test_list_project_labels_returns_fallback_workspace_labels_when_registry_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = type("Project", (), {"created_by": 1})()
    db = DummyDb(project=project, labels=[])
    current_user = type("User", (), {"id": 1, "is_system_admin": False})()

    monkeypatch.setattr(projects_endpoint, "ensure_project_capability", lambda *_args, **_kwargs: None)

    result = projects_endpoint.list_project_labels(project_id=1, db=db, current_user=current_user)

    assert result.total == 7
    assert result.items[0].namespace == "k12"
    assert result.items[0].name == "question_block"
    assert result.items[0].display_name_i18n == {"zh-CN": "题目", "en-US": "Question"}
    assert result.items[0].default_color == "#5e6ad2"


def test_list_project_labels_returns_database_labels(monkeypatch: pytest.MonkeyPatch) -> None:
    project = type("Project", (), {"created_by": 999})()
    label = type(
        "LabelRow",
        (),
        {
            "id": 12,
            "project_id": 1,
            "namespace": "k12",
            "name": "custom_block",
            "display_name": "Custom Block",
            "geometry_types_json": ["bbox_xyxy", "quad", 1],
            "attributes_schema_json": {"required": ["difficulty"]},
            "default_color": "#123456",
            "is_builtin": False,
            "is_active": True,
        },
    )()
    db = DummyDb(project=project, labels=[label])
    current_user = type("User", (), {"id": 2, "is_system_admin": False})()

    monkeypatch.setattr(projects_endpoint, "ensure_project_capability", lambda *_args, **_kwargs: None)

    result = projects_endpoint.list_project_labels(project_id=1, db=db, current_user=current_user)

    assert result.total == 1
    assert result.items[0].id == 12
    assert result.items[0].name == "custom_block"
    assert result.items[0].display_name == "Custom Block"
    assert result.items[0].display_name_i18n is None
    assert result.items[0].geometry_types == ["bbox_xyxy", "quad"]
    assert result.items[0].attributes_schema == {"required": ["difficulty"]}
    assert result.items[0].default_color == "#123456"
