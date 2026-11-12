"""Explore mapped-service patterns across the Africa Compass Victoria pilot.

All indicators describe OpenStreetMap records. Grid distances are straight-line
haversine distances from approximate 500m cell centres, not road-network routes,
travel times, population-weighted access, or confirmation that a service is open.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import folium
import pandas as pd
from folium.plugins import MarkerCluster

ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = ROOT / "data" / "processed" / "victoria_places.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "outputs"

# Keep aligned with the extraction boundary in sey_pipeline.py.
SOUTH, WEST, NORTH, EAST = (-4.64, 55.43, -4.60, 55.47)
GRID_SIZE_METRES = 500
EARTH_RADIUS_KM = 6371.0088

GROUP_BY_SUBCATEGORY = {
    "hospital": "healthcare", "clinic": "healthcare", "doctors": "healthcare",
    "pharmacy": "healthcare", "dentist": "healthcare", "healthcare": "healthcare",
    "school": "education", "kindergarten": "education", "childcare": "education",
    "college": "education", "university": "education",
    "supermarket": "food_retail", "convenience": "food_retail",
    "butcher": "food_retail", "marketplace": "food_retail", "bakery": "food_retail",
    "greengrocer": "food_retail", "farm": "food_retail", "wholesale": "food_retail",
    "bank": "finance", "atm": "finance", "bureau_de_change": "finance",
    "police": "civic_safety", "fire_station": "civic_safety",
    "townhall": "civic_safety", "post_office": "civic_safety",
    "community_centre": "civic_safety", "public_building": "civic_safety",
    "outpost": "civic_safety",
    "ferry_terminal": "public_transport", "bus_station": "public_transport",
}
GROUP_LABELS = {
    "healthcare": "Healthcare",
    "education": "Education and childcare",
    "food_retail": "Food retail",
    "finance": "Financial services",
    "civic_safety": "Civic and safety services",
    "public_transport": "Public transport facilities",
    "other_service": "Other mapped services",
}
DISTANCE_GROUPS = ("healthcare", "education", "food_retail")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two latitude/longitude pairs, in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def classify_service_group(subcategory: object) -> str:
    """Group an extracted OSM subcategory for exploratory analysis."""
    key = "" if pd.isna(subcategory) else str(subcategory).strip().lower()
    return GROUP_BY_SUBCATEGORY.get(key, "other_service")


def _grid_parameters() -> tuple[float, float, int, int]:
    """Approximate 500m grid steps and number of rows/columns."""
    lat_step = GRID_SIZE_METRES / 111_320
    mid_lat = (SOUTH + NORTH) / 2
    lon_step = GRID_SIZE_METRES / (111_320 * math.cos(math.radians(mid_lat)))
    return (
        lat_step, lon_step,
        math.ceil((NORTH - SOUTH) / lat_step),
        math.ceil((EAST - WEST) / lon_step),
    )


def make_accessibility_grid(features: pd.DataFrame) -> pd.DataFrame:
    """Build cell counts and straight-line distances to selected mapped services."""
    lat_step, lon_step, n_rows, n_cols = _grid_parameters()
    cells = []
    for row in range(n_rows):
        south = SOUTH + row * lat_step
        north = min(SOUTH + (row + 1) * lat_step, NORTH)
        for col in range(n_cols):
            west = WEST + col * lon_step
            east = min(WEST + (col + 1) * lon_step, EAST)
            cells.append({
                "grid_id": f"V{row + 1:02d}_{col + 1:02d}",
                "row": row, "column": col,
                "south": south, "west": west, "north": north, "east": east,
                "latitude": (south + north) / 2,
                "longitude": (west + east) / 2,
            })
    grid = pd.DataFrame(cells)

    work = features.copy()
    work["_row"] = ((work["latitude"] - SOUTH) / lat_step).astype(int).clip(0, n_rows - 1)
    work["_col"] = ((work["longitude"] - WEST) / lon_step).astype(int).clip(0, n_cols - 1)
    work["analysis_group"] = work["subcategory"].map(classify_service_group)
    work["is_bus_stop"] = (
        work["category"].eq("transport") & work["subcategory"].eq("bus_stop")
    ).astype(int)

    all_counts = work.groupby(["_row", "_col"]).size().rename("mapped_feature_count")
    service_counts = (
        work[work["category"].eq("service")]
        .groupby(["_row", "_col"]).size().rename("mapped_service_count")
    )
    bus_counts = (
        work.groupby(["_row", "_col"])["is_bus_stop"]
        .sum().rename("mapped_bus_stop_count")
    )
    service_groups = (
        work[work["category"].eq("service")]
        .pivot_table(index=["_row", "_col"], columns="analysis_group",
                     values="osm_id", aggfunc="count", fill_value=0)
        .add_prefix("service_")
    )

    grid = grid.join(all_counts, on=["row", "column"])
    grid = grid.join(service_counts, on=["row", "column"])
    grid = grid.join(bus_counts, on=["row", "column"])
    if not service_groups.empty:
        service_groups.index.names = ["row", "column"]
        grid = grid.join(service_groups, on=["row", "column"])
    count_cols = [
        c for c in grid.columns
        if c.endswith("_count") or c.startswith("service_")
    ]
    grid[count_cols] = grid[count_cols].fillna(0).astype(int)

    for group in DISTANCE_GROUPS:
        points = work.loc[
            work["category"].eq("service") & work["analysis_group"].eq(group),
            ["latitude", "longitude"],
        ].dropna().to_numpy()
        distance_col = f"nearest_{group}_km"
        if len(points) == 0:
            grid[distance_col] = pd.NA
        else:
            distances = [
                min(haversine_km(lat, lon, p[0], p[1]) for p in points)
                for lat, lon in grid[["latitude", "longitude"]].itertuples(index=False, name=None)
            ]
            grid[distance_col] = [round(value, 3) for value in distances]

    bus_points = work.loc[
        work["category"].eq("transport") & work["subcategory"].eq("bus_stop"),
        ["latitude", "longitude"],
    ].dropna().to_numpy()
    if len(bus_points) == 0:
        grid["nearest_bus_stop_km"] = pd.NA
    else:
        bus_distances = [
            min(haversine_km(lat, lon, p[0], p[1]) for p in bus_points)
            for lat, lon in grid[["latitude", "longitude"]].itertuples(index=False, name=None)
        ]
        grid["nearest_bus_stop_km"] = [round(value, 3) for value in bus_distances]

    for col in ("mapped_feature_count", "mapped_service_count", "mapped_bus_stop_count"):
        grid[col] = grid[col].fillna(0).astype(int)
    return grid


def analyse_accessibility(input_csv: str | Path = INPUT_CSV) -> dict[str, Path]:
    """Write Flourish-ready CSVs, metrics JSON and a layered HTML map."""
    source = Path(input_csv)
    if not source.exists():
        raise FileNotFoundError(f"Processed input CSV not found: {source}")
    features = pd.read_csv(source)
    required = {
        "osm_id", "name", "category", "subcategory", "latitude", "longitude"
    }
    missing = required.difference(features.columns)
    if missing:
        raise ValueError(f"Input CSV missing required columns: {', '.join(sorted(missing))}")

    features["analysis_group"] = features["subcategory"].map(classify_service_group)
    services = features[features["category"].eq("service")].copy()
    services["analysis_group_label"] = services["analysis_group"].map(GROUP_LABELS)
    summary = (
        services.groupby(["analysis_group", "analysis_group_label"], as_index=False)
        .agg(mapped_locations=("osm_id", "count"))
        .sort_values("mapped_locations", ascending=False)
    )
    total_services = len(services)
    summary["share_of_mapped_services_pct"] = (
        (summary["mapped_locations"] / total_services * 100).round(1)
        if total_services else 0.0
    )
    subcategory_summary = (
        services.groupby(["subcategory", "analysis_group", "analysis_group_label"], as_index=False)
        .agg(mapped_locations=("osm_id", "count"))
        .sort_values("mapped_locations", ascending=False)
    )
    subcategory_summary["share_of_mapped_services_pct"] = (
        (subcategory_summary["mapped_locations"] / total_services * 100).round(1)
        if total_services else 0.0
    )
    grid = make_accessibility_grid(features)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "service_points": PROCESSED_DIR / "victoria_service_points.csv",
        "service_summary": PROCESSED_DIR / "victoria_service_summary.csv",
        "subcategory_summary": PROCESSED_DIR / "victoria_service_subcategory_summary.csv",
        "grid": PROCESSED_DIR / "victoria_accessibility_grid_500m.csv",
        "metrics": PROCESSED_DIR / "victoria_accessibility_metrics.json",
        "map": OUTPUT_DIR / "victoria_service_accessibility_map.html",
    }
    services.to_csv(paths["service_points"], index=False)
    summary.to_csv(paths["service_summary"], index=False)
    subcategory_summary.to_csv(paths["subcategory_summary"], index=False)
    grid.to_csv(paths["grid"], index=False)

    metrics = {
        "pilot": "Victoria, Mahe, Seychelles",
        "source": "OpenStreetMap contributors",
        "total_mapped_features": int(len(features)),
        "mapped_service_locations": int(total_services),
        "mapped_bus_stops": int(
            (features["category"].eq("transport") &
             features["subcategory"].eq("bus_stop")).sum()
        ),
        "grid_cell_size_m_approx": GRID_SIZE_METRES,
        "grid_cells": int(len(grid)),
        "grid_cells_with_mapped_services": int((grid["mapped_service_count"] > 0).sum()),
        "groups": {
            row.analysis_group: int(row.mapped_locations)
            for row in summary.itertuples()
        },
        "grid_proximity": {
            group: {
                "median_distance_km": round(float(grid[f"nearest_{group}_km"].median()), 3),
                "cells_within_500m": int((grid[f"nearest_{group}_km"] <= 0.5).sum()),
                "share_of_grid_cells_within_500m_pct": round(
                    float((grid[f"nearest_{group}_km"] <= 0.5).mean() * 100), 1
                ),
            }
            for group in ("healthcare", "education", "food_retail", "bus_stop")
        },
        "distance_method": (
            "Straight-line haversine distance from grid-cell centre to nearest "
            "mapped point in the selected group."
        ),
        "limitations": [
            "Grid cells are not population-weighted and include non-residential and coastal areas.",
            "Distances are straight-line approximations, not walking/driving routes or travel times.",
            "OpenStreetMap coverage and tagging may be incomplete or out of date.",
            "A mapped feature is not proof that a service is currently operating or available.",
        ],
    }
    paths["metrics"].write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    centre = [float(features["latitude"].median()), float(features["longitude"].median())]
    fmap = folium.Map(location=centre, zoom_start=14, control_scale=True)
    grid_layer = folium.FeatureGroup(
        name="Approx. 500m grid: mapped service counts", show=True
    )
    max_count = max(int(grid["mapped_service_count"].max()), 1)
    for cell in grid.itertuples(index=False):
        count = int(cell.mapped_service_count)
        intensity = count / max_count
        fill = (
            "#fff5f0" if count == 0 else
            "#fcbba1" if intensity < 0.34 else
            "#fb6a4a" if intensity < 0.67 else "#cb181d"
        )
        popup = (
            f"<b>{cell.grid_id}</b><br>Mapped services: {count}"
            f"<br>Bus stops: {int(cell.mapped_bus_stop_count)}"
            f"<br>All mapped features: {int(cell.mapped_feature_count)}"
        )
        folium.Rectangle(
            bounds=[[cell.south, cell.west], [cell.north, cell.east]],
            color="#555555", weight=0.5, fill=True,
            fill_color=fill, fill_opacity=0.48,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(grid_layer)
    grid_layer.add_to(fmap)

    marker_colours = {
        "healthcare": "red", "education": "blue", "food_retail": "green",
        "finance": "purple", "civic_safety": "darkred",
        "public_transport": "cadetblue", "other_service": "gray",
    }
    for group, subset in services.groupby("analysis_group"):
        layer = folium.FeatureGroup(name=GROUP_LABELS[group], show=True)
        cluster = MarkerCluster().add_to(layer)
        for rec in subset.itertuples(index=False):
            name = str(rec.name).replace("<", "&lt;").replace(">", "&gt;")
            subcategory = str(rec.subcategory).replace("<", "&lt;").replace(">", "&gt;")
            folium.Marker(
                [float(rec.latitude), float(rec.longitude)],
                tooltip=name,
                popup=f"<b>{name}</b><br>{GROUP_LABELS[group]}<br>OSM tag: {subcategory}",
                icon=folium.Icon(color=marker_colours.get(group, "gray"), icon="info-sign"),
            ).add_to(cluster)
        layer.add_to(fmap)
    folium.LayerControl(collapsed=False).add_to(fmap)
    fmap.save(str(paths["map"]))
    return paths


if __name__ == "__main__":
    for name, path in analyse_accessibility().items():
        print(f"{name}: {path}")
