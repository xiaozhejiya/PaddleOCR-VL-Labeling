"""资产导入服务测试。

覆盖事项：
1. 正常上传和重复 sha256 复用时，raw asset、document、page 和审计记录一致。
2. 项目或用户前置校验失败时，不进入文件暂存和数据库提交。
3. 数据库写入失败或重复 sha256 并发竞争时，不能残留本次 raw 文件。
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from PIL import Image
from sqlalchemy.exc import IntegrityError

from app.db.models import Asset, Document, Page, Project
from app.services import asset_service


class FakeDb:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def png_bytes() -> bytes:
    image = Image.new("RGB", (16, 9), color=(0, 0, 0))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def storage_has_files(root: Path) -> bool:
    return any(path.is_file() for path in root.rglob("*"))


def install_common_repo_fakes(
    monkeypatch: Any, calls: list[tuple[str, dict[str, Any]]]
) -> None:
    monkeypatch.setattr(
        asset_service.asset_repository,
        "get_project_by_id",
        lambda _db, project_id: Project(id=project_id, name="测试项目"),
    )
    monkeypatch.setattr(
        asset_service.asset_repository,
        "get_active_user_by_id",
        lambda _db, user_id: object() if user_id == 99 else None,
    )

    def create_document_for_upload(_db: object, **kwargs: Any) -> Document:
        calls.append(("document", kwargs))
        return Document(
            id=20,
            public_id=kwargs["public_id"],
            project_id=kwargs["project_id"],
            document_type="uploaded_image",
            source_type="upload",
            domain_metadata_json={},
            split="train",
            lock_status="unlocked",
        )

    def create_page_for_upload(_db: object, **kwargs: Any) -> Page:
        calls.append(("page", kwargs))
        return Page(
            id=30,
            public_id=kwargs["public_id"],
            document_id=kwargs["document_id"],
            page_index=0,
            image_asset_id=kwargs["image_asset_id"],
            width=kwargs["width"],
            height=kwargs["height"],
            status="imported",
        )

    def write_upload_audit_log(_db: object, **kwargs: Any) -> None:
        calls.append(("audit", kwargs))

    monkeypatch.setattr(
        asset_service.asset_repository,
        "create_document_for_upload",
        create_document_for_upload,
    )
    monkeypatch.setattr(
        asset_service.asset_repository,
        "create_page_for_upload",
        create_page_for_upload,
    )
    monkeypatch.setattr(
        asset_service.asset_repository,
        "write_upload_audit_log",
        write_upload_audit_log,
    )


def test_import_uploaded_image_creates_raw_asset_document_and_page(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    install_common_repo_fakes(monkeypatch, calls)
    monkeypatch.setattr(
        asset_service.asset_repository, "get_asset_by_sha256", lambda _db, _sha: None
    )

    def create_asset(_db: object, **kwargs: Any) -> Asset:
        calls.append(("asset", kwargs))
        assert (tmp_path / Path(*kwargs["storage_path"].split("/"))).exists()
        return Asset(id=10, **kwargs)

    monkeypatch.setattr(asset_service.asset_repository, "create_asset", create_asset)

    db = FakeDb()
    result = asset_service.import_uploaded_image(
        db,  # type: ignore[arg-type]
        project_id=1,
        fileobj=BytesIO(png_bytes()),
        original_filename="paper.png",
        content_type="image/png",
        created_by=99,
        storage_root=tmp_path,
        max_upload_mb=1,
    )

    assert result.asset_reused is False
    assert result.asset.public_id.startswith("asset_")
    assert result.document.public_id.startswith("doc_")
    assert result.page.public_id.startswith("page_")
    assert result.page.width == 16
    assert result.page.height == 9
    assert db.commits == 1
    assert db.rollbacks == 0
    assert [name for name, _kwargs in calls] == ["asset", "document", "page", "audit"]
    assert calls[-1][1]["asset_reused"] is False


def test_import_uploaded_image_reuses_existing_sha_without_raw_overwrite(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    install_common_repo_fakes(monkeypatch, calls)
    existing_asset = Asset(
        id=10,
        public_id="asset_existing",
        asset_type="page_image",
        storage_path="raw/assets/aa/asset_existing.original.png",
        original_filename="paper.png",
        mime_type="image/png",
        size_bytes=123,
        sha256="a" * 64,
        width=16,
        height=9,
        readonly=True,
    )
    monkeypatch.setattr(
        asset_service.asset_repository,
        "get_asset_by_sha256",
        lambda _db, _sha: existing_asset,
    )

    def create_asset(_db: object, **_kwargs: Any) -> Asset:
        raise AssertionError("重复 sha256 上传不能创建新的 asset 记录")

    monkeypatch.setattr(asset_service.asset_repository, "create_asset", create_asset)

    db = FakeDb()
    result = asset_service.import_uploaded_image(
        db,  # type: ignore[arg-type]
        project_id=1,
        fileobj=BytesIO(png_bytes()),
        original_filename="paper.png",
        content_type="image/png",
        created_by=99,
        storage_root=tmp_path,
        max_upload_mb=1,
    )

    assert result.asset_reused is True
    assert result.asset.public_id == "asset_existing"
    assert db.commits == 1
    assert db.rollbacks == 0
    assert (
        not list((tmp_path / "raw").glob("**/*"))
        if (tmp_path / "raw").exists()
        else True
    )
    assert [name for name, _kwargs in calls] == ["document", "page", "audit"]
    assert calls[-1][1]["asset_reused"] is True


def test_import_uploaded_image_rejects_missing_project_before_file_staging(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        asset_service.asset_repository,
        "get_project_by_id",
        lambda _db, _project_id: None,
    )

    def fail_if_staged(**_kwargs: Any) -> None:
        raise AssertionError("项目不存在时不能写入上传临时文件")

    monkeypatch.setattr(asset_service, "stage_upload_file", fail_if_staged)

    db = FakeDb()
    with pytest.raises(asset_service.ProjectNotFoundError, match="项目不存在"):
        asset_service.import_uploaded_image(
            db,  # type: ignore[arg-type]
            project_id=404,
            fileobj=BytesIO(png_bytes()),
            original_filename="paper.png",
            content_type="image/png",
            created_by=99,
            storage_root=tmp_path,
            max_upload_mb=1,
        )

    assert db.commits == 0
    assert db.rollbacks == 0
    assert not storage_has_files(tmp_path)


def test_import_uploaded_image_rejects_inactive_user_before_file_staging(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        asset_service.asset_repository,
        "get_project_by_id",
        lambda _db, project_id: Project(id=project_id, name="测试项目"),
    )
    monkeypatch.setattr(
        asset_service.asset_repository,
        "get_active_user_by_id",
        lambda _db, _user_id: None,
    )

    def fail_if_staged(**_kwargs: Any) -> None:
        raise AssertionError("用户不可用时不能写入上传临时文件")

    monkeypatch.setattr(asset_service, "stage_upload_file", fail_if_staged)

    db = FakeDb()
    with pytest.raises(asset_service.UserNotFoundError, match="用户不可用"):
        asset_service.import_uploaded_image(
            db,  # type: ignore[arg-type]
            project_id=1,
            fileobj=BytesIO(png_bytes()),
            original_filename="paper.png",
            content_type="image/png",
            created_by=100,
            storage_root=tmp_path,
            max_upload_mb=1,
        )

    assert db.commits == 0
    assert db.rollbacks == 0
    assert not storage_has_files(tmp_path)


def test_import_uploaded_image_cleans_raw_file_when_page_creation_fails(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    install_common_repo_fakes(monkeypatch, calls)
    monkeypatch.setattr(
        asset_service.asset_repository, "get_asset_by_sha256", lambda _db, _sha: None
    )

    def create_asset(_db: object, **kwargs: Any) -> Asset:
        calls.append(("asset", kwargs))
        assert (tmp_path / Path(*kwargs["storage_path"].split("/"))).exists()
        return Asset(id=10, **kwargs)

    def create_page_for_upload(_db: object, **kwargs: Any) -> Page:
        calls.append(("page", kwargs))
        raise RuntimeError("page insert failed")

    monkeypatch.setattr(asset_service.asset_repository, "create_asset", create_asset)
    monkeypatch.setattr(
        asset_service.asset_repository,
        "create_page_for_upload",
        create_page_for_upload,
    )

    db = FakeDb()
    with pytest.raises(asset_service.AssetImportError, match="文件资产导入失败"):
        asset_service.import_uploaded_image(
            db,  # type: ignore[arg-type]
            project_id=1,
            fileobj=BytesIO(png_bytes()),
            original_filename="paper.png",
            content_type="image/png",
            created_by=99,
            storage_root=tmp_path,
            max_upload_mb=1,
        )

    assert db.commits == 0
    assert db.rollbacks == 1
    assert [name for name, _kwargs in calls] == ["asset", "document", "page"]
    assert not storage_has_files(tmp_path)


def test_import_uploaded_image_reuses_existing_asset_after_duplicate_race(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    lookups = 0
    install_common_repo_fakes(monkeypatch, calls)
    existing_asset = Asset(
        id=11,
        public_id="asset_existing_after_race",
        asset_type="page_image",
        storage_path="raw/assets/aa/asset_existing_after_race.original.png",
        original_filename="paper.png",
        mime_type="image/png",
        size_bytes=123,
        sha256="b" * 64,
        width=16,
        height=9,
        readonly=True,
    )

    def get_asset_by_sha256(_db: object, _sha: str) -> Asset | None:
        nonlocal lookups
        lookups += 1
        return None if lookups == 1 else existing_asset

    def create_asset(_db: object, **kwargs: Any) -> Asset:
        calls.append(("asset", kwargs))
        assert (tmp_path / Path(*kwargs["storage_path"].split("/"))).exists()
        raise IntegrityError("INSERT assets", {}, Exception("duplicate sha256"))

    monkeypatch.setattr(
        asset_service.asset_repository, "get_asset_by_sha256", get_asset_by_sha256
    )
    monkeypatch.setattr(asset_service.asset_repository, "create_asset", create_asset)

    db = FakeDb()
    result = asset_service.import_uploaded_image(
        db,  # type: ignore[arg-type]
        project_id=1,
        fileobj=BytesIO(png_bytes()),
        original_filename="paper.png",
        content_type="image/png",
        created_by=99,
        storage_root=tmp_path,
        max_upload_mb=1,
    )

    assert result.asset_reused is True
    assert result.asset.public_id == "asset_existing_after_race"
    assert db.rollbacks == 1
    assert db.commits == 1
    assert lookups == 2
    assert [name for name, _kwargs in calls] == ["asset", "document", "page", "audit"]
    assert not storage_has_files(tmp_path)
