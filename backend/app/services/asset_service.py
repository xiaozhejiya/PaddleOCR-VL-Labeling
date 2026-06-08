from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Asset, Document, Page
from app.repositories import assets as asset_repository
from app.storage.local import (
    StorageError,
    StagedUpload,
    UnsupportedUploadError,
    UploadTooLargeError,
    commit_staged_raw_asset,
    remove_committed_raw_asset,
    stage_upload_file,
)
from app.utils.ids import new_public_id


class ProjectNotFoundError(ValueError):
    """项目不存在。"""


class UserNotFoundError(ValueError):
    """用户不存在、被禁用或已删除。"""


class AssetImportError(ValueError):
    """资产导入失败。"""


@dataclass(frozen=True)
class AssetImportResult:
    asset: Asset
    document: Document
    page: Page
    asset_reused: bool


def import_uploaded_image(
    db: Session,
    *,
    project_id: int,
    fileobj: BinaryIO,
    original_filename: str | None,
    content_type: str | None,
    created_by: int,
    storage_root: Path | None = None,
    max_upload_mb: int | None = None,
) -> AssetImportResult:
    """导入单页图片，生成 raw asset、document 和 page 记录。

    事务边界：本函数负责提交数据库事务。文件先写入临时目录并计算 sha256；
    若数据库中已存在同 sha256 资产，只丢弃临时文件并复用旧资产，避免覆盖 raw 文件。
    """

    settings = get_settings()
    resolved_storage_root = storage_root or settings.storage_root
    resolved_max_upload_mb = max_upload_mb or settings.max_upload_mb

    if asset_repository.get_project_by_id(db, project_id) is None:
        raise ProjectNotFoundError(f"项目不存在：{project_id}")
    if asset_repository.get_active_user_by_id(db, created_by) is None:
        raise UserNotFoundError(f"用户不可用：{created_by}")

    # raw 资产不可变：先在 tmp/ 下完成哈希和图片校验，再决定创建新文件还是
    # 复用已有 sha256 对应的标准文件。
    staged = stage_upload_file(
        fileobj=fileobj,
        original_filename=original_filename,
        declared_content_type=content_type,
        storage_root=resolved_storage_root,
        max_upload_mb=resolved_max_upload_mb,
    )

    # 只有临时文件被移动到 raw/assets 后才记录路径；后续数据库写入失败时，
    # 该值用于精确清理本次调用产生的文件副作用。
    storage_path: str | None = None
    try:
        # 幂等边界：sha256 唯一键代表不可变 raw 文件；但每次上传请求仍然
        # 需要生成独立的 document/page，便于审计和后续标注。
        asset = asset_repository.get_asset_by_sha256(db, staged.sha256)
        asset_reused = asset is not None
        if asset is None:
            asset_public_id = new_public_id("asset")
            # 先移动文件再插入 asset 行，避免数据库提交后指向一个实际不存在
            # 的 raw 文件。
            storage_path = commit_staged_raw_asset(
                staged=staged,
                storage_root=resolved_storage_root,
                asset_public_id=asset_public_id,
            )
            asset = asset_repository.create_asset(
                db,
                public_id=asset_public_id,
                asset_type="page_image",
                storage_path=storage_path,
                original_filename=staged.original_filename,
                mime_type=staged.mime_type,
                size_bytes=staged.size_bytes,
                sha256=staged.sha256,
                width=staged.width,
                height=staged.height,
                created_by=created_by,
            )
        else:
            # sha256 已存在表示本次临时文件与已有不可变 raw 资产重复，只删除
            # 临时副本，不能覆盖 raw 存储。
            staged.discard()

        # 导入记录按请求生成。asset 可以复用，但调用方仍会拿到本次上传对应的
        # 新 document/page。
        result = _create_document_page_and_audit(
            db,
            project_id=project_id,
            asset=asset,
            staged=staged,
            created_by=created_by,
            asset_reused=asset_reused,
        )
        db.commit()
        return result
    except IntegrityError as exc:
        # 并发重复上传场景：另一个事务可能在本事务读取后、插入前写入相同
        # sha256。这里回滚本事务行，清理本次文件副作用，再复用唯一约束赢家。
        db.rollback()
        _discard_staged_or_committed(
            staged=staged,
            storage_root=resolved_storage_root,
            storage_path=storage_path,
        )
        existing_asset = asset_repository.get_asset_by_sha256(db, staged.sha256)
        if existing_asset is None:
            raise AssetImportError("文件资产导入失败。") from exc

        try:
            result = _create_document_page_and_audit(
                db,
                project_id=project_id,
                asset=existing_asset,
                staged=staged,
                created_by=created_by,
                asset_reused=True,
            )
            db.commit()
            return result
        except Exception as reuse_exc:
            db.rollback()
            raise AssetImportError("文件资产导入失败。") from reuse_exc
    except Exception as exc:
        # SQL 回滚无法撤销文件系统写入；抛出校验/存储错误或包装未知异常前，
        # 先清理本次调用拥有的临时文件或 raw 文件。
        db.rollback()
        _discard_staged_or_committed(
            staged=staged,
            storage_root=resolved_storage_root,
            storage_path=storage_path,
        )
        if isinstance(exc, (StorageError, UnsupportedUploadError, UploadTooLargeError)):
            raise
        raise AssetImportError("文件资产导入失败。") from exc


def _create_document_page_and_audit(
    db: Session,
    *,
    project_id: int,
    asset: Asset,
    staged: StagedUpload,
    created_by: int,
    asset_reused: bool,
) -> AssetImportResult:
    """在不可变 asset 已确定后，创建本次上传专属的数据库记录。"""

    document = asset_repository.create_document_for_upload(
        db,
        public_id=new_public_id("doc"),
        project_id=project_id,
        source_asset_public_id=asset.public_id,
        original_filename=staged.original_filename,
    )
    page = asset_repository.create_page_for_upload(
        db,
        public_id=new_public_id("page"),
        document_id=document.id,
        image_asset_id=asset.id,
        width=staged.width,
        height=staged.height,
    )
    asset_repository.write_upload_audit_log(
        db,
        project_id=project_id,
        actor_id=created_by,
        asset=asset,
        document=document,
        page=page,
        asset_reused=asset_reused,
    )
    return AssetImportResult(
        asset=asset,
        document=document,
        page=page,
        asset_reused=asset_reused,
    )


def _discard_staged_or_committed(
    *,
    staged: StagedUpload,
    storage_root: Path,
    storage_path: str | None,
) -> None:
    """只移除失败调用自己产生的文件系统副作用。"""

    if storage_path is None:
        staged.discard()
        return
    remove_committed_raw_asset(storage_root=storage_root, storage_path=storage_path)
