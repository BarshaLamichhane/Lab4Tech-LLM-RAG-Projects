from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


CATALOG_FILENAME = "index.json"


def load_profile_catalog(data_dir: Path) -> dict:
    path = data_dir / CATALOG_FILENAME
    if not path.exists():
        return {"profiles": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"profiles": []}
    profiles = payload.get("profiles", [])
    return {"profiles": profiles if isinstance(profiles, list) else []}


def profile_paths(data_dir: Path) -> list[Path]:
    """Return catalogued profiles first, with uncatalogued legacy profiles included."""
    if not data_dir.exists():
        return []
    catalogued: list[Path] = []
    seen: set[str] = set()
    for item in load_profile_catalog(data_dir)["profiles"]:
        filename = item.get("file") if isinstance(item, dict) else None
        path = data_dir / filename if isinstance(filename, str) else None
        if path and path.is_file() and path.name != CATALOG_FILENAME:
            catalogued.append(path)
            seen.add(path.name)
    legacy = [
        path
        for path in sorted(data_dir.glob("*.json"))
        if path.name != CATALOG_FILENAME and path.name not in seen
    ]
    return [*catalogued, *legacy]


def update_profile_catalog(data_dir: Path, profile: dict, filename: str) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    catalog = load_profile_catalog(data_dir)
    profiles = [
        item
        for item in catalog["profiles"]
        if isinstance(item, dict) and item.get("file") != filename
    ]
    profiles.append(
        {
            "role": profile.get("role", ""),
            "company": profile.get("company_name", ""),
            "file": filename,
            "created_at": datetime.now(UTC).date().isoformat(),
        }
    )
    profiles.sort(key=lambda item: (str(item.get("role", "")).casefold(), str(item.get("company", "")).casefold()))
    path = data_dir / CATALOG_FILENAME
    path.write_text(json.dumps({"profiles": profiles}, indent=2), encoding="utf-8")
    return path


def profile_display_name(profile: dict) -> str:
    role = str(profile.get("role", "")).strip() or "Unknown role"
    company = str(profile.get("company_name", "")).strip()
    return f"{role} at {company}" if company else role
