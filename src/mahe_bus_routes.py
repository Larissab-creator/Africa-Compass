"""Extract Mahé bus routes and stops from OpenStreetMap route relations.

Bus lines are shown only where an OSM route=bus relation has mapped road members.
This avoids inventing route geometry from timetables or route numbers alone.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

RAW_FILE = RAW_DIR / "mahe_bus_routes_overpass.json"
ROUTES_GEOJSON = PROCESSED_DIR / "mahe_bus_routes.geojson"
STOPS_GEOJSON = PROCESSED_DIR / "mahe_bus_stops.geojson"
ROUTES_CSV = PROCESSED_DIR / "mahe_bus_routes.csv"
STOPS_CSV = PROCESSED_DIR / "mahe_bus_stops.csv"

MAHE_RELATION_ID = 9435209
MAHE_AREA_ID = 3_600_000_000 + MAHE_RELATION_ID

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
REQUEST_TIMEOUT = 110
REQUEST_PAUSE_SECONDS = 2

QUERY = f"""
[out:json][timeout:90];
area({MAHE_AREA_ID})->.mahe;
relation["type"="route"]["route"="bus"](area.mahe)->.bus_routes;
way(r.bus_routes)->.bus_ways;
node(w.bus_ways)->.way_nodes;
node(r.bus_routes)->.route_nodes;
node["highway"="bus_stop"](area.mahe)->.highway_stops;
node["public_transport"="platform"](area.mahe)->.platform_stops;
(
  .bus_routes;
  .bus_ways;
  .way_nodes;
  .route_nodes;
  .highway_stops;
  .platform_stops;
);
out meta;
"""

ROUTE_COLUMNS = [
    "osm_id", "ref", "name", "from", "to", "operator", "network",
    "interval", "duration", "way_count", "stop_count", "geometry_status",
    "osm_url",
]
STOP_COLUMNS = ["osm_id", "name", "highway", "public_transport", "route_refs", "osm_url"]
STOP_ROLES = {
    "stop", "platform", "stop_entry_only", "stop_exit_only",
    "platform_entry_only", "platform_exit_only", "hail_and_ride",
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOGGER = logging.getLogger("africa_compass.mahe_bus_routes")


def fetch_bus_data(session: requests.Session | None = None) -> dict[str, Any]:
    """Fetch bus route relations, their member ways/nodes and mapped bus stops."""
    client = session or requests.Session()
    headers = {
        "User-Agent": (
            "AfricaCompass/0.5 (Mahé public transport mapping project; "
            "https://github.com/Larissab-creator/Africa-Compass)"
        )
    }
    last_error: Exception | None = None
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            LOGGER.info("Querying Mahé bus routes from %s", endpoint)
            response = client.post(
                endpoint, data={"data": QUERY}, headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload.get("elements"), list):
                raise ValueError("Overpass response has no elements list")
            RAW_DIR.mkdir(parents=True, exist_ok=True)
            RAW_FILE.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            time.sleep(REQUEST_PAUSE_SECONDS)
            return payload
        except requests.HTTPError as exc:
            last_error = exc
            status = exc.response.status_code if exc.response is not None else None
            LOGGER.warning("%s returned HTTP %s", endpoint, status)
        except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            LOGGER.warning("%s failed: %s", endpoint, exc)
    raise RuntimeError(
        f"All Overpass endpoints failed for bus data. Last error: {last_error}"
    ) from last_error


def _joined_route_geometry(
    relation: dict[str, Any],
    ways: dict[str, dict[str, Any]],
    nodes: dict[str, dict[str, Any]],
) -> list[list[list[float]]]:
    """Assemble ordered relation way members into connected line segments."""
    segments: list[list[list[float]]] = []
    for member in relation.get("members", []):
        if member.get("type") != "way":
            continue
        way = ways.get(str(member.get("ref", "")))
        if not way:
            continue
        coordinates = []
        for node_id in way.get("nodes", []):
            node = nodes.get(str(node_id))
            if node and node.get("lon") is not None and node.get("lat") is not None:
                coordinates.append([float(node["lon"]), float(node["lat"])])
        if len(coordinates) < 2:
            continue
        if member.get("role") in {"backward", "reverse"}:
            coordinates.reverse()

        if not segments:
            segments.append(coordinates)
            continue

        current = segments[-1]
        if current[-1] == coordinates[0]:
            current.extend(coordinates[1:])
        elif current[-1] == coordinates[-1]:
            coordinates.reverse()
            current.extend(coordinates[1:])
        else:
            segments.append(coordinates)

    return [segment for segment in segments if len(segment) >= 2]


def process_bus_elements(
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Create GeoJSON line features for routes and point features for stops.

    Returns route features, stop features, and a route inventory (including
    route relations that currently have stops but no mapped line geometry).
    """
    elements = payload.get("elements", [])
    nodes = {
        str(item["id"]): item
        for item in elements
        if item.get("type") == "node" and item.get("id") is not None
    }
    ways = {
        str(item["id"]): item
        for item in elements
        if item.get("type") == "way" and item.get("id") is not None
    }
    relations = [
        item for item in elements
        if item.get("type") == "relation"
        and (item.get("tags") or {}).get("type") == "route"
        and (item.get("tags") or {}).get("route") == "bus"
    ]

    route_features: list[dict[str, Any]] = []
    route_rows: list[dict[str, Any]] = []
    stop_route_refs: dict[str, set[str]] = {}
    stop_node_ids: set[str] = set()
    stop_name_by_id: dict[str, str] = {}

    for relation in relations:
        tags = relation.get("tags") or {}
        osm_id = str(relation.get("id", ""))
        if not osm_id:
            continue
        ref = str(tags.get("ref", "")).strip()
        name = str(tags.get("name", "")).strip()
        label = ref or name or f"OSM relation {osm_id}"
        relation_stop_ids: list[str] = []
        for member in relation.get("members", []):
            if member.get("type") != "node":
                continue
            node_id = str(member.get("ref", ""))
            role = str(member.get("role", ""))
            node = nodes.get(node_id)
            node_tags = (node or {}).get("tags") or {}
            if role in STOP_ROLES or node_tags.get("highway") == "bus_stop":
                if node_id:
                    relation_stop_ids.append(node_id)
                    stop_node_ids.add(node_id)
                    stop_route_refs.setdefault(node_id, set()).add(label)
                    if node_tags.get("name"):
                        stop_name_by_id[node_id] = str(node_tags["name"])

        segments = _joined_route_geometry(relation, ways, nodes)
        way_count = sum(1 for member in relation.get("members", []) if member.get("type") == "way")
        geometry: dict[str, Any] | None = None
        if len(segments) == 1:
            geometry = {"type": "LineString", "coordinates": segments[0]}
        elif len(segments) > 1:
            geometry = {"type": "MultiLineString", "coordinates": segments}

        properties = {
            "osm_id": osm_id,
            "ref": ref,
            "name": name,
            "from": str(tags.get("from", "")).strip(),
            "to": str(tags.get("to", "")).strip(),
            "operator": str(tags.get("operator", "")).strip(),
            "network": str(tags.get("network", "")).strip(),
            "interval": str(tags.get("interval", "")).strip(),
            "duration": str(tags.get("duration", "")).strip(),
            "way_count": way_count,
            "stop_count": len(set(relation_stop_ids)),
            "geometry_status": "mapped" if geometry else "stops_only",
            "osm_url": f"https://www.openstreetmap.org/relation/{osm_id}",
        }
        route_rows.append(properties)
        if geometry:
            route_features.append({
                "type": "Feature",
                "geometry": geometry,
                "properties": properties,
            })

    # Also include mapped bus-stop nodes even when they are not members of a
    # route relation, so the map can expose stop locations separately.
    for node_id, node in nodes.items():
        tags = node.get("tags") or {}
        is_bus_stop = (
            tags.get("highway") == "bus_stop"
            or tags.get("bus") in {"yes", "designated"}
        )
        if is_bus_stop and node.get("lat") is not None and node.get("lon") is not None:
            stop_node_ids.add(node_id)
            if tags.get("name"):
                stop_name_by_id[node_id] = str(tags["name"])

    stop_features: list[dict[str, Any]] = []
    stop_rows: list[dict[str, Any]] = []
    for node_id in sorted(stop_node_ids, key=lambda value: (0, int(value)) if value.isdigit() else (1, value)):
        node = nodes.get(node_id)
        if not node or node.get("lat") is None or node.get("lon") is None:
            continue
        tags = node.get("tags") or {}
        name = str(tags.get("name") or stop_name_by_id.get(node_id) or "").strip()
        route_refs = sorted(stop_route_refs.get(node_id, set()))
        properties = {
            "osm_id": node_id,
            "name": name,
            "highway": str(tags.get("highway", "")),
            "public_transport": str(tags.get("public_transport", "")),
            "route_refs": route_refs,
            "osm_url": f"https://www.openstreetmap.org/node/{node_id}",
        }
        stop_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(node["lon"]), float(node["lat"])],
            },
            "properties": properties,
        })
        stop_rows.append({
            **properties,
            "route_refs": ";".join(route_refs),
        })

    return route_features, stop_features, route_rows


def run_pipeline() -> dict[str, Path]:
    """Fetch, process and save Mahé bus routes and mapped bus stops."""
    payload = fetch_bus_data()
    route_features, stop_features, route_rows = process_bus_elements(payload)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ROUTES_GEOJSON.write_text(
        json.dumps({"type": "FeatureCollection", "features": route_features}, ensure_ascii=False),
        encoding="utf-8",
    )
    STOPS_GEOJSON.write_text(
        json.dumps({"type": "FeatureCollection", "features": stop_features}, ensure_ascii=False),
        encoding="utf-8",
    )
    pd.DataFrame(route_rows, columns=ROUTE_COLUMNS).to_csv(
        ROUTES_CSV, index=False, encoding="utf-8"
    )
    pd.DataFrame(
        [
            {key: row.get(key, "") for key in STOP_COLUMNS}
            for row in stop_features_to_rows(stop_features)
        ],
        columns=STOP_COLUMNS,
    ).to_csv(STOPS_CSV, index=False, encoding="utf-8")

    LOGGER.info(
        "Mahé bus data complete: %s mapped route lines from %s route relations; %s mapped stops",
        len(route_features), len(route_rows), len(stop_features),
    )
    return {
        "bus_routes_geojson": ROUTES_GEOJSON,
        "bus_stops_geojson": STOPS_GEOJSON,
        "bus_routes_csv": ROUTES_CSV,
        "bus_stops_csv": STOPS_CSV,
    }


def stop_features_to_rows(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten stop feature properties for CSV output."""
    return [feature.get("properties", {}) for feature in features]


if __name__ == "__main__":
    for label, path in run_pipeline().items():
        print(f"{label}: {path}")
