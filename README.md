# Africa Compass 🌍

**Making local places and routes easier to discover.**

Africa Compass is an interactive mapping project that starts with Mahé, Seychelles. It focuses on the details that can be easy to miss on a map: smaller roads, local access routes, tracks, footpaths, trails and the connections between neighbourhoods and smaller settlements.

The main experience is a searchable map of Mahé's road network. Visitors can explore the island, look up mapped roads, inspect road details and see how the underlying OpenStreetMap data changes over time.

## Why Africa Compass?

Many places across Africa and other parts of the world are represented on digital maps, but the level of detail is not always the same. Smaller communities and local routes can be missing, incomplete, unnamed or difficult to find unless someone zooms in closely or already knows the area.

That can make exploring an unfamiliar place harder than it needs to be. A visitor may find the main road but struggle to identify a smaller lane, a local access road, a track towards a settlement or a footpath leading to a trail.

Africa Compass aims to make these local details easier to see and explore. The longer-term ambition is to bring more attention to places and routes that are less visible in widely used mapping experiences, starting with a practical pilot on Mahé and gradually expanding to other African and Indian Ocean locations.

For visitors to Seychelles, clearer local map detail can make it easier to plan an outing, find routes beyond the main roads and explore the island with less uncertainty. It can also help people who live locally identify gaps or outdated information and contribute corrections.

## The Mahé pilot

The current main product is the **Mahé interactive road map**.

It is designed to help people:

- Search for mapped road names and inspect individual road sections.
- View named and unnamed roads separately.
- Explore different road types, including local roads and access routes.
- Switch on a separate layer for footpaths, tracks and trails.
- Select a road to see available details such as its road type, surface, lanes, one-way information and last recorded OpenStreetMap edit.
- Identify road records that have appeared, changed or disappeared between data snapshots.
- Prepare a report about a missing or incorrect map feature for review and submission through OpenStreetMap.

The map is intended to make local geography easier to explore. It is not currently a turn-by-turn navigation service, and it cannot guarantee that a road or trail is open, safe or suitable for every traveller.

## Weekly data refresh

The Mahé road map is refreshed automatically **every Monday at 03:00 UTC** through GitHub Actions. The workflow can also be started manually.

Each scheduled run:

1. Retrieves the latest available Mahé road and path data from OpenStreetMap using the Overpass API.
2. Processes the road-line geometry and available road attributes.
3. Compares the latest extract with the previous saved snapshot.
4. Records road features that are newly mapped, updated or no longer present in the extract.
5. Builds the interactive map website and publishes it through GitHub Pages.

The first successful run creates the comparison baseline. Later runs can then identify differences from that saved snapshot.

**What the change labels mean:** “Newly mapped” means a road feature has appeared in the latest OpenStreetMap extract; “updated” means its recorded tags, geometry or version have changed; and “no longer in extract” means it was present in the previous snapshot but is absent from the latest one. These labels describe changes in map data. They do not independently prove that a road has physically been built, altered or closed.

The workflow and its run history are available here: [Mahé road-map refresh workflow](https://github.com/Larissab-creator/Africa-Compass/actions/workflows/refresh-mahe-roads.yml).

## Data source

The Mahé road network is sourced from [OpenStreetMap](https://www.openstreetmap.org/), using the Overpass API to retrieve road features and their line geometry for the island.

OpenStreetMap is a collaborative mapping project. Its coverage and level of detail depend on the information contributed and maintained by its community. Africa Compass processes that information into a map experience; it does not independently survey every road or trail.

The earlier Victoria places and services pipeline remains part of the project as a supporting data-exploration pilot. It extracts mapped places and points of interest and supports exploratory service-accessibility analysis. It is separate from the Mahé road-line map.

## Technology

- **Python** – data extraction, processing and validation.
- **OpenStreetMap Overpass API** – source for mapped road and place data.
- **GeoJSON and CSV** – portable formats for road geometry and tabular records.
- **Leaflet** – interactive web mapping.
- **DuckDB** – local analytical storage for the Victoria places dataset.
- **GitHub Actions** – automated weekly refresh, tests and publishing.
- **GitHub Pages** – hosting for the interactive map website.

## Run the project locally

Python 3.10 or newer is recommended. The scheduled GitHub Actions workflow currently uses Python 3.11.

### 1. Clone the repository

```bash
git clone https://github.com/Larissab-creator/Africa-Compass.git
cd Africa-Compass
```

### 2. Create and activate a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Build the Mahé road map

```bash
python src/mahe_roads.py
python src/build_map_site.py
```

The road extraction creates processed road data and an interactive HTML map. The website builder assembles a Pages-ready version of the map in the `_site/` directory.

### 5. Run the supporting Victoria pipeline

```bash
python src/sey_pipeline.py
python src/build_map.py
python src/accessibility_analysis.py
```

This supporting pipeline creates the Victoria places dataset, a places map and exploratory service-accessibility outputs.

### 6. Run the tests

```bash
python -m pytest -q
```

The Overpass API is a public service, so an extraction may occasionally be delayed or unavailable when an endpoint is busy. The road pipeline is configured to try alternative public endpoints.

## Main generated outputs

| File | Purpose |
| --- | --- |
| `data/raw/mahe_roads_overpass.json` | Source response from the Mahé road extract |
| `data/processed/mahe_roads.csv` | Tabular road inventory and attributes |
| `data/processed/mahe_roads.geojson` | Road-line geometry for mapping and GIS |
| `data/processed/mahe_road_changes.csv` | Differences identified between snapshots |
| `data/history/mahe_roads_snapshot.json` | Saved comparison snapshot |
| `outputs/mahe_road_network.html` | Downloadable interactive road map |
| `_site/` | Website files prepared for GitHub Pages |
| `data/processed/africa_compass.duckdb` | DuckDB database for the supporting Victoria dataset |

Generated data files are recreated by running the relevant pipeline or workflow; they are not all stored in the repository by default.

## Project structure

```text
Africa-Compass/
├── .github/
│   └── workflows/
│       ├── refresh-mahe-roads.yml
│       └── refresh-data.yml
├── data/
│   ├── raw/
│   ├── processed/
│   └── history/
├── docs/
│   ├── map/
│   │   └── index.html
│   └── mahe-road-map.md
├── outputs/
├── src/
│   ├── sey_pipeline.py
│   ├── build_map.py
│   ├── accessibility_analysis.py
│   ├── mahe_roads.py
│   └── build_map_site.py
├── tests/
├── requirements.txt
└── README.md
```

## Current limitations and responsible use

- Map completeness depends on what has been added to OpenStreetMap. A missing road name or feature does not necessarily mean the road or path does not exist.
- Weekly refreshes reflect changes in the OpenStreetMap data, not independently verified changes on the ground.
- The map does not currently calculate turn-by-turn routes, journey times, trail conditions or accessibility.
- A mapped footpath or trail should not be assumed to be maintained, open to the public or suitable for every visitor. Check local advice and conditions before setting out.
- The supporting Victoria accessibility analysis uses mapped points and straight-line distances from grid-cell centres. It is exploratory, is not population-weighted and does not represent actual walking or driving times.
- Contact details and opening hours appear only when they have been added to OpenStreetMap. Missing information does not prove that a service is closed or unavailable.

Africa Compass is a discovery and mapping project, not an emergency-services directory or a substitute for local guidance and appropriate navigation.

## Future direction

Mahé is the starting point, not the final boundary. The longer-term direction is to expand the approach to more islands, districts and countries, with attention to local roads, settlement connections, footpaths, trails and places that can be difficult for visitors to discover.

The aim is simple: make it easier to see how places connect, support more confident exploration, and help bring underrepresented local geography into clearer view.

## Data attribution and licence

Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright). OpenStreetMap data is made available under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/).

Africa Compass is an independent project and is not affiliated with the OpenStreetMap Foundation. Any public-facing map or dataset derived from OpenStreetMap must retain the required attribution and comply with the ODbL.
