import pandas as pd

from src import sey_pipeline as pipeline


def test_transform_features_extracts_named_node_and_way():
    payload = {
        "elements": [
            {
                "type": "node",
                "id": 101,
                "lat": -4.62,
                "lon": 55.45,
                "tags": {"name": "Victoria Hospital", "amenity": "hospital"},
            },
            {
                "type": "way",
                "id": 202,
                "center": {"lat": -4.621, "lon": 55.451},
                "tags": {"name": "Independence Avenue", "highway": "residential"},
            },
            {"type": "node", "id": 303, "lat": -4.62, "lon": 55.45, "tags": {}},
        ]
    }

    result = pipeline.transform_features(payload)

    assert len(result) == 2
    hospital = result.loc[result["name"] == "Victoria Hospital"].iloc[0]
    road = result.loc[result["name"] == "Independence Avenue"].iloc[0]
    assert hospital["category"] == "service"
    assert hospital["subcategory"] == "hospital"
    assert road["category"] == "transport"
    assert road["latitude"] == -4.621


def test_validate_features_removes_bad_duplicate_and_out_of_area_records():
    sample = pd.DataFrame(
        [
            {"osm_id": "1", "osm_type": "node", "name": "A", "latitude": -4.62, "longitude": 55.45},
            {"osm_id": "1", "osm_type": "node", "name": "A duplicate", "latitude": -4.62, "longitude": 55.45},
            {"osm_id": "", "osm_type": "node", "name": "Blank ID", "latitude": -4.62, "longitude": 55.45},
            {"osm_id": "3", "osm_type": "way", "name": "Bad latitude", "latitude": 120, "longitude": 55.45},
            {"osm_id": "4", "osm_type": "way", "name": "Missing coordinates", "latitude": None, "longitude": 55.45},
            {"osm_id": "5", "osm_type": "relation", "name": "Outside Victoria", "latitude": -4.50, "longitude": 55.45},
        ]
    )

    result = pipeline.validate_features(sample)

    assert len(result) == 1
    assert result.iloc[0]["osm_id"] == "1"
    assert result.iloc[0]["name"] == "A"


def test_save_outputs_writes_csv_and_duckdb(tmp_path, monkeypatch):
    csv_path = tmp_path / "victoria_places.csv"
    db_path = tmp_path / "africa_compass.duckdb"
    monkeypatch.setattr(pipeline, "PROCESSED_DIR", tmp_path)
    monkeypatch.setattr(pipeline, "CSV_FILE", csv_path)
    monkeypatch.setattr(pipeline, "DB_FILE", db_path)

    sample = pd.DataFrame(
        [{"osm_id": "10", "osm_type": "node", "name": "Test Place", "category": "place"}]
    )
    pipeline.save_outputs(sample)

    assert csv_path.exists()
    assert db_path.exists()
    import duckdb

    with duckdb.connect(str(db_path), read_only=True) as connection:
        count = connection.execute("SELECT COUNT(*) FROM victoria_places").fetchone()[0]
    assert count == 1


def test_build_map_creates_interactive_html(tmp_path):
    from src.build_map import build_map

    input_csv = tmp_path / "places.csv"
    output_html = tmp_path / "map.html"
    pd.DataFrame(
        [
            {"name": "Victoria Hospital", "category": "service", "subcategory": "hospital",
             "latitude": -4.62, "longitude": 55.45, "address": "Victoria",
             "phone": "", "opening_hours": "", "website": ""},
            {"name": "Independence Avenue", "category": "transport", "subcategory": "residential",
             "latitude": -4.621, "longitude": 55.451, "address": "",
             "phone": "", "opening_hours": "", "website": ""},
        ]
    ).to_csv(input_csv, index=False)

    result = build_map(input_csv=input_csv, output_html=output_html)

    assert result == output_html
    assert output_html.exists()
    html_content = output_html.read_text(encoding="utf-8")
    assert "Victoria Hospital" in html_content
    assert "Service (1)" in html_content
    assert "Transport (1)" in html_content


def test_fetch_map_data_fails_over_to_second_overpass_endpoint(tmp_path, monkeypatch):
    class FakeResponse:
        def __init__(self, status_code, payload=None):
            self.status_code = status_code
            self.payload = payload or {}

        def raise_for_status(self):
            if self.status_code >= 400:
                error = pipeline.requests.HTTPError(f"HTTP {self.status_code}")
                error.response = self
                raise error

        def json(self):
            return self.payload

    class FakeSession:
        def __init__(self):
            self.urls = []

        def post(self, url, **kwargs):
            self.urls.append(url)
            if len(self.urls) == 1:
                return FakeResponse(502)
            return FakeResponse(200, {"elements": [{"type": "node", "id": 1}]})

    endpoints = ["https://primary.example/api/interpreter", "https://fallback.example/api/interpreter"]
    monkeypatch.setattr(pipeline, "OVERPASS_ENDPOINTS", endpoints)
    monkeypatch.setattr(pipeline, "RAW_DIR", tmp_path)
    monkeypatch.setattr(pipeline, "RAW_FILE", tmp_path / "raw.json")
    monkeypatch.setattr(pipeline, "SLEEP_SECONDS", 0)
    monkeypatch.setattr(pipeline.time, "sleep", lambda seconds: None)
    session = FakeSession()

    result = pipeline.fetch_map_data(retries=1, session=session)

    assert session.urls == endpoints
    assert result["elements"][0]["id"] == 1
    assert (tmp_path / "raw.json").exists()
