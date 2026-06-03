from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditLog, MemberRoleBinding, ProjectMember, RoleRegistry


def list_builtin_roles(db: Session) -> list[RoleRegistry]:
    stmt = (
        select(RoleRegistry)
        .where(RoleRegistry.is_builtin.is_(True))
        .order_by(RoleRegistry.scope, RoleRegistry.code)
    )
    return list(db.scalars(stmt))


def get_role_by_code(db: Session, code: str) -> RoleRegistry | None:
    stmt = select(RoleRegistry).where(RoleRegistry.code == code)
    return db.scalar(stmt)


def bind_project_role(
    db: Session,
    *,
    project_member_id: int,
    role_code: str,
    granted_by: int,
) -> MemberRoleBinding:
    if granted_by is None:
        raise ValueError("granted_by is required for audited role grants")

    role = get_role_by_code(db, role_code)
    if role is None or not role.is_active:
        raise ValueError(f"Role is not available: {role_code}")
    if role.scope != "project":
        raise ValueError(f"Role is not project-scoped: {role_code}")

    project_member = db.get(ProjectMember, project_member_id)
    if project_member is None:
        raise ValueError(f"Project member is not available: {project_member_id}")

    binding = MemberRoleBinding(
        project_member_id=project_member_id,
        role_id=role.id,
        role_scope="project",
        granted_by=granted_by,
        status="active",
    )
    db.add(binding)
    db.flush()

    db.add(
        AuditLog(
            project_id=project_member.project_id,
            actor_id=granted_by,
            action="role.grant",
            resource_type="member_role_binding",
            resource_id=str(binding.id) if binding.id is not None else None,
            after_json={
                "project_member_id": project_member_id,
                "user_id": project_member.user_id,
                "role_id": role.id,
                "role_code": role.code,
                "role_scope": role.scope,
                "status": binding.status,
                "granted_by": granted_by,
            },
        )
    )
    return binding


def list_project_member_roles(
    db: Session,
    *,
    project_member_id: int,
) -> list[RoleRegistry]:
    stmt = (
        select(RoleRegistry)
        .join(MemberRoleBinding, MemberRoleBinding.role_id == RoleRegistry.id)
        .where(
            MemberRoleBinding.project_member_id == project_member_id,
            MemberRoleBinding.status == "active",
            RoleRegistry.scope == "project",
            RoleRegistry.is_active.is_(True),
        )
        .order_by(RoleRegistry.code)
    )
    return list(db.scalars(stmt))
