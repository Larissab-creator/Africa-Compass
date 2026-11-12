from pathlib import Path

from src import mahe_roads


def make_way(osm_id, name, version=1, lat1=-4.62, lon1=55.45, lat2=-4.621, lon2=55.451):
    return {
        "type": "way",
        "id": osm_id,
        "version": version,
        "timestamp": "2026-11-12T12:00:00Z",
        "tags": {"highway": "residential", "name": name, "surface": "asphalt"},
        "geometry": [
            {"lat": lat1, "lon": lon1},
            {"lat": lat2, "lon": lon2},
        ],
    }


def test_first_road_snapshot_marks_all_roads_as_baseline():
    payload = {"elements": [make_way(1001, "North Road"), make_way(1002, "South Road")]}

    features, snapshot, changes = mahe_roads.process_road_elements(payload)

    assert len(features) == 2
    assert {f["properties"]["road_status"] for f in features} == {"baseline"}
    assert snapshot["way_count"] == 2
    assert changes == []
    assert features[0]["geometry"]["coordinates"][0] == [55.45, -4.62]
    assert features[0]["properties"]["version"] == 1
    assert features[0]["properties"]["last_edited_utc"] == "2026-11-12T12:00:00Z"


def test_road_snapshot_detects_new_updated_existing_and_missing():
    baseline_payload = {
        "elements": [
            make_way(1001, "Existing Road"),
            make_way(1002, "Updated Road"),
        ]
    }
    _, previous, _ = mahe_roads.process_road_elements(baseline_payload)
    previous["ways"]["1003"] = {
        "version": 1, "signature": "previous", "name": "Removed from extract"
    }

    payload = {
        "elements": [
            make_way(1001, "Existing Road"),
            make_way(1002, "Updated Road", version=2, lat2=-4.622),
            make_way(1004, "Newly Mapped Road"),
        ]
    }

    features, snapshot, changes = mahe_roads.process_road_elements(payload, previous)
    statuses = {f["properties"]["osm_id"]: f["properties"]["road_status"] for f in features}
    change_types = {row["osm_id"]: row["change_type"] for row in changes}

    assert statuses["1001"] == "existing"
    assert statuses["1002"] == "updated"
    assert statuses["1004"] == "newly_mapped"
    assert change_types["1003"] == "no_longer_in_extract"
    assert snapshot["way_count"] == 3


def test_build_road_map_creates_html(tmp_path):
    payload = {"elements": [make_way(2001, "Victoria Road")]}
    features, _, _ = mahe_roads.process_road_elements(payload)
    output = tmp_path / "mahe_roads.html"

    result = mahe_roads.build_road_map(features, output)

    assert result == output
    assert output.exists()
    html = output.read_text(encoding="utf-8")
    assert "AFRICA COMPASS" in html
    assert "Mahé Island" in html
    assert "Victoria Road" in html
