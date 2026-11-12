"""Build an interactive Folium map from the processed Africa Compass CSV."""

from __future__ import annotations

import html
from pathlib import Path
from urllib.parse import urlparse

import folium
import pandas as pd
from folium.plugins import MarkerCluster

ROOT = Path(__file__).resolve().parents[1]
CSV_FILE = ROOT / "data" / "processed" / "victoria_places.csv"
OUTPUT_FILE = ROOT / "outputs" / "victoria_interactive_map.html"

CATEGORY_COLORS = {
    "service": "#D1495B",
    "transport": "#00798C",
    "attraction": "#EDAe49",
    "place": "#30638E",
}
REQUIRED_COLUMNS = {"name", "category", "latitude", "longitude"}


def _safe_website(value: object) -> str | None:
    """Return a safe HTTP(S) URL, or None for untrusted/invalid values."""
    if pd.isna(value):
        return None
    url = str(value).strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return url


def build_map(
    input_csv: str | Path = CSV_FILE,
    output_html: str | Path = OUTPUT_FILE,
) -> Path:
    """Create a layered interactive map from a validated CSV dataset."""
    input_path = Path(input_csv)
    output_path = Path(output_html)
    if not input_path.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {input_path}. Run src/sey_pipeline.py first."
        )

    df = pd.read_csv(input_path)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

    df = df.copy()
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["name", "latitude", "longitude"])
    df = df[df["latitude"].between(-90, 90) & df["longitude"].between(-180, 180)]
    if df.empty:
        raise ValueError("No valid named locations with usable coordinates were found.")

    df["category"] = df["category"].fillna("place").astype(str).str.lower()
    centre = [float(df["latitude"].median()), float(df["longitude"].median())]
    map_view = folium.Map(
        location=centre,
        zoom_start=14,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    for category in sorted(df["category"].unique()):
        category_df = df[df["category"] == category]
        colour = CATEGORY_COLORS.get(category, "#6C757D")
        layer = folium.FeatureGroup(
            name=f"{category.title()} ({len(category_df)})",
            show=True,
        )
        cluster = MarkerCluster().add_to(layer)

        for _, record in category_df.iterrows():
            name = html.escape(str(record["name"]))
            subcategory = html.escape(str(record.get("subcategory", "") or ""))
            address = html.escape(str(record.get("address", "") or ""))
            phone = html.escape(str(record.get("phone", "") or ""))
            opening_hours = html.escape(str(record.get("opening_hours", "") or ""))

            details = [f"<b>{name}</b>", f"Category: {html.escape(category)}"]
            if subcategory and subcategory.lower() != "nan":
                details.append(f"Type: {subcategory}")
            if address and address.lower() != "nan":
                details.append(f"Address: {address}")
            if phone and phone.lower() != "nan":
                details.append(f"Phone: {phone}")
            if opening_hours and opening_hours.lower() != "nan":
                details.append(f"Opening hours: {opening_hours}")

            website = _safe_website(record.get("website"))
            if website:
                safe_url = html.escape(website, quote=True)
                details.append(
                    f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">Website</a>'
                )

            popup_html = "<br>".join(details)
            folium.CircleMarker(
                location=[float(record["latitude"]), float(record["longitude"])],
                radius=6,
                color=colour,
                weight=1,
                fill=True,
                fill_color=colour,
                fill_opacity=0.8,
                tooltip=name,
                popup=folium.Popup(popup_html, max_width=320),
            ).add_to(cluster)

        layer.add_to(map_view)

    bounds = [
        [float(df["latitude"].min()), float(df["longitude"].min())],
        [float(df["latitude"].max()), float(df["longitude"].max())],
    ]
    map_view.fit_bounds(bounds, padding=(24, 24))
    folium.LayerControl(collapsed=False).add_to(map_view)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    map_view.save(str(output_path))
    return output_path


if __name__ == "__main__":
    result = build_map()
    print(f"Interactive map saved to: {result}")
