
import json
import time
from pathlib import Path

import requests

# Africa Compass: first mapping data pipeline
# Pilot location: Victoria, Mahe, Seychelles

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
RAW_FILE = RAW_DIR / "victoria_osm_raw.json"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

QUERY = """
[out:json][timeout:60];
(
  node["name"]( -4.64,55.43,-4.60,55.47);
  way["name"]( -4.64,55.43,-4.60,55.47);
  relation["name"]( -4.64,55.43,-4.60,55.47);
);
out center tags;
"""


def fetch_map_data():
    """Download named OpenStreetMap features around Victoria."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    response = requests.post(
        OVERPASS_URL,
        data={"data": QUERY},
        headers={"User-Agent": "AfricaCompass/0.1 educational mapping project"},
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()

    # Preserve the original API response as received.
    RAW_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Saved raw data to: {RAW_FILE}")
    print(f"Features returned: {len(payload.get('elements', []))}")
    return payload


if __name__ == "__main__":
    fetch_map_data()

