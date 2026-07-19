from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv


@dataclass
class AppConfig:
    settings: Dict[str, Any]
    prompts: Dict[str, Any]
    root_dir: Path
    data_dir: Path


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"YAML not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(
    root_dir: Optional[str] = None,
    settings_path: str = "settings.yaml",
    prompts_path: str = "prompts.yaml",
    env_path: str = ".env",
) -> AppConfig:
    root = Path(root_dir) if root_dir else Path.cwd()

    # .env は存在する場合だけ読み込む
    env_file = root / env_path
    if env_file.exists():
        load_dotenv(env_file)

    settings = load_yaml(root / settings_path)
    prompts = load_yaml(root / prompts_path)

    data_dir = root / settings.get("project", {}).get("data_dir", "data")
    data_dir.mkdir(parents=True, exist_ok=True)

    return AppConfig(settings=settings, prompts=prompts, root_dir=root, data_dir=data_dir)


def env_get(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()
