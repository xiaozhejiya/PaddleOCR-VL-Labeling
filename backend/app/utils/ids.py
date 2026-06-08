from __future__ import annotations

import secrets


def new_public_id(prefix: str) -> str:
    """生成对外稳定编号；数据库内部主键不暴露给 API 和文件 manifest。"""

    return f"{prefix}_{secrets.token_hex(8)}"
