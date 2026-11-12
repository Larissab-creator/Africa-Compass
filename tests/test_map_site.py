import json

from src import build_map_site


def test_build_site_copies_map_data_and_creates_metadata(tmp_path, monkeypatch):
    source_geojson = tmp_path / "roads.geojson"
    source_geojson.write_text(
        json.dumps({
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[55.45, -4.62], [55.451, -4.621]]},
                 "properties": {"name": "Victoria Road", "road_status": "baseline"}},
                {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[55.46, -4.63], [55.461, -4.631]]},
                 "properties": {"name": "", "road_status": "baseline"}},
            ],
        }),
        encoding="utf-8",
    )
    source_snapshot = tmp_path / "snapshot.json"
    source_snapshot.write_text(
        json.dumps({"snapshot_created_utc": "2026-11-12T21:00:00Z", "osm_relation_id": 9435209}),
        encoding="utf-8",
    )
    roads_csv = tmp_path / "roads.csv"
    roads_csv.write_text("osm_id,name\n1,Victoria Road\n", encoding="utf-8")
    changes_csv = tmp_path / "changes.csv"
    changes_csv.write_text("osm_id,change_type\n", encoding="utf-8")
    html = tmp_path / "index.html"
    html.write_text("<html>test</html>", encoding="utf-8")
    site = tmp_path / "_site"

    monkeypatch.setattr(build_map_site, "SOURCE_GEOJSON", source_geojson)
    monkeypatch.setattr(build_map_site, "SOURCE_SNAPSHOT", source_snapshot)
    monkeypatch.setattr(build_map_site, "SOURCE_ROADS_CSV", roads_csv)
    monkeypatch.setattr(build_map_site, "SOURCE_CHANGES_CSV", changes_csv)
    monkeypatch.setattr(build_map_site, "SOURCE_HTML", html)
    monkeypatch.setattr(build_map_site, "SITE_DIR", site)
    monkeypatch.setattr(build_map_site, "SITE_DATA_DIR", site / "data")

    outputs = build_map_site.build_site()

    assert all(path.exists() for path in outputs.values())
    metadata = json.loads(outputs["metadata"].read_text(encoding="utf-8"))
    assert metadata["road_feature_count"] == 2
    assert metadata["named_road_feature_count"] == 1
    assert metadata["baseline_established"] is True
    assert metadata["snapshot_created_utc"] == "2026-11-12T21:00:00Z"
