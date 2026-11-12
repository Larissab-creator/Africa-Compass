import pandas as pd

from src import accessibility_analysis as analysis


def test_service_group_classification():
    assert analysis.classify_service_group("hospital") == "healthcare"
    assert analysis.classify_service_group("school") == "education"
    assert analysis.classify_service_group("supermarket") == "food_retail"
    assert analysis.classify_service_group("restaurant") == "other_service"


def test_haversine_distance_is_zero_for_same_point():
    assert analysis.haversine_km(-4.62, 55.45, -4.62, 55.45) == 0


def test_accessibility_analysis_writes_outputs(tmp_path, monkeypatch):
    input_csv = tmp_path / "sample_places.csv"
    processed_dir = tmp_path / "processed"
    output_dir = tmp_path / "outputs"
    sample = pd.DataFrame(
        [
            {"osm_id": "1", "name": "Victoria Hospital", "category": "service", "subcategory": "hospital", "latitude": -4.62, "longitude": 55.45},
            {"osm_id": "2", "name": "School", "category": "service", "subcategory": "school", "latitude": -4.621, "longitude": 55.451},
            {"osm_id": "3", "name": "Market", "category": "service", "subcategory": "supermarket", "latitude": -4.622, "longitude": 55.452},
            {"osm_id": "4", "name": "Bus stop", "category": "transport", "subcategory": "bus_stop", "latitude": -4.623, "longitude": 55.453},
        ]
    )
    sample.to_csv(input_csv, index=False)
    monkeypatch.setattr(analysis, "PROCESSED_DIR", processed_dir)
    monkeypatch.setattr(analysis, "OUTPUT_DIR", output_dir)

    result = analysis.analyse_accessibility(input_csv=input_csv)

    assert all(path.exists() for path in result.values())
    summary = pd.read_csv(result["service_summary"])
    counts = dict(zip(summary["analysis_group"], summary["mapped_locations"]))
    assert counts["healthcare"] == 1
    assert counts["education"] == 1
    assert counts["food_retail"] == 1
    grid = pd.read_csv(result["grid"])
    assert len(grid) > 0
    assert "nearest_healthcare_km" in grid.columns
    assert "nearest_education_km" in grid.columns
    assert "nearest_food_retail_km" in grid.columns
