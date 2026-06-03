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
