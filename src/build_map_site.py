"""Assemble the Africa Compass Mahé road-map website files."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE_GEOJSON = ROOT / "data" / "processed" / "mahe_roads.geojson"
SOURCE_SNAPSHOT = ROOT / "data" / "history" / "mahe_roads_snapshot.json"
SOURCE_ROADS_CSV = ROOT / "data" / "processed" / "mahe_roads.csv"
SOURCE_CHANGES_CSV = ROOT / "data" / "processed" / "mahe_road_changes.csv"
SOURCE_HTML = ROOT / "docs" / "map" / "index.html"
SITE_DIR = ROOT / "_site"
SITE_DATA_DIR = SITE_DIR / "data"


def build_site() -> dict[str, Path]:
    """Copy the interactive app and current road data into a Pages-ready folder."""
    required = [SOURCE_GEOJSON, SOURCE_ROADS_CSV, SOURCE_CHANGES_CSV, SOURCE_HTML]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Required road-map inputs are missing: " + ", ".join(missing))

    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HTML, SITE_DIR / "index.html")
    shutil.copy2(SOURCE_GEOJSON, SITE_DATA_DIR / "mahe_roads.geojson")
    shutil.copy2(SOURCE_ROADS_CSV, SITE_DATA_DIR / "mahe_roads.csv")
    shutil.copy2(SOURCE_CHANGES_CSV, SITE_DATA_DIR / "mahe_road_changes.csv")

    geojson = json.loads(SOURCE_GEOJSON.read_text(encoding="utf-8"))
    features = geojson.get("features", [])
    status_counts: dict[str, int] = {}
    for feature in features:
        status = feature.get("properties", {}).get("road_status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    snapshot = {}
    baseline_established = SOURCE_SNAPSHOT.exists()
    if baseline_established:
        snapshot = json.loads(SOURCE_SNAPSHOT.read_text(encoding="utf-8"))

    metadata = {
        "island": "Mahé, Seychelles",
        "source": "OpenStreetMap contributors",
        "snapshot_created_utc": snapshot.get("snapshot_created_utc"),
        "baseline_established": baseline_established,
        "osm_relation_id": snapshot.get("osm_relation_id"),
        "road_feature_count": len(features),
        "named_road_feature_count": sum(
            bool((f.get("properties", {}).get("name") or "").strip())
            for f in features
        ),
        "road_status_counts": status_counts,
        "change_tracking_note": (
            "Changes refer to differences between Africa Compass OpenStreetMap "
            "snapshots; they do not prove physical road construction or closure."
        ),
    }
    metadata_path = SITE_DATA_DIR / "mahe_map_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return {
        "index": SITE_DIR / "index.html",
        "geojson": SITE_DATA_DIR / "mahe_roads.geojson",
        "roads_csv": SITE_DATA_DIR / "mahe_roads.csv",
        "changes_csv": SITE_DATA_DIR / "mahe_road_changes.csv",
        "metadata": metadata_path,
    }


if __name__ == "__main__":
    for name, path in build_site().items():
        print(f"{name}: {path}")
