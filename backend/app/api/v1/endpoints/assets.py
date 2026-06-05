from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import ensure_project_capability, get_current_user
from app.db.models import User
from app.db.session import get_db_session
from app.schemas.asset import AssetUploadData, AssetUploadResponse
from app.services.asset_service import (
    AssetImportError,
    ProjectNotFoundError,
    UserNotFoundError,
    import_uploaded_image,
)
from app.storage.local import StorageError, UnsupportedUploadError, UploadTooLargeError
from app.utils.ids import new_public_id

router = APIRouter(tags=["assets"])


# 标准的项目级上传入口。认证由 Bearer token 处理，service 层只接收已经解析
# 出来的用户 id，用于 created_by 和审计归属。
@router.post(
    "/projects/{project_id}/assets/upload",
    response_model=AssetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="上传图片资产",
)
def upload_project_asset(
    project_id: int,
    file: UploadFile = File(..., description="待导入的单页图片文件。"),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> AssetUploadResponse:
    return _upload_image(project_id=project_id, file=file, db=db, actor_id=current_user.id)


# M3 保留了简化上传路径；这里作为历史兼容入口保留，但仍使用同一套 JWT
# 认证和项目能力校验。
@router.post(
    "/assets/upload",
    response_model=AssetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="上传图片资产（M3 兼容入口）",
)
def upload_asset(
    project_id: int = Form(..., description="项目内部主键，兼容 M3 简化上传入口。"),
    file: UploadFile = File(..., description="待导入的单页图片文件。"),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> AssetUploadResponse:
    return _upload_image(project_id=project_id, file=file, db=db, actor_id=current_user.id)


def _upload_image(
    *, project_id: int, file: UploadFile, db: Session, actor_id: int
) -> AssetUploadResponse:
    try:
        # 兼容入口的 project_id 来自 form 表单，不能直接套用只读取路径参数的
        # 依赖，因此在共享 helper 内显式执行项目能力判定。
        ensure_project_capability(
            db,
            user_id=actor_id,
            project_id=project_id,
            capability="can_upload_assets",
        )
        result = import_uploaded_image(
            db,
            project_id=project_id,
            fileobj=file.file,
            original_filename=file.filename,
            content_type=file.content_type,
            created_by=actor_id,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except UploadTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except (UnsupportedUploadError, StorageError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except AssetImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return AssetUploadResponse(
        data=AssetUploadData(
            asset_id=result.asset.public_id,
            document_id=result.document.public_id,
            page_id=result.page.public_id,
            sha256=result.asset.sha256,
            size_bytes=result.asset.size_bytes,
            mime_type=result.asset.mime_type or "",
            width=result.page.width,
            height=result.page.height,
            asset_reused=result.asset_reused,
        ),
        request_id=new_public_id("req"),
    )
