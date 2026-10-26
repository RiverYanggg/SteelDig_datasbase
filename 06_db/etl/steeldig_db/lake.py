"""资产湖：内容寻址的不可变对象存储。

本地实现采用 S3 风格的 key 布局，可整体平移到 MinIO / S3 / OSS::

    <lake>/objects/sha256/ab/cd/<sha256>.<ext>

同一份字节只落一次（图片跨论文重复率很高），因此湖的体积 ≈ 去重后的真实字节数。
对象一经写入不覆盖、不删除；DB 里的 lake.object / lake.object_ref 只是它的目录。
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_EXT_BY_MEDIA = {
    "application/json": "json",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/tiff": "tif",
    "image/bmp": "bmp",
    "application/pdf": "pdf",
    "text/markdown": "md",
    "text/plain": "txt",
}

_KIND_BY_MEDIA = {
    "application/json": "json",
    "application/pdf": "pdf",
    "text/markdown": "markdown",
    "text/plain": "text",
}


@dataclass(frozen=True)
class StoredObject:
    object_id: str
    bytes: int
    media_type: str
    kind: str
    uri: str


class Lake:
    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.objects = self.root / "objects" / "sha256"
        self.objects.mkdir(parents=True, exist_ok=True)
        self._written = 0
        self._reused = 0

    # -- 内部 --------------------------------------------------------------
    def _path_for(self, object_id: str, ext: str) -> Path:
        return self.objects / object_id[:2] / object_id[2:4] / f"{object_id}.{ext}"

    def _put(self, data: bytes, media_type: str) -> StoredObject:
        object_id = hashlib.sha256(data).hexdigest()
        ext = _EXT_BY_MEDIA.get(media_type) or "bin"
        path = self._path_for(object_id, ext)
        kind = _KIND_BY_MEDIA.get(media_type, "image" if media_type.startswith("image/") else "other")
        if path.exists():
            self._reused += 1
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_bytes(data)
            os.replace(tmp, path)          # 原子落盘
            self._written += 1
        return StoredObject(object_id, len(data), media_type, kind,
                            str(path.relative_to(self.root)))

    # -- 对外 --------------------------------------------------------------
    def put_json(self, obj: Any) -> StoredObject:
        # 规范化序列化：sort_keys + 紧凑分隔符，保证同内容同哈希
        data = json.dumps(obj, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
        return self._put(data, "application/json")

    def put_bytes(self, data: bytes, media_type: str) -> StoredObject:
        return self._put(data, media_type)

    def put_file(self, path: Path) -> StoredObject:
        media, _ = mimetypes.guess_type(path.name)
        if not media:
            media = "application/octet-stream"
        return self._put(path.read_bytes(), media)

    def resolve(self, uri: str) -> Path:
        return (self.root / uri).resolve()

    # -- 校验 --------------------------------------------------------------
    def verify(self) -> dict[str, Any]:
        """全量重算哈希，确认湖没有被篡改/损坏。"""
        total, bad, size = 0, [], 0
        for p in self.objects.rglob("*"):
            if not p.is_file() or p.suffix == ".tmp":
                continue
            total += 1
            size += p.stat().st_size
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if digest != p.stem:
                bad.append(str(p))
        return {"objects": total, "bytes": size, "corrupted": bad}

    @property
    def stats(self) -> dict[str, int]:
        return {"written": self._written, "reused": self._reused}
