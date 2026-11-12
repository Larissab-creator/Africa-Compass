# Mahé Island road map

## Product direction

Africa Compass is being developed as an interactive geographical map, not a slide deck or a chart-first dashboard. The main Mahé view should show the island-wide road network, readable existing road labels, and a clear way to inspect road segments.

## Data source and geography

The road inventory is queried from OpenStreetMap using Mahé Island's OSM relation (relation ID 9435209) and its corresponding Overpass area. The query retrieves OSM ways tagged with `highway` and uses `out meta geom` so the full road-line geometry, OSM version and edit timestamp are preserved.

This is important: the Victoria point pipeline uses representative centre points for ways and relations. Those centre points are not suitable for drawing roads as lines. The Mahé road pipeline is a separate, geometry-preserving extraction.

## What appears on the map

- **Roads and streets:** line geometry styled by OpenStreetMap road class, including smaller access roads and service roads.
- **Footpaths and trails:** a separate layer for mapped paths, cycleways, bridleways and steps.
- **Hover labels:** hovering over roads and paths displays the mapped name and feature type. If no name is recorded, the map displays an explicit unnamed label rather than guessing.
- **Bus routes:** route lines are assembled from OpenStreetMap route=bus relations where those relations and their member ways are mapped.
- **Bus stops:** mapped bus-stop nodes and public-transport platforms are shown as a separate layer. Stops are linked to route numbers when the OSM route relation identifies them.
- **Newly mapped and updated roads:** road ways are compared with the previous saved snapshot.

Selecting a road displays available road attributes. Selecting a bus route shows its route reference, mapped start and destination, operator and stop count. Selecting a bus stop shows its name and any linked route references.

## What “new road” means

Africa Compass will use careful status labels:

- **Newly mapped** means this OSM road way appeared in the latest Africa Compass snapshot but not the previous one.
- **Updated** means the OSM way's version, tags or geometry changed since the previous snapshot.
- **No longer in extract** means the way was in the previous snapshot but is absent from the current query result.

These are data-change indicators, not proof of physical construction, resurfacing, closure or demolition. A real-world road construction tracker would need additional verified sources such as official public works notices, planning records or field reports.

## Snapshot history

The refresh workflow saves `data/history/mahe_roads_snapshot.json` to the repository after each run. The first run establishes the baseline. The scheduled workflow refreshes the road inventory and bus route/stop extracts every Monday at 03:00 UTC. Later runs compare the road data with the saved baseline.

## Outputs

| Output | Purpose |
|---|---|
| `outputs/mahe_road_network.html` | Downloadable interactive island-wide road map |
| `docs/map/index.html` | Source for the Africa Compass interactive web app |
| `_site/` | Pages-ready site assembled during the workflow |
| `data/processed/mahe_roads.csv` | Road inventory and attributes |
| `data/processed/mahe_roads.geojson` | Full line geometry for web maps and GIS |
| `data/processed/mahe_road_changes.csv` | Newly mapped, updated and no-longer-in-extract ways |
| `data/history/mahe_roads_snapshot.json` | Compact comparison baseline for future refreshes |
| `data/processed/mahe_bus_routes.geojson` | Mapped bus route line geometry |
| `data/processed/mahe_bus_stops.geojson` | Mapped bus stop and platform locations |
| `data/processed/mahe_bus_routes.csv` | Bus route inventory and attributes |
| `data/processed/mahe_bus_stops.csv` | Bus stop inventory and mapped route references |

## Web map experience

The public-facing app lives in `docs/map/index.html` and is assembled by `src/build_map_site.py`. It provides search across roads, bus routes and bus stops; separate map layers for roads, paths, bus routes and stops; hover labels for mapped road and path names; selectable feature details; data downloads; and a hand-off to OpenStreetMap Notes for map corrections. Current timetables and service information should be checked with the [Seychelles Public Transport Corporation](https://sptc.sc/timetable/). The issue-report action copies the description and map-centre coordinates; the user reviews and submits the note on OpenStreetMap. Africa Compass does not collect or submit reports itself.

The site is published using GitHub Pages from the `refresh-mahe-roads.yml` workflow. For the first deployment, enable Pages in repository settings: **Settings → Pages → Build and deployment → Source → GitHub Actions**. Once enabled, the workflow builds the map data, uploads the website artifact and deploys the site.

The interactive app uses Leaflet with the OpenStreetMap standard tile layer as its labelled basemap. Its road overlays are generated from the separate full-geometry GeoJSON inventory. The map requests tiles only for the area a visitor is currently viewing; it does not bulk-download or prefetch map tiles.

## Attribution and licensing

Map data © OpenStreetMap contributors. OpenStreetMap data is made available under the Open Database License (ODbL). Display required attribution on the map and link to https://www.openstreetmap.org/copyright. Any redistribution of OSM-derived databases must comply with the ODbL.

## Current limitations

- Road names, mapped paths, bus route relations and bus stops reflect OpenStreetMap coverage and tagging at the time of the snapshot. Bus route lines may be incomplete where route relations or member ways have not been mapped.
- An unnamed road is not necessarily a new or unrecognised road; its name may simply not be mapped.
- Bus route lines are only drawn for mapped OSM bus route relations. No line is inferred from a route number or timetable. For current departure times and service updates, consult SPTC and its travel app.
- Changes in OSM are community data edits and are not independent confirmation of a change on the ground.
- The initial saved snapshot is a baseline. Newly mapped and updated status indicators become meaningful from the second successful snapshot onward.
- The first GitHub Pages deployment requires Pages to be enabled with the source set to GitHub Actions in repository settings.
