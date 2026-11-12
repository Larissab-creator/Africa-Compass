"""Build a full Mahé Island road inventory and interactive road map.

Road changes mean changes between Africa Compass OpenStreetMap snapshots.
They do not establish that a road was physically constructed or removed.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

import folium
import pandas as pd
import requests
from folium.features import GeoJsonPopup, GeoJsonTooltip

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
HISTORY_DIR = ROOT / "data" / "history"
OUTPUT_DIR = ROOT / "outputs"

RAW_FILE = RAW_DIR / "mahe_roads_overpass.json"
ROADS_CSV = PROCESSED_DIR / "mahe_roads.csv"
ROADS_GEOJSON = PROCESSED_DIR / "mahe_roads.geojson"
CHANGES_CSV = PROCESSED_DIR / "mahe_road_changes.csv"
SNAPSHOT_FILE = HISTORY_DIR / "mahe_roads_snapshot.json"
MAP_FILE = OUTPUT_DIR / "mahe_road_network.html"

# OpenStreetMap relation for Mahé Island. Overpass area IDs for relations
# are formed by adding 3,600,000,000 to the relation ID.
MAHE_RELATION_ID = 9435209
MAHE_AREA_ID = 3_600_000_000 + MAHE_RELATION_ID

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
REQUEST_TIMEOUT = 110
RETRIES_PER_ENDPOINT = 1
REQUEST_PAUSE_SECONDS = 2

QUERY = f"""
[out:json][timeout:90];
area({MAHE_AREA_ID})->.mahe;
way["highway"](area.mahe);
out meta geom;
"""

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOGGER = logging.getLogger("africa_compass.mahe_roads")

ROAD_COLORS = {
    "motorway": "#8B1E3F",
    "trunk": "#B23A48",
    "primary": "#D97706",
    "secondary": "#E7A23B",
    "tertiary": "#E0B84B",
    "residential": "#356A8A",
    "unclassified": "#527C91",
    "living_street": "#6B8F71",
    "service": "#7F8C8D",
    "track": "#8B8B62",
    "road": "#6C757D",
}
ROAD_WIDTHS = {
    "motorway": 5, "trunk": 4.5, "primary": 4, "secondary": 3.5,
    "tertiary": 3, "residential": 2.4, "unclassified": 2.2,
    "living_street": 2.2, "service": 1.8, "track": 1.6, "road": 2,
}
CSV_COLUMNS = [
    "osm_id", "name", "road_class", "ref", "surface", "lanes", "oneway",
    "access", "lit", "maxspeed", "bridge", "tunnel", "version",
    "last_edited_utc", "road_status", "coordinate_count", "osm_url",
]
CHANGE_COLUMNS = [
    "osm_id", "name", "change_type", "old_version", "new_version",
    "last_edited_utc", "osm_url",
]


def _request_overpass(
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Fetch the Mahé road ways, switching hosts when an endpoint is busy."""
    client = session or requests.Session()
    headers = {
        "User-Agent": (
            "AfricaCompass/0.4 (Mahé road mapping project; "
            "https://github.com/Larissab-creator/Africa-Compass)"
        )
    }
    last_error: Exception | None = None

    for endpoint in OVERPASS_ENDPOINTS:
        for attempt in range(1, RETRIES_PER_ENDPOINT + 1):
            try:
                LOGGER.info("Querying Mahé road network from %s", endpoint)
                response = client.post(
                    endpoint, data={"data": QUERY}, headers=headers,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload.get("elements"), list):
                    raise ValueError("Overpass response has no elements list")
                LOGGER.info("Received %s road ways", len(payload["elements"]))
                time.sleep(REQUEST_PAUSE_SECONDS)
                return payload
            except requests.HTTPError as exc:
                last_error = exc
                status = exc.response.status_code if exc.response is not None else None
                LOGGER.warning("%s returned HTTP %s", endpoint, status)
                if status is not None and 400 <= status < 500:
                    break
                if status in {429, 500, 502, 503, 504}:
                    break
                if attempt < RETRIES_PER_ENDPOINT:
                    time.sleep(2**attempt)
            except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                LOGGER.warning("%s attempt %s failed: %s", endpoint, attempt, exc)
                if attempt < RETRIES_PER_ENDPOINT:
                    time.sleep(2**attempt)

    raise RuntimeError(
        f"All Overpass endpoints failed. Last error: {last_error}"
    ) from last_error


def fetch_road_data(
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Download and preserve the raw Overpass response."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    payload = _request_overpass(session=session)
    RAW_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


def _signature(tags: dict[str, Any], coordinates: list[list[float]]) -> str:
    content = json.dumps(
        {"tags": tags, "coordinates": coordinates},
        sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def process_road_elements(
    payload: dict[str, Any],
    previous_snapshot: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    """Convert OSM ways to GeoJSON features and classify snapshot changes."""
    previous = (previous_snapshot or {}).get("ways", {})
    features: list[dict[str, Any]] = []
    current: dict[str, Any] = {}

    for element in payload.get("elements", []):
        if element.get("type") != "way":
            continue
        tags = element.get("tags") or {}
        geometry = element.get("geometry") or []
        if len(geometry) < 2:
            continue
        coordinates = [
            [float(point["lon"]), float(point["lat"])]
            for point in geometry
            if point.get("lon") is not None and point.get("lat") is not None
        ]
        if len(coordinates) < 2:
            continue

        osm_id = str(element.get("id", ""))
        if not osm_id:
            continue
        version = int(element.get("version") or 0)
        edited = element.get("timestamp")
        signature = _signature(tags, coordinates)
        old = previous.get(osm_id)

        if previous_snapshot is None:
            road_status = "baseline"
        elif old is None:
            road_status = "newly_mapped"
        elif old.get("signature") != signature or int(old.get("version", 0)) != version:
            road_status = "updated"
        else:
            road_status = "existing"

        properties = {
            "osm_id": osm_id,
            "name": str(tags.get("name", "")).strip(),
            "road_class": tags.get("highway", "road"),
            "ref": tags.get("ref", ""),
            "surface": tags.get("surface", ""),
            "lanes": tags.get("lanes", ""),
            "oneway": tags.get("oneway", ""),
            "access": tags.get("access", ""),
            "lit": tags.get("lit", ""),
            "maxspeed": tags.get("maxspeed", ""),
            "bridge": tags.get("bridge", ""),
            "tunnel": tags.get("tunnel", ""),
            "version": version,
            "last_edited_utc": edited or "",
            "road_status": road_status,
            "coordinate_count": len(coordinates),
            "osm_url": f"https://www.openstreetmap.org/way/{osm_id}",
        }
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coordinates},
            "properties": properties,
        })
        current[osm_id] = {
            "version": version,
            "signature": signature,
            "name": properties["name"],
            "road_class": properties["road_class"],
            "last_edited_utc": edited or "",
        }

    changes: list[dict[str, Any]] = []
    if previous_snapshot is not None:
        for feature in features:
            props = feature["properties"]
            if props["road_status"] in {"newly_mapped", "updated"}:
                old = previous.get(props["osm_id"], {})
                changes.append({
                    "osm_id": props["osm_id"],
                    "name": props["name"],
                    "change_type": props["road_status"],
                    "old_version": old.get("version", ""),
                    "new_version": props["version"],
                    "last_edited_utc": props["last_edited_utc"],
                    "osm_url": props["osm_url"],
                })
        present_ids = set(current)
        for osm_id, old in previous.items():
            if osm_id not in present_ids:
                changes.append({
                    "osm_id": osm_id,
                    "name": old.get("name", ""),
                    "change_type": "no_longer_in_extract",
                    "old_version": old.get("version", ""),
                    "new_version": "",
                    "last_edited_utc": "",
                    "osm_url": f"https://www.openstreetmap.org/way/{osm_id}",
                })

    snapshot = {
        "island": "Mahé, Seychelles",
        "osm_relation_id": MAHE_RELATION_ID,
        "snapshot_created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "way_count": len(current),
        "ways": current,
    }
    return features, snapshot, changes


def _features_to_dataframe(features: list[dict[str, Any]]) -> pd.DataFrame:
    rows = [feature["properties"] for feature in features]
    return pd.DataFrame(rows, columns=CSV_COLUMNS)


def build_road_map(features: list[dict[str, Any]], output_file: Path = MAP_FILE) -> Path:
    """Create the island-wide interactive road map with selectable road layers."""
    if not features:
        raise ValueError("No road features were returned for Mahé.")

    coordinates = [
        coordinate
        for feature in features
        for coordinate in feature["geometry"]["coordinates"]
    ]
    min_lon = min(point[0] for point in coordinates)
    max_lon = max(point[0] for point in coordinates)
    min_lat = min(point[1] for point in coordinates)
    max_lat = max(point[1] for point in coordinates)
    centre = [(min_lat + max_lat) / 2, (min_lon + max_lon) / 2]

    fmap = folium.Map(
        location=centre, zoom_start=11, tiles="OpenStreetMap",
        control_scale=True, prefer_canvas=True,
    )

    title = """
    <div style="position: fixed; top: 14px; left: 60px; z-index: 9999;
      background: rgba(255,255,255,.96); padding: 10px 14px;
      border: 1px solid #d5dde5; border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,.12);">
      <div style="font-size:16px;font-weight:700;color:#17324D;">AFRICA COMPASS</div>
      <div style="font-size:12px;color:#486581;">Mahé Island · Interactive road map</div>
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(title))

    pedestrian_classes = {
        "footway", "path", "steps", "cycleway", "bridleway",
        "pedestrian", "corridor", "platform",
    }
    road_features = [
        feature for feature in features
        if feature["properties"].get("road_class") not in pedestrian_classes
    ]
    path_features = [
        feature for feature in features
        if feature["properties"].get("road_class") in pedestrian_classes
    ]

    all_roads = folium.FeatureGroup(name="Roads and streets", show=True)
    named_roads = folium.FeatureGroup(name="Named roads", show=False)
    unlabelled_roads = folium.FeatureGroup(name="Roads without a mapped name", show=False)
    paths_layer = folium.FeatureGroup(name="Footpaths, cycleways and trails", show=False)
    new_roads = folium.FeatureGroup(name="Newly mapped since last snapshot", show=True)
    updated_roads = folium.FeatureGroup(name="Updated since last snapshot", show=False)

    def style(feature: dict[str, Any]) -> dict[str, Any]:
        props = feature["properties"]
        road_class = props.get("road_class", "road")
        return {
            "color": ROAD_COLORS.get(road_class, "#6C757D"),
            "weight": ROAD_WIDTHS.get(road_class, 2),
            "opacity": 0.84,
        }

    all_geojson = folium.GeoJson(
        {"type": "FeatureCollection", "features": road_features},
        name="Roads and streets",
        style_function=style,
        tooltip=GeoJsonTooltip(
            fields=["name", "road_class", "ref", "surface", "road_status"],
            aliases=["Road name", "Road type", "Route reference", "Surface", "Map status"],
            sticky=False,
            labels=True,
        ),
        popup=GeoJsonPopup(
            fields=["name", "road_class", "surface", "lanes", "oneway",
                    "last_edited_utc", "osm_url"],
            aliases=["Road name", "Road type", "Surface", "Lanes",
                     "One-way", "Last edited in OSM", "OpenStreetMap"],
            labels=True,
            localize=True,
        ),
    ).add_to(all_roads)

    named_features = [
        feature for feature in road_features
        if feature["properties"].get("name")
    ]
    unnamed_features = [
        feature for feature in road_features
        if not feature["properties"].get("name")
    ]
    new_features = [
        feature for feature in road_features
        if feature["properties"].get("road_status") == "newly_mapped"
    ]
    updated_features = [
        feature for feature in road_features
        if feature["properties"].get("road_status") == "updated"
    ]

    def add_subset(layer: folium.FeatureGroup, subset: list[dict[str, Any]], colour: str) -> None:
        if not subset:
            return
        folium.GeoJson(
            {"type": "FeatureCollection", "features": subset},
            style_function=lambda feature: {
                "color": colour, "weight": 4, "opacity": 0.95,
            },
            tooltip=GeoJsonTooltip(
                fields=["name", "road_class", "road_status"],
                aliases=["Road name", "Road type", "Map status"],
            ),
        ).add_to(layer)

    add_subset(named_roads, named_features, "#177E89")
    add_subset(unlabelled_roads, unnamed_features, "#8A8F98")
    add_subset(paths_layer, path_features, "#89929B")
    add_subset(new_roads, new_features, "#D1495B")
    add_subset(updated_roads, updated_features, "#F4A261")

    for layer in (all_roads, named_roads, unlabelled_roads, paths_layer, new_roads, updated_roads):
        layer.add_to(fmap)

    legend = """
    <div style="position: fixed; bottom: 28px; left: 14px; z-index: 9999;
      background: rgba(255,255,255,.96); padding: 10px 13px;
      border: 1px solid #d5dde5; border-radius: 8px;
      font-size: 12px; color: #243B53;">
      <b>Road map key</b><br>
      <span style="color:#8B1E3F;">━━</span> Main routes<br>
      <span style="color:#356A8A;">━━</span> Local roads<br>
      <span style="color:#177E89;">━━</span> Named-road overlay<br>
      <span style="color:#89929B;">━━</span> Footpaths and trails<br>
      <span style="color:#D1495B;">━━</span> Newly mapped in this snapshot<br>
      <span style="color:#F4A261;">━━</span> Updated in this snapshot
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(legend))
    folium.LayerControl(collapsed=False).add_to(fmap)
    fmap.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]], padding=(18, 18))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(output_file))
    return output_file


def run_pipeline() -> dict[str, Path]:
    """Download, compare with prior snapshot, and build Mahé road outputs."""
    payload = fetch_road_data()
    previous = None
    if SNAPSHOT_FILE.exists():
        previous = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))

    features, snapshot, changes = process_road_elements(payload, previous)
    if not features:
        raise RuntimeError("Overpass returned no usable road geometries for Mahé.")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    roads_df = _features_to_dataframe(features)
    roads_df.to_csv(ROADS_CSV, index=False, encoding="utf-8")
    pd.DataFrame(changes, columns=CHANGE_COLUMNS).to_csv(
        CHANGES_CSV, index=False, encoding="utf-8"
    )
    ROADS_GEOJSON.write_text(
        json.dumps(
            {"type": "FeatureCollection", "features": features},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    SNAPSHOT_FILE.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    build_road_map(features, MAP_FILE)

    status_counts = roads_df["road_status"].value_counts().to_dict()
    LOGGER.info(
        "Mahé road map complete: %s roads, %s named, status=%s",
        len(roads_df), int(roads_df["name"].ne("").sum()), status_counts,
    )
    return {
        "roads_csv": ROADS_CSV,
        "roads_geojson": ROADS_GEOJSON,
        "road_changes": CHANGES_CSV,
        "road_snapshot": SNAPSHOT_FILE,
        "road_map": MAP_FILE,
    }


if __name__ == "__main__":
    for label, path in run_pipeline().items():
        print(f"{label}: {path}")
