"""本地文件存储测试。

覆盖事项：
1. 上传文件的 sha256、MIME、扩展名、尺寸和大小校验。
2. raw asset 只允许追加创建，拒绝覆盖既有原始文件。
3. 存储路径必须保持在 STORAGE_ROOT 内，拒绝路径穿越。
4. 校验失败时不留下临时文件。
"""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from app.storage.local import (
    StorageError,
    UnsupportedUploadError,
    commit_staged_raw_asset,
    remove_committed_raw_asset,
    stage_upload_file,
)


def png_bytes() -> bytes:
    image = Image.new("RGB", (12, 8), color=(255, 255, 255))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def stored_path(root: Path, relative_path: str) -> Path:
    return root / Path(*relative_path.split("/"))


def test_stage_and_commit_upload_calculates_hash_and_writes_raw_asset(
    tmp_path: Path,
) -> None:
    content = png_bytes()
    staged = stage_upload_file(
        fileobj=BytesIO(content),
        original_filename="../paper.png",
        declared_content_type="image/png",
        storage_root=tmp_path,
        max_upload_mb=1,
    )

    assert staged.original_filename == "paper.png"
    assert staged.sha256 == sha256(content).hexdigest()
    assert staged.size_bytes == len(content)
    assert staged.mime_type == "image/png"
    assert staged.width == 12
    assert staged.height == 8

    relative_path = commit_staged_raw_asset(
        staged=staged,
        storage_root=tmp_path,
        asset_public_id="asset_test",
    )

    assert relative_path == f"raw/assets/{staged.sha256[:2]}/asset_test.original.png"
    assert stored_path(tmp_path, relative_path).read_bytes() == content
    assert not staged.temp_path.exists()


def test_stage_upload_rejects_mismatched_mime_type(tmp_path: Path) -> None:
    with pytest.raises(UnsupportedUploadError, match="MIME 类型"):
        stage_upload_file(
            fileobj=BytesIO(png_bytes()),
            original_filename="paper.png",
            declared_content_type="image/jpeg",
            storage_root=tmp_path,
            max_upload_mb=1,
        )


def test_stage_upload_rejects_empty_file_without_leaving_temp_file(
    tmp_path: Path,
) -> None:
    with pytest.raises(UnsupportedUploadError, match="为空"):
        stage_upload_file(
            fileobj=BytesIO(b""),
            original_filename="paper.png",
            declared_content_type="image/png",
            storage_root=tmp_path,
            max_upload_mb=1,
        )

    assert not list((tmp_path / "tmp" / "uploads").glob("*.tmp"))


def test_stage_upload_rejects_missing_extension(tmp_path: Path) -> None:
    with pytest.raises(UnsupportedUploadError, match="扩展名"):
        stage_upload_file(
            fileobj=BytesIO(png_bytes()),
            original_filename="paper",
            declared_content_type="image/png",
            storage_root=tmp_path,
            max_upload_mb=1,
        )


def test_commit_raw_asset_refuses_overwrite(tmp_path: Path) -> None:
    first = stage_upload_file(
        fileobj=BytesIO(png_bytes()),
        original_filename="paper.png",
        declared_content_type="image/png",
        storage_root=tmp_path,
        max_upload_mb=1,
    )
    commit_staged_raw_asset(
        staged=first,
        storage_root=tmp_path,
        asset_public_id="asset_same",
    )

    second = stage_upload_file(
        fileobj=BytesIO(png_bytes()),
        original_filename="paper.png",
        declared_content_type="image/png",
        storage_root=tmp_path,
        max_upload_mb=1,
    )
    try:
        with pytest.raises(StorageError, match="拒绝覆盖"):
            commit_staged_raw_asset(
                staged=second,
                storage_root=tmp_path,
                asset_public_id="asset_same",
            )
    finally:
        second.discard()


def test_commit_raw_asset_rejects_path_traversal_public_id(tmp_path: Path) -> None:
    staged = stage_upload_file(
        fileobj=BytesIO(png_bytes()),
        original_filename="paper.png",
        declared_content_type="image/png",
        storage_root=tmp_path,
        max_upload_mb=1,
    )
    try:
        with pytest.raises(StorageError, match="安全相对路径"):
            commit_staged_raw_asset(
                staged=staged,
                storage_root=tmp_path,
                asset_public_id="../../escape",
            )

        assert staged.temp_path.exists()
        assert not any((tmp_path / "raw").glob("**/*")) if (tmp_path / "raw").exists() else True
    finally:
        staged.discard()


def test_remove_committed_raw_asset_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(StorageError, match="安全相对路径"):
        remove_committed_raw_asset(
            storage_root=tmp_path,
            storage_path="raw/assets/aa/../../escape.original.png",
        )
