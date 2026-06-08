from __future__ import annotations

import hashlib
import mimetypes
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO
from uuid import uuid4

from PIL import Image, UnidentifiedImageError


# 上传策略以 Pillow 校验出的真实图片格式为准；客户端提供的文件名和 MIME
# 只有在与实际内容匹配时才被接受。
IMAGE_FORMATS: dict[str, dict[str, object]] = {
    "JPEG": {
        "mime_type": "image/jpeg",
        "extensions": {".jpg", ".jpeg"},
        "content_types": {"image/jpeg", "image/pjpeg"},
    },
    "PNG": {
        "mime_type": "image/png",
        "extensions": {".png"},
        "content_types": {"image/png"},
    },
    "WEBP": {
        "mime_type": "image/webp",
        "extensions": {".webp"},
        "content_types": {"image/webp"},
    },
    "TIFF": {
        "mime_type": "image/tiff",
        "extensions": {".tif", ".tiff"},
        "content_types": {"image/tiff"},
    },
    "BMP": {
        "mime_type": "image/bmp",
        "extensions": {".bmp"},
        "content_types": {"image/bmp"},
    },
}

# 一些客户端上传 multipart 时只会发送通用二进制 MIME；这里允许它们，是因为
# 写入 raw 前会用 Pillow 对真实字节内容做校验。
GENERIC_BINARY_CONTENT_TYPES = {"", "application/octet-stream"}
CHUNK_SIZE = 1024 * 1024


class StorageError(ValueError):
    """文件存储错误，message 面向 API 错误文案。"""


class UploadTooLargeError(StorageError):
    """上传文件超过配置限制。"""


class UnsupportedUploadError(StorageError):
    """上传文件类型不受支持或内容校验失败。"""


@dataclass(frozen=True)
class StagedUpload:
    temp_path: Path
    original_filename: str | None
    extension: str
    mime_type: str
    size_bytes: int
    sha256: str
    width: int
    height: int

    def discard(self) -> None:
        self.temp_path.unlink(missing_ok=True)


def stage_upload_file(
    *,
    fileobj: BinaryIO,
    original_filename: str | None,
    declared_content_type: str | None,
    storage_root: Path,
    max_upload_mb: int,
) -> StagedUpload:
    """把上传内容写入受控临时目录，并完成大小、hash、MIME 和图像尺寸校验。"""

    root = _resolve_storage_root(storage_root)
    # 临时文件必须留在 STORAGE_ROOT 内，后续清理和路径校验才能与已提交的 raw
    # 资产使用同一个文件系统边界。
    temp_dir = root / "tmp" / "uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"upload_{uuid4().hex}.tmp"
    safe_filename = _safe_original_filename(original_filename)
    max_upload_bytes = max_upload_mb * 1024 * 1024

    try:
        sha256 = hashlib.sha256()
        size_bytes = 0
        with temp_path.open("wb") as output:
            while True:
                # 分块流式读取可以在不把整文件加载进内存的情况下，同时控制大小
                # 上限并计算 sha256。
                chunk = fileobj.read(CHUNK_SIZE)
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > max_upload_bytes:
                    raise UploadTooLargeError(f"上传文件超过 {max_upload_mb} MB 限制。")
                sha256.update(chunk)
                output.write(chunk)

        if size_bytes == 0:
            raise UnsupportedUploadError("上传文件为空。")

        return _inspect_staged_image(
            temp_path=temp_path,
            original_filename=safe_filename,
            declared_content_type=declared_content_type,
            size_bytes=size_bytes,
            sha256=sha256.hexdigest(),
        )
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def commit_staged_raw_asset(
    *,
    staged: StagedUpload,
    storage_root: Path,
    asset_public_id: str,
) -> str:
    """把临时文件移动到 raw/assets，只允许创建新文件，不能覆盖已存在路径。"""

    root = _resolve_storage_root(storage_root)
    prefix = staged.sha256[:2]
    # 存储路径只由可信 public_id 和内容哈希生成；原始文件名只是元数据，
    # 不能参与决定 raw 文件路径。
    relative_path = (
        PurePosixPath("raw")
        / "assets"
        / prefix
        / (f"{asset_public_id}.original{staged.extension}")
    )
    target_path = _controlled_path(root, relative_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # raw 资产不可变；目标路径已存在时必须失败，不能覆盖可能已被数据库行
    # 引用的原始字节。
    if target_path.exists():
        raise StorageError("原始文件目标路径已存在，拒绝覆盖。")

    try:
        staged.temp_path.rename(target_path)
    except FileExistsError as exc:
        raise StorageError("原始文件目标路径已存在，拒绝覆盖。") from exc

    return relative_path.as_posix()


def remove_committed_raw_asset(*, storage_root: Path, storage_path: str) -> None:
    """删除本次事务创建但未能登记成功的 raw 文件。"""

    root = _resolve_storage_root(storage_root)
    # 补偿清理仍然走受控路径解析，避免回滚逻辑删除 STORAGE_ROOT 之外的文件。
    target_path = _controlled_path(root, PurePosixPath(storage_path))
    target_path.unlink(missing_ok=True)


def _inspect_staged_image(
    *,
    temp_path: Path,
    original_filename: str | None,
    declared_content_type: str | None,
    size_bytes: int,
    sha256: str,
) -> StagedUpload:
    extension = _extension_from_filename(original_filename)
    normalized_declared_type = _normalize_content_type(
        declared_content_type, original_filename
    )

    try:
        # 先信任解码后的图片字节；扩展名和声明 MIME 只在真实图片格式确定后
        # 作为兼容性校验。
        with Image.open(temp_path) as image:
            image_format = image.format
            width, height = image.size
            image.verify()
    except UnidentifiedImageError as exc:
        raise UnsupportedUploadError(
            "仅支持可识别的图片文件，PDF 渲染将在后续任务阶段接入。"
        ) from exc

    if image_format not in IMAGE_FORMATS:
        raise UnsupportedUploadError(f"暂不支持 {image_format or '未知'} 图片格式。")

    format_info = IMAGE_FORMATS[image_format]
    allowed_extensions = format_info["extensions"]
    allowed_content_types = format_info["content_types"]
    actual_mime_type = str(format_info["mime_type"])

    # 文件扩展名和 MIME 都必须与已校验的图片格式一致，防止伪装上传进入
    # raw 存储。
    if extension not in allowed_extensions:
        raise UnsupportedUploadError("上传文件扩展名与图片内容不匹配。")

    if (
        normalized_declared_type not in GENERIC_BINARY_CONTENT_TYPES
        and normalized_declared_type not in allowed_content_types
    ):
        raise UnsupportedUploadError("上传文件 MIME 类型与图片内容不匹配。")

    return StagedUpload(
        temp_path=temp_path,
        original_filename=original_filename,
        extension=extension,
        mime_type=actual_mime_type,
        size_bytes=size_bytes,
        sha256=sha256,
        width=width,
        height=height,
    )


def _resolve_storage_root(storage_root: Path) -> Path:
    root = storage_root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _controlled_path(root: Path, relative_path: PurePosixPath) -> Path:
    """解析仓库存储路径，并阻止路径穿越。"""

    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise StorageError("存储路径必须是 STORAGE_ROOT 内的安全相对路径。")

    target_path = (root / Path(*relative_path.parts)).resolve()
    try:
        target_path.relative_to(root)
    except ValueError as exc:
        raise StorageError("生成的存储路径超出 STORAGE_ROOT。") from exc
    return target_path


def _safe_original_filename(original_filename: str | None) -> str | None:
    if original_filename is None:
        return None
    # 只保留展示用文件名；用户输入是元数据，不能作为文件系统路径使用。
    filename = Path(original_filename.replace("\x00", "")).name.strip()
    return filename or None


def _extension_from_filename(original_filename: str | None) -> str:
    if not original_filename:
        raise UnsupportedUploadError("上传文件必须包含图片扩展名。")
    extension = Path(original_filename).suffix.lower()
    if not extension:
        raise UnsupportedUploadError("上传文件必须包含图片扩展名。")
    return extension


def _normalize_content_type(
    declared_content_type: str | None,
    original_filename: str | None,
) -> str:
    if declared_content_type:
        return declared_content_type.split(";", 1)[0].strip().lower()
    guessed_type, _encoding = mimetypes.guess_type(original_filename or "")
    return (guessed_type or "").lower()
