from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    ensure_project_capability,
    get_current_user,
    get_project_capabilities,
)
from app.db.models import (
    LabelRegistry,
    MemberRoleBinding,
    ProjectMember,
    RoleRegistry,
    User,
)
from app.db.models.project import Project
from app.db.session import get_db_session
from app.schemas.page import PageListOut
from app.schemas.project import (
    ProjectCreate,
    ProjectLabelListOut,
    ProjectLabelOut,
    ProjectListOut,
    ProjectOut,
    ProjectUpdate,
)

router = APIRouter(prefix="/projects", tags=["projects"])

PROJECT_CAPABILITIES: tuple[str, ...] = (
    "can_view_project",
    "can_create_annotation_revision",
    "can_submit_revision",
    "can_review_revision",
    "can_create_export_job",
    "can_download_export",
    "can_manage_project_members",
    "can_manage_labels",
    "can_manage_relations",
    "can_lock_revision",
    "can_unlock_revision",
    "can_rollback_revision",
    "can_upload_assets",
    "can_import_pages",
    "can_view_audit_log",
)

SYSTEM_CAPABILITIES: tuple[str, ...] = ("can_manage_system_users",)


@dataclass(frozen=True)
class _BuiltinWorkspaceLabel:
    namespace: str
    name: str
    display_name: str
    display_name_i18n: dict[str, str]
    default_color: str


_FALLBACK_WORKSPACE_LABELS: tuple[_BuiltinWorkspaceLabel, ...] = (
    _BuiltinWorkspaceLabel(
        namespace="k12",
        name="question_block",
        display_name="Question",
        display_name_i18n={"zh-CN": "题目", "en-US": "Question"},
        default_color="#5e6ad2",
    ),
    _BuiltinWorkspaceLabel(
        namespace="k12",
        name="answer_area",
        display_name="Answer Area",
        display_name_i18n={"zh-CN": "答案区域", "en-US": "Answer Area"},
        default_color="#24a148",
    ),
    _BuiltinWorkspaceLabel(
        namespace="k12",
        name="option_block",
        display_name="Option Area",
        display_name_i18n={"zh-CN": "选项区域", "en-US": "Option Area"},
        default_color="#0f62fe",
    ),
    _BuiltinWorkspaceLabel(
        namespace="k12",
        name="option_image",
        display_name="Image Area",
        display_name_i18n={"zh-CN": "图像区域", "en-US": "Image Area"},
        default_color="#da1e28",
    ),
    _BuiltinWorkspaceLabel(
        namespace="k12",
        name="formula",
        display_name="Formula",
        display_name_i18n={"zh-CN": "公式", "en-US": "Formula"},
        default_color="#dd5b00",
    ),
    _BuiltinWorkspaceLabel(
        namespace="k12",
        name="table",
        display_name="Table",
        display_name_i18n={"zh-CN": "表格", "en-US": "Table"},
        default_color="#0f62fe",
    ),
    _BuiltinWorkspaceLabel(
        namespace="k12",
        name="noise_or_erasure",
        display_name="Other",
        display_name_i18n={"zh-CN": "其他", "en-US": "Other"},
        default_color="#8c8c8c",
    ),
)


@router.get("", response_model=ProjectListOut, summary="获取项目列表")
def list_projects(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectListOut:
    visible_project_ids = _get_visible_project_ids(db, user_id=current_user.id)
    if not visible_project_ids:
        return ProjectListOut(items=[], total=0)

    projects = db.scalars(
        select(Project)
        .where(Project.id.in_(visible_project_ids))
        .order_by(Project.created_at.desc())
    ).all()
    return ProjectListOut(
        items=[ProjectOut.model_validate(p) for p in projects],
        total=len(projects),
    )


@router.post(
    "",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建项目",
)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectOut:
    project = Project(
        name=payload.name,
        description=payload.description,
        created_by=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


@router.get("/{project_id}", response_model=ProjectOut, summary="获取项目详情")
def get_project(
    project_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectOut:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=project_id,
        capability="can_view_project",
    )
    return ProjectOut.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectOut, summary="更新项目")
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectOut:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
    summary="删除项目",
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> None:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    db.delete(project)
    db.commit()


@router.get(
    "/{project_id}/pages", response_model=PageListOut, summary="获取项目页面列表"
)
def list_project_pages(
    project_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> PageListOut:
    from app.api.v1.endpoints.pages import list_project_pages as _list

    return _list(project_id, db, current_user)


@router.get(
    "/{project_id}/labels",
    response_model=ProjectLabelListOut,
    summary="获取项目标签注册表",
)
def list_project_labels(
    project_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectLabelListOut:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=project_id,
        capability="can_view_project",
    )

    rows = db.scalars(
        select(LabelRegistry)
        .where(
            LabelRegistry.is_active.is_(True),
            (LabelRegistry.project_id == project_id)
            | LabelRegistry.project_id.is_(None),
        )
        .order_by(
            LabelRegistry.namespace.asc(),
            LabelRegistry.name.asc(),
            LabelRegistry.project_id.asc(),
        )
    ).all()

    if not rows:
        fallback_items = [
            ProjectLabelOut(
                id=None,
                project_id=None,
                namespace=item.namespace,
                name=item.name,
                display_name=item.display_name,
                display_name_i18n=item.display_name_i18n,
                geometry_types=["bbox_xyxy", "quad", "polygon"],
                attributes_schema={},
                default_color=item.default_color,
                is_builtin=True,
                is_active=True,
            )
            for item in _FALLBACK_WORKSPACE_LABELS
        ]
        return ProjectLabelListOut(items=fallback_items, total=len(fallback_items))

    deduplicated: dict[tuple[str, str], ProjectLabelOut] = {}
    for row in rows:
        deduplicated[(row.namespace, row.name)] = _label_to_out(row)

    items = list(deduplicated.values())
    return ProjectLabelListOut(items=items, total=len(items))


@router.get("/{project_id}/me/capabilities", summary="获取当前用户在项目中的能力")
def get_my_capabilities(
    project_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if project.created_by == current_user.id:
        capabilities = set(PROJECT_CAPABILITIES)
    else:
        capabilities = get_project_capabilities(
            db,
            user_id=current_user.id,
            project_id=project_id,
        )

    if current_user.is_system_admin:
        capabilities.update(SYSTEM_CAPABILITIES)

    all_caps = (*PROJECT_CAPABILITIES, *SYSTEM_CAPABILITIES)
    return {capability: capability in capabilities for capability in all_caps}


def _label_to_out(label: LabelRegistry) -> ProjectLabelOut:
    return ProjectLabelOut(
        id=label.id,
        project_id=label.project_id,
        namespace=label.namespace,
        name=label.name,
        display_name=label.display_name,
        display_name_i18n=_FALLBACK_LABEL_I18N.get((label.namespace, label.name)),
        geometry_types=[
            item for item in label.geometry_types_json if isinstance(item, str)
        ],
        attributes_schema=label.attributes_schema_json,
        default_color=label.default_color,
        is_builtin=label.is_builtin,
        is_active=label.is_active,
    )


_FALLBACK_LABEL_I18N: dict[tuple[str, str], dict[str, str]] = {
    (item.namespace, item.name): item.display_name_i18n
    for item in _FALLBACK_WORKSPACE_LABELS
}


def _get_visible_project_ids(db: Session, *, user_id: int) -> set[int]:
    visible_project_ids = set(
        db.scalars(select(Project.id).where(Project.created_by == user_id)).all()
    )

    stmt = (
        select(ProjectMember.project_id, RoleRegistry.permissions_json)
        .join(
            MemberRoleBinding, MemberRoleBinding.project_member_id == ProjectMember.id
        )
        .join(RoleRegistry, RoleRegistry.id == MemberRoleBinding.role_id)
        .where(
            ProjectMember.user_id == user_id,
            ProjectMember.member_status == "active",
            MemberRoleBinding.status == "active",
            RoleRegistry.scope == "project",
            RoleRegistry.is_active.is_(True),
        )
    )
    for project_id, permissions_json in db.execute(stmt).all():
        capability_items = permissions_json.get("capabilities", [])
        if (
            isinstance(project_id, int)
            and isinstance(capability_items, list)
            and "can_view_project" in capability_items
        ):
            visible_project_ids.add(project_id)
    return visible_project_ids
