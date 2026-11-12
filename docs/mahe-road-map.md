# Mahé Island road map

## Product direction

Africa Compass is being developed as an interactive geographical map, not a slide deck or a chart-first dashboard. The main Mahé view should show the island-wide road network, readable existing road labels, and a clear way to inspect road segments.

## Data source and geography

The road inventory is queried from OpenStreetMap using Mahé Island's OSM relation (relation ID 9435209) and its corresponding Overpass area. The query retrieves OSM ways tagged with `highway` and uses `out meta geom` so the full road-line geometry, OSM version and edit timestamp are preserved.

This is important: the Victoria point pipeline uses representative centre points for ways and relations. Those centre points are not suitable for drawing roads as lines. The Mahé road pipeline is a separate, geometry-preserving extraction.

## What appears on the map

- **Roads and streets:** line geometry styled by OSM road class. Footpaths, cycleways and trails are available as a separate optional layer.
- **Named roads:** a selectable overlay; the underlying OpenStreetMap basemap also provides familiar road and place labels.
- **Roads without a mapped name:** a separate layer so incomplete naming can be reviewed.
- **Newly mapped since last snapshot:** road ways present in the current extract but absent from the previous saved snapshot.
- **Updated since last snapshot:** road ways whose OSM version, tags or geometry changed between snapshots.

Selecting a road displays its name where available, road class, surface, lanes, one-way tag, OSM version, last OSM edit timestamp and a link to the OSM way.

## What “new road” means

Africa Compass will use careful status labels:

- **Newly mapped** means this OSM road way appeared in the latest Africa Compass snapshot but not the previous one.
- **Updated** means the OSM way's version, tags or geometry changed since the previous snapshot.
- **No longer in extract** means the way was in the previous snapshot but is absent from the current query result.

These are data-change indicators, not proof of physical construction, resurfacing, closure or demolition. A real-world road construction tracker would need additional verified sources such as official public works notices, planning records or field reports.

## Snapshot history

The refresh workflow saves `data/history/mahe_roads_snapshot.json` to the repository after each run. The first run establishes the baseline. The scheduled workflow refreshes the road inventory weekly, and later runs compare the current data with the saved baseline.

## Outputs

| Output | Purpose |
|---|---|
| `outputs/mahe_road_network.html` | Downloadable interactive island-wide road map |\n| `docs/map/index.html` | Source for the Africa Compass interactive web app |\n| `_site/` | Pages-ready site assembled during the workflow |
| `data/processed/mahe_roads.csv` | Road inventory and attributes |
| `data/processed/mahe_roads.geojson` | Full line geometry for web maps and GIS |
| `data/processed/mahe_road_changes.csv` | Newly mapped, updated and no-longer-in-extract ways |
| `data/history/mahe_roads_snapshot.json` | Compact comparison baseline for future refreshes |

## Web map experience

The public-facing app lives in `docs/map/index.html` and is assembled by `src/build_map_site.py`. It provides road-name search, selectable road layers, a separate footpaths/trails filter, road-type filtering, a road detail panel, downloads for the road inventory and change log, and a hand-off to OpenStreetMap Notes for map corrections. The issue-report action copies the description and map-centre coordinates; the user reviews and submits the note on OpenStreetMap. Africa Compass does not collect or submit reports itself.

The site is published using GitHub Pages from the `refresh-mahe-roads.yml` workflow. For the first deployment, enable Pages in repository settings: **Settings → Pages → Build and deployment → Source → GitHub Actions**. Once enabled, the workflow builds the map data, uploads the website artifact and deploys the site.

The interactive app uses Leaflet with the OpenStreetMap standard tile layer as its labelled basemap. Its road overlays are generated from the separate full-geometry GeoJSON inventory. The map requests tiles only for the area a visitor is currently viewing; it does not bulk-download or prefetch map tiles.

## Attribution and licensing

Map data © OpenStreetMap contributors. OpenStreetMap data is made available under the Open Database License (ODbL). Display required attribution on the map and link to https://www.openstreetmap.org/copyright. Any redistribution of OSM-derived databases must comply with the ODbL.

## Current limitations

- The road inventory reflects OpenStreetMap coverage and tagging at the time of the snapshot.
- An unnamed road is not necessarily a new or unrecognised road; its name may simply not be mapped.
- Changes in OSM are community data edits and are not independent confirmation of a change on the ground.
- The initial saved snapshot is a baseline. Newly mapped and updated status indicators become meaningful from the second successful snapshot onward.\n- The first GitHub Pages deployment requires Pages to be enabled with the source set to GitHub Actions in repository settings.
