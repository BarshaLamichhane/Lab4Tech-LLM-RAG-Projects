from __future__ import annotations

import json
from pathlib import Path

from backend.matching.skill_matching_engine import SKILL_CATEGORIES_PATH, SKILL_WEIGHTS


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = PROJECT_ROOT / "data" / "app_settings.json"


def load_app_settings() -> dict:
    taxonomy = _load_json(SKILL_CATEGORIES_PATH, {})
    saved = _load_json(SETTINGS_PATH, {})
    return {
        "skill_weights": saved.get("skill_weights", SKILL_WEIGHTS),
        "skill_aliases": taxonomy.get("skill_aliases", {}),
        "broad_skill_aliases": taxonomy.get("broad_skill_aliases", {}),
    }


def save_app_settings(settings: dict) -> dict:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps({"skill_weights": settings["skill_weights"]}, indent=2),
        encoding="utf-8",
    )

    taxonomy = _load_json(SKILL_CATEGORIES_PATH, {})
    taxonomy["skill_aliases"] = settings["skill_aliases"]
    taxonomy["broad_skill_aliases"] = settings["broad_skill_aliases"]
    SKILL_CATEGORIES_PATH.write_text(json.dumps(taxonomy, indent=2), encoding="utf-8")
    return load_app_settings()


def _load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))
