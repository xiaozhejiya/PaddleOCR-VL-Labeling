"""项目角色 repository 测试。

覆盖事项：
1. 系统级角色、停用角色和不存在的项目成员不能绑定到项目成员。
2. 角色授予必须带审计操作者。
3. 成功授予项目角色时必须同步写入 audit_logs 所需字段。
"""

import pytest

from app.db.models import AuditLog, MemberRoleBinding, ProjectMember, RoleRegistry
from app.repositories import roles


class RejectingSession:
    def add(self, _value: object) -> None:
        raise AssertionError("system roles must not be added as project bindings")


def test_bind_project_role_rejects_system_role(monkeypatch: pytest.MonkeyPatch) -> None:
    system_role = RoleRegistry(
        id=1,
        code="system_admin",
        scope="system",
        is_active=True,
    )
    monkeypatch.setattr(roles, "get_role_by_code", lambda _db, _code: system_role)

    with pytest.raises(ValueError, match="not project-scoped"):
        roles.bind_project_role(
            RejectingSession(),  # type: ignore[arg-type]
            project_member_id=1,
            role_code="system_admin",
            granted_by=99,
        )


def test_bind_project_role_requires_audit_actor() -> None:
    with pytest.raises(ValueError, match="granted_by"):
        roles.bind_project_role(  # type: ignore[arg-type]
            RejectingSession(),  # type: ignore[arg-type]
            project_member_id=1,
            role_code="viewer",
            granted_by=None,
        )


def test_bind_project_role_rejects_inactive_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inactive_role = RoleRegistry(
        id=2,
        code="viewer",
        scope="project",
        is_active=False,
    )
    monkeypatch.setattr(roles, "get_role_by_code", lambda _db, _code: inactive_role)

    with pytest.raises(ValueError, match="not available"):
        roles.bind_project_role(
            RejectingSession(),  # type: ignore[arg-type]
            project_member_id=1,
            role_code="viewer",
            granted_by=99,
        )


class MissingMemberSession:
    def get(self, _model: type[object], _identity: int) -> object | None:
        return None

    def add(self, _value: object) -> None:
        raise AssertionError("成员不存在时不能写入角色绑定")


def test_bind_project_role_rejects_missing_project_member(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_role = RoleRegistry(
        id=7,
        code="viewer",
        scope="project",
        is_active=True,
    )
    monkeypatch.setattr(roles, "get_role_by_code", lambda _db, _code: project_role)

    with pytest.raises(ValueError, match="Project member is not available"):
        roles.bind_project_role(
            MissingMemberSession(),  # type: ignore[arg-type]
            project_member_id=404,
            role_code="viewer",
            granted_by=99,
        )


class RecordingSession:
    def __init__(self, project_member: ProjectMember) -> None:
        self.project_member = project_member
        self.added: list[object] = []

    def get(self, model: type[object], identity: int) -> object | None:
        if model is ProjectMember and identity == self.project_member.id:
            return self.project_member
        return None

    def add(self, value: object) -> None:
        self.added.append(value)

    def flush(self) -> None:
        for value in self.added:
            if isinstance(value, MemberRoleBinding):
                value.id = 88


def test_bind_project_role_writes_audit_log(monkeypatch: pytest.MonkeyPatch) -> None:
    project_role = RoleRegistry(
        id=7,
        code="viewer",
        scope="project",
        is_active=True,
    )
    project_member = ProjectMember(
        id=1,
        project_id=123,
        user_id=456,
    )
    session = RecordingSession(project_member)
    monkeypatch.setattr(roles, "get_role_by_code", lambda _db, _code: project_role)

    binding = roles.bind_project_role(  # type: ignore[arg-type]
        session,
        project_member_id=1,
        role_code="viewer",
        granted_by=99,
    )

    assert binding.id == 88
    assert isinstance(session.added[0], MemberRoleBinding)
    assert isinstance(session.added[1], AuditLog)
    audit_log = session.added[1]
    assert audit_log.project_id == 123
    assert audit_log.actor_id == 99
    assert audit_log.action == "role.grant"
    assert audit_log.resource_type == "member_role_binding"
    assert audit_log.resource_id == "88"
    assert audit_log.after_json == {
        "project_member_id": 1,
        "user_id": 456,
        "role_id": 7,
        "role_code": "viewer",
        "role_scope": "project",
        "status": "active",
        "granted_by": 99,
    }
