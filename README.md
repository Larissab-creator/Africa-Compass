# Africa Compass 🌍

Africa Compass is an open-data mapping and data-engineering project that helps people discover places, essential services and transport options. The first pilot focuses on Victoria, Mahé, Seychelles, with a longer-term goal of expanding to other African and Indian Ocean countries.

## Current pilot

The current Python pipeline retrieves named OpenStreetMap (OSM) features within a small bounding box around Victoria. It preserves the original API response, standardises useful fields, performs basic quality checks, and writes analysis-ready CSV and DuckDB outputs.

This is an initial technical pilot, not a complete directory of Seychelles. Coverage depends on what is mapped in OpenStreetMap and on the tags used by local contributors.

## Pipeline

1. **Extract** – query the OpenStreetMap Overpass API for named nodes, ways and relations.
2. **Preserve** – save the source response as JSON under `data/raw/`.
3. **Transform** – standardise names, OSM identifiers, coordinates, categories, addresses and available contact details.
4. **Validate** – remove records with missing identifiers, names or coordinates; reject out-of-range coordinates; remove duplicate OSM objects.
5. **Load** – write a CSV file and a DuckDB table for analysis and visualisation.
6. **Visualise** – build an interactive Folium map with switchable category layers.

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

The script calls the public Overpass API. It needs an internet connection and may take a little time if the service is busy.

### 5. Build the interactive map

After the pipeline has created the processed CSV, run:

```bash
python src/build_map.py
```

The interactive HTML map is saved to `outputs/victoria_interactive_map.html`. Open that file in a web browser.

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
│   └── processed/
├── src/
│   ├── sey_pipeline.py
│   ├── build_map.py
│   └── __init__.py
├── outputs/
│   └── victoria_interactive_map.html (generated)
├── tests/
│   └── test_pipeline.py
├── requirements.txt
└── README.md
```

## Data source and attribution

Map data is © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) and is made available under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/).

Africa Compass is an independent project and is not affiliated with the OpenStreetMap Foundation. Any public-facing map or dataset derived from OSM should provide the required attribution and comply with the ODbL.

## Current limitations and next steps

- The geographic boundary is currently a small pilot area around Victoria, not all of Mahé or Seychelles.
- The query currently focuses on named OSM features; unnamed roads and facilities are not included.
- Some OSM objects may not have a direct point coordinate. For ways and relations, the pipeline uses the OSM centre coordinate when supplied.
- Contact details and opening hours are included only when mapped in OSM. Missing information does not mean a service is closed or unavailable.
- The classification rules will need refinement and local validation before broader use.

Planned work includes expanding the geographic coverage, improving service classification and quality checks, adding an interactive map, and building analytical visualisations.

**Important:** Africa Compass is a discovery and data-analysis prototype, not an emergency-services directory, navigation system or guarantee that a listed place is open or operational.
