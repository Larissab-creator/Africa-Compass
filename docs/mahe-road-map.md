# Mahé Island road map

## Product direction

Africa Compass is being developed as an interactive geographical map, not a slide deck or a chart-first dashboard. The main Mahé view should show the island-wide road network, readable existing road labels, and a clear way to inspect road segments.

## Data source and geography

The road inventory is queried from OpenStreetMap using Mahé Island's OSM relation (relation ID 9435209) and its corresponding Overpass area. The query retrieves OSM ways tagged with `highway` and uses `out geom tags` so the full road-line geometry is preserved.

This is important: the Victoria point pipeline uses representative centre points for ways and relations. Those centre points are not suitable for drawing roads as lines. The Mahé road pipeline is a separate, geometry-preserving extraction.

## What appears on the map

- **All mapped roads:** line geometry styled by OSM road class.
- **Named roads:** a selectable overlay; the underlying OpenStreetMap basemap also provides familiar road and place labels.
- **Roads without a mapped name:** a separate layer so incomplete naming can be reviewed.
- **Newly mapped since last snapshot:** road ways present in the current extract but absent from the previous saved snapshot.
- **Updated since last snapshot:** road ways whose OSM version, tags or geometry changed between snapshots.

Selecting a road displays its name where available, road class, surface, lanes, one-way tag, last OSM edit timestamp and a link to the OSM way.

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
| `outputs/mahe_road_network.html` | Interactive island-wide road map |
| `data/processed/mahe_roads.csv` | Road inventory and attributes |
| `data/processed/mahe_roads.geojson` | Full line geometry for web maps and GIS |
| `data/processed/mahe_road_changes.csv` | Newly mapped, updated and no-longer-in-extract ways |
| `data/history/mahe_roads_snapshot.json` | Compact comparison baseline for future refreshes |

## Map technology

The map is generated with Folium/Leaflet and uses OpenStreetMap tiles as the labelled basemap. Its road overlays are generated from the separate full-geometry GeoJSON inventory. Leaflet supports GeoJSON line layers and selectable overlays.

## Attribution and licensing

Map data © OpenStreetMap contributors. OpenStreetMap data is made available under the Open Database License (ODbL). Display required attribution on the map and link to https://www.openstreetmap.org/copyright. Any redistribution of OSM-derived databases must comply with the ODbL.

## Current limitations

- The road inventory reflects OpenStreetMap coverage and tagging at the time of the snapshot.
- An unnamed road is not necessarily a new or unrecognised road; its name may simply not be mapped.
- Changes in OSM are community data edits and are not independent confirmation of a change on the ground.
- The initial saved snapshot is a baseline. Newly mapped and updated status indicators become meaningful from the second successful snapshot onward.
