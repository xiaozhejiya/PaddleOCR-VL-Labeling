from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi import HTTPException, status

from app.api.v1.endpoints import projects as projects_endpoint


class DummyDb:
    def __init__(self, project: object | None):
        self._project = project

    def get(self, _model: object, _id: int):
        return self._project


class _ScalarResult:
    def __init__(self, items: list[object]):
        self._items = items

    def all(self) -> list[object]:
        return self._items


class DummyProjectListDb:
    def __init__(self, projects: list[object]):
        self._projects = projects

    def scalars(self, _stmt: object) -> _ScalarResult:
        return _ScalarResult(self._projects)


def test_get_my_capabilities_returns_404_for_missing_project() -> None:
    db = DummyDb(project=None)
    current_user = type("User", (), {"id": 1, "is_system_admin": False})()

    with pytest.raises(HTTPException) as exc_info:
        projects_endpoint.get_my_capabilities(
            project_id=1, db=db, current_user=current_user
        )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_my_capabilities_returns_all_project_caps_for_creator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = type("Project", (), {"created_by": 1})()
    db = DummyDb(project=project)
    current_user = type("User", (), {"id": 1, "is_system_admin": False})()

    monkeypatch.setattr(
        projects_endpoint, "get_project_capabilities", lambda *_args, **_kwargs: set()
    )

    result = projects_endpoint.get_my_capabilities(
        project_id=1, db=db, current_user=current_user
    )
    for cap in projects_endpoint.PROJECT_CAPABILITIES:
        assert result[cap] is True
    assert result["can_manage_system_users"] is False


def test_get_my_capabilities_returns_project_member_caps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = type("Project", (), {"created_by": 999})()
    db = DummyDb(project=project)
    current_user = type("User", (), {"id": 1, "is_system_admin": False})()

    monkeypatch.setattr(
        projects_endpoint,
        "get_project_capabilities",
        lambda *_args, **_kwargs: {
            "can_create_annotation_revision",
            "can_view_project",
        },
    )

    result = projects_endpoint.get_my_capabilities(
        project_id=1, db=db, current_user=current_user
    )
    assert result["can_view_project"] is True
    assert result["can_create_annotation_revision"] is True
    assert result["can_review_revision"] is False


def test_get_my_capabilities_includes_system_caps_for_system_admin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = type("Project", (), {"created_by": 999})()
    db = DummyDb(project=project)
    current_user = type("User", (), {"id": 1, "is_system_admin": True})()

    monkeypatch.setattr(
        projects_endpoint, "get_project_capabilities", lambda *_args, **_kwargs: set()
    )

    result = projects_endpoint.get_my_capabilities(
        project_id=1, db=db, current_user=current_user
    )
    assert result["can_manage_system_users"] is True


def test_list_projects_includes_member_visible_projects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(UTC)
    projects = [
        type(
            "Project",
            (),
            {
                "id": 1,
                "name": "项目 A",
                "description": None,
                "schema_version": "v1",
                "created_by": 99,
                "created_at": now,
                "updated_at": now,
            },
        )(),
        type(
            "Project",
            (),
            {
                "id": 2,
                "name": "项目 B",
                "description": None,
                "schema_version": "v1",
                "created_by": 100,
                "created_at": now,
                "updated_at": now,
            },
        )(),
    ]
    db = DummyProjectListDb(projects)
    current_user = type("User", (), {"id": 1})()

    monkeypatch.setattr(
        projects_endpoint,
        "_get_visible_project_ids",
        lambda *_args, **_kwargs: {1, 2},
    )

    result = projects_endpoint.list_projects(db=db, current_user=current_user)

    assert result.total == 2
    assert [item.id for item in result.items] == [1, 2]


def test_get_project_allows_member_with_can_view_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(UTC)
    project = type(
        "Project",
        (),
        {
            "id": 10,
            "name": "成员项目",
            "description": None,
            "schema_version": "v1",
            "created_by": 999,
            "created_at": now,
            "updated_at": now,
        },
    )()
    db = DummyDb(project=project)
    current_user = type("User", (), {"id": 1})()
    seen: list[tuple[int, int, str]] = []

    def fake_ensure(
        db_obj: object, *, user_id: int, project_id: int, capability: str
    ) -> None:
        seen.append((user_id, project_id, capability))

    monkeypatch.setattr(projects_endpoint, "ensure_project_capability", fake_ensure)

    result = projects_endpoint.get_project(
        project_id=10, db=db, current_user=current_user
    )

    assert result.id == 10
    assert seen == [(1, 10, "can_view_project")]
