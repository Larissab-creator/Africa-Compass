"""Africa Compass: reproducible OpenStreetMap data pipeline.

Pilot area: Victoria, Mahe, Seychelles.
Downloads named OSM features, normalises their attributes, validates records,
and writes CSV and DuckDB outputs for downstream mapping and analysis.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
RAW_FILE = RAW_DIR / "victoria_osm_raw.json"
CSV_FILE = PROCESSED_DIR / "victoria_places.csv"
DB_FILE = PROCESSED_DIR / "africa_compass.duckdb"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
# Overpass bbox order: south, west, north, east.
BBOX = (-4.64, 55.43, -4.60, 55.47)
SLEEP_SECONDS = 2

QUERY = """
[out:json][timeout:90];
(
  node["name"]({south},{west},{north},{east});
  way["name"]({south},{west},{north},{east});
  relation["name"]({south},{west},{north},{east});
);
out center tags;
""".format(south=BBOX[0], west=BBOX[1], north=BBOX[2], east=BBOX[3])

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOGGER = logging.getLogger("africa_compass")


def fetch_map_data(
    retries: int = 3, session: requests.Session | None = None
) -> dict[str, Any]:
    """Download named OpenStreetMap features and preserve the raw response."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    client = session or requests.Session()
    headers = {"User-Agent": "AfricaCompass/0.2 (educational mapping project)"}

    for attempt in range(1, retries + 1):
        try:
            response = client.post(
                OVERPASS_URL, data={"data": QUERY}, headers=headers, timeout=120
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload.get("elements"), list):
                raise ValueError("Overpass response does not contain an elements list")
            RAW_FILE.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            LOGGER.info(
                "Saved %s raw features to %s", len(payload["elements"]), RAW_FILE
            )
            time.sleep(SLEEP_SECONDS)
            return payload
        except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
            LOGGER.warning("Download attempt %s/%s failed: %s", attempt, retries, exc)
            if attempt == retries:
                raise
            time.sleep(2**attempt)

    raise RuntimeError("OSM download failed unexpectedly")


def classify_feature(tags: dict[str, Any]) -> str:
    """Assign a practical high-level category using OSM tags."""
    if any(key in tags for key in ("amenity", "healthcare", "school", "shop")):
        return "service"
    if any(key in tags for key in ("highway", "public_transport", "railway", "route")):
        return "transport"
    if any(key in tags for key in ("tourism", "historic", "leisure", "natural")):
        return "attraction"
    return "place"


def transform_features(payload: dict[str, Any]) -> pd.DataFrame:
    """Convert raw OSM elements into a consistent tabular dataset."""
    rows: list[dict[str, Any]] = []
    tag_keys = (
        "amenity", "healthcare", "school", "shop", "highway",
        "public_transport", "railway", "tourism", "historic", "leisure", "natural",
    )

    for element in payload.get("elements", []):
        tags = element.get("tags") or {}
        name = tags.get("name")
        if not name:
            continue

        latitude, longitude = element.get("lat"), element.get("lon")
        if latitude is None or longitude is None:
            centre = element.get("center") or {}
            latitude, longitude = centre.get("lat"), centre.get("lon")

        rows.append(
            {
                "osm_id": str(element.get("id", "")),
                "osm_type": element.get("type", "unknown"),
                "name": str(name).strip(),
                "category": classify_feature(tags),
                "subcategory": next(
                    (tags[key] for key in tag_keys if tags.get(key)),
                    "unclassified",
                ),
                "latitude": latitude,
                "longitude": longitude,
                "address": " ".join(
                    str(tags[key]).strip()
                    for key in ("addr:housenumber", "addr:street", "addr:city")
                    if tags.get(key)
                ),
                "website": tags.get("website") or tags.get("contact:website"),
                "phone": tags.get("phone") or tags.get("contact:phone"),
                "opening_hours": tags.get("opening_hours"),
                "source": "OpenStreetMap",
            }
        )

    columns = [
        "osm_id", "osm_type", "name", "category", "subcategory", "latitude",
        "longitude", "address", "website", "phone", "opening_hours", "source",
    ]
    df = pd.DataFrame(rows, columns=columns)
    if not df.empty:
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    return df


def validate_features(df: pd.DataFrame) -> pd.DataFrame:
    """Remove unusable, duplicate, and out-of-area OSM records."""
    required = ["osm_id", "osm_type", "name", "latitude", "longitude"]
    clean = df.dropna(subset=required).copy()
    clean = clean[clean["osm_id"].astype(str).str.strip().ne("")]
    clean = clean[clean["osm_type"].astype(str).str.strip().ne("")]
    clean = clean[clean["name"].str.strip().ne("")]
    clean = clean[clean["latitude"].between(-90, 90)]
    clean = clean[clean["longitude"].between(-180, 180)]

    # OSM returns ways/relations that intersect the query area, but their
    # representative centre can fall outside it. Keep map points in the
    # Victoria pilot boundary so island-wide features do not distort the map.
    south, west, north, east = BBOX
    clean = clean[clean["latitude"].between(south, north)]
    clean = clean[clean["longitude"].between(west, east)]

    clean = clean.drop_duplicates(subset=["osm_type", "osm_id"])
    return clean.reset_index(drop=True)


def save_outputs(df: pd.DataFrame) -> None:
    """Write the processed dataset to CSV and a DuckDB database."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_FILE, index=False, encoding="utf-8")

    with duckdb.connect(str(DB_FILE)) as connection:
        connection.register("processed_features", df)
        connection.execute(
            "CREATE OR REPLACE TABLE victoria_places AS "
            "SELECT * FROM processed_features"
        )
        connection.unregister("processed_features")

    LOGGER.info("Saved %s validated records to %s", len(df), CSV_FILE)
    LOGGER.info("Saved DuckDB database to %s", DB_FILE)


def run_pipeline() -> pd.DataFrame:
    """Run download, transformation, validation, and output steps."""
    raw_data = fetch_map_data()
    transformed = transform_features(raw_data)
    validated = validate_features(transformed)
    save_outputs(validated)
    LOGGER.info(
        "Pipeline complete: %s raw elements -> %s named -> %s valid records",
        len(raw_data.get("elements", [])),
        len(transformed),
        len(validated),
    )
    return validated


if __name__ == "__main__":
    run_pipeline()
