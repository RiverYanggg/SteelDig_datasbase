"""运行配置：环境变量优先，其次读取 06_db/.env。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DB_HOME = Path(__file__).resolve().parents[2]          # 06_db/
REPO_HOME = DB_HOME.parent                              # database/


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


_load_dotenv(DB_HOME / ".env")


@dataclass(frozen=True)
class Settings:
    dsn: str
    lake_backend: str
    lake_root: Path
    extraction_root: Path
    mineru_root: Path
    manifests_root: Path
    embed_model: str | None
    model_cache: Path
    dataset_version: str
    app_name: str

    @classmethod
    def load(cls) -> "Settings":
        lake_root = os.environ.get("STEELDIG_LAKE_ROOT", "../05_lake")
        return cls(
            dsn=os.environ.get(
                "STEELDIG_DSN",
                "postgresql://steeldig:steeldig_dev_pw@127.0.0.1:5435/steeldig",
            ),
            lake_backend=os.environ.get("STEELDIG_LAKE_BACKEND", "local"),
            lake_root=(DB_HOME / lake_root).resolve() if not os.path.isabs(lake_root) else Path(lake_root),
            extraction_root=Path(
                os.environ.get("STEELDIG_EXTRACTION_ROOT", str(REPO_HOME / "02_extraction"))
            ),
            mineru_root=Path(
                os.environ.get("STEELDIG_MINERU_ROOT", str(REPO_HOME / "01_raw" / "mineru_source"))
            ),
            manifests_root=Path(
                os.environ.get("STEELDIG_MANIFESTS_ROOT", str(REPO_HOME / "03_manifests"))
            ),
            embed_model=os.environ.get("STEELDIG_EMBED_MODEL") or None,
            model_cache=(DB_HOME / os.environ.get("STEELDIG_MODEL_CACHE", ".cache/models")).resolve()
            if not os.path.isabs(os.environ.get("STEELDIG_MODEL_CACHE", "")) 
            else Path(os.environ["STEELDIG_MODEL_CACHE"]),
            dataset_version=os.environ.get("STEELDIG_DATASET_VERSION", "2026.10"),
            app_name=os.environ.get("STEELDIG_APP_NAME", "SteelDig"),
        )


settings = Settings.load()
