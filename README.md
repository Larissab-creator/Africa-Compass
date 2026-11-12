# Africa Compass 🌍

Africa Compass is an interactive mapping project focused on Mahé Island, Seychelles. Its main experience is a labelled island map with searchable road lines, selectable road details, separate footpath and trail layers, and a record of changes between OpenStreetMap snapshots.

## Current pilot

The main product is the Mahé road map web app in `docs/map/`. GitHub Actions retrieves the island's full road-line geometry from OpenStreetMap, builds a searchable Leaflet map, publishes it to GitHub Pages, and compares each refresh with a saved snapshot to identify road records newly mapped, updated or no longer present in the extract. The earlier Victoria services dataset remains available as a supporting pilot.

This is an initial technical pilot, not a complete directory of Seychelles. Coverage depends on what is mapped in OpenStreetMap and on the tags used by local contributors.

## Pipeline

1. **Extract** – query the OpenStreetMap Overpass API for named nodes, ways and relations.
2. **Preserve** – save the source response as JSON under `data/raw/`.
3. **Transform** – standardise names, OSM identifiers, coordinates, categories, addresses and available contact details.
4. **Validate** – remove records with missing identifiers, names or coordinates; reject out-of-range coordinates and representative centres outside the Victoria pilot bounding box; remove duplicate OSM objects.
5. **Load** – write a CSV file and a DuckDB table for analysis and visualisation.
6. **Map Mahé roads** – retrieve full road-line geometry for Mahé and preserve road names and road attributes.
7. **Publish the map app** – assemble a responsive Leaflet website with search, selectable road layers, road detail panels and map-issue reporting links.
8. **Track map changes** – compare each road extract with the previous saved snapshot and flag newly mapped, updated and no-longer-present OSM road ways.

### Data categories

- `service`: features tagged with amenity, healthcare, school or shop information.
- `transport`: features tagged with highway, public transport, railway or route information.
- `attraction`: features tagged with tourism, historic, leisure or natural information.
- `place`: other named features.

The category is a practical first-pass classification based on OSM tags. It is not a formal assessment of service quality or availability.

## Getting started

Python 3.10 or newer is recommended.

### 1. Clone the repository

```bash
git clone https://github.com/Larissab-creator/Africa-Compass.git
cd Africa-Compass
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the pipeline

```bash
python src/sey_pipeline.py
```

The script calls public global Overpass API instances. If one host is at capacity or unavailable, the downloader tries the configured alternatives. It needs an internet connection; public instances are best-effort services and may occasionally be busy.

### 5. Build the maps

Run the Mahé road map and website builder:

```bash
python src/mahe_roads.py
python src/build_map_site.py
```

This creates a full-island road inventory and a Pages-ready website in `_site/`. The map uses OpenStreetMap's labelled basemap, with Africa Compass road overlays, search, selectable road details, separate footpaths and trails, and a way to prepare an OpenStreetMap note for a missing or incorrect road.

The Victoria-focused places map and exploratory service analysis can still be generated with:

```bash
python src/sey_pipeline.py
python src/build_map.py
python src/accessibility_analysis.py
```


The Mahé road map and website are refreshed from the [Mahé road-map workflow](https://github.com/Larissab-creator/Africa-Compass/actions/workflows/refresh-mahe-roads.yml). It can be run manually and is scheduled weekly. The first successful snapshot establishes the baseline; later runs compare against it. The workflow publishes the interactive website to GitHub Pages and also packages the map and source data as a downloadable artifact.

### 6. Run the tests

```bash
python -m pytest -q
```

## Generated outputs

The pipeline creates these files when it runs:

| Path | Description |
| --- | --- |
| `data/raw/victoria_osm_raw.json` | Original Overpass API response |
| `data/processed/victoria_places.csv` | Validated, tabular dataset |
| `data/processed/africa_compass.duckdb` | DuckDB database containing the `victoria_places` table |

Generated data files are not committed to the repository by default. Run the pipeline to recreate them.

## Project structure

```text
Africa-Compass/
├── data/
│   ├── raw/
│   ├── processed/
│   └── history/
│       └── mahe_roads_snapshot.json
├── src/
│   ├── sey_pipeline.py
│   ├── build_map.py
│   ├── accessibility_analysis.py
│   ├── mahe_roads.py
│   ├── build_map_site.py
│   └── __init__.py
├── outputs/
│   ├── mahe_road_network.html (generated)
│   └── victoria_interactive_map.html (generated)
├── tests/
│   ├── test_pipeline.py
│   ├── test_accessibility_analysis.py
│   ├── test_mahe_roads.py
│   └── test_map_site.py
├── .github/
│   └── workflows/
│       ├── refresh-mahe-roads.yml
│       └── refresh-data.yml
├── docs/
│   ├── map/
│   │   └── index.html
│   └── mahe-road-map.md
├── requirements.txt
└── README.md
```

## Data source and attribution

Map data is © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) and is made available under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/).

Africa Compass is an independent project and is not affiliated with the OpenStreetMap Foundation. Any public-facing map or dataset derived from OSM should provide the required attribution and comply with the ODbL.

## Current limitations and next steps

- The geographic boundary is currently a small pilot area around Victoria, not all of Mahé or Seychelles. Ways and relations are represented by their OpenStreetMap centre point; records whose centre falls outside the pilot bounding box are excluded from the map dataset.
- The query currently focuses on named OSM features; unnamed roads and facilities are not included.
- Some OSM objects may not have a direct point coordinate. For ways and relations, the pipeline uses the OSM centre coordinate when supplied.
- Contact details and opening hours are included only when mapped in OSM. Missing information does not mean a service is closed or unavailable.
- The service grouping is a first-pass classification of extracted OSM tags and requires local validation.
- The 500m grid is not population-weighted and contains coastal and non-residential cells. Nearest-facility distances are straight-line calculations from grid-cell centres, not walking/driving network distances or travel times.

Planned work includes improving road-name coverage, validating road changes, adding a road-update review process, and gradually expanding the mapped features beyond Mahé.

**Important:** Africa Compass is a discovery and data-analysis prototype, not an emergency-services directory, navigation system or guarantee that a listed place is open or operational.
