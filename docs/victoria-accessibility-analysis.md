# Victoria mapped-service analysis — method and first findings

**Snapshot date:** 12 November 2026  
**Pilot area:** Victoria, Mahé, Seychelles  
**Primary source:** OpenStreetMap contributors

## What was analysed

The analysis uses the validated Victoria pilot extract produced by `src/sey_pipeline.py`. The snapshot contains 931 named mapped features: 430 transport features, 217 service features, 173 place features and 111 attractions. The transport category includes 206 features tagged as bus stops.

The analysis is exploratory. It describes mapped OpenStreetMap records, not a complete census of services or a measure of lived accessibility.

## First-pass service groups

Service features are grouped from the extracted OSM `subcategory` field:

| Analysis group | Included OSM subcategories | Mapped locations |
|---|---|---:|
| Healthcare | hospital, clinic, doctors, pharmacy, dentist, healthcare | 9 |
| Education and childcare | school, kindergarten, childcare, college, university | 10 |
| Food retail | supermarket, convenience, butcher, marketplace, bakery, greengrocer, farm, wholesale | 28 |
| Financial services | bank, ATM, bureau de change | 19 |
| Civic and safety services | police, fire station, town hall, post office, community centre, public building, outpost | 12 |
| Public transport facilities | ferry terminal, bus station | 4 |
| Other mapped services | all remaining service subcategories | 135 |
| **Total service features** |  | **217** |

The 135 records in “other mapped services” include a mixture of dining, hospitality, retail and other activities. These are not all essential services. The grouping is a transparent, first-pass rule set and should be reviewed with local knowledge before public-facing use.

## Spatial method

The Victoria pilot bounding box is divided into approximately 500m by 500m cells. The grid contains 81 cells. For each cell, the pipeline calculates:
- counts of all mapped features, service features and bus stops;
- counts of selected service groups; and
- straight-line distance from the cell centre to the nearest mapped healthcare, education or food-retail point.

Distances use the haversine great-circle formula. They are not walking distances, driving distances, journey times or route-network measurements.

## First findings

- 30 of 81 grid cells (37.0%) contain at least one mapped service feature.
- 48 of 81 cells (59.3%) contain at least one mapped bus stop.
- Median straight-line distance from grid-cell centres to the nearest mapped healthcare point is 1.056 km.
- Median straight-line distance to the nearest mapped education point is 0.891 km.
- Median straight-line distance to the nearest mapped food-retail point is 0.578 km.
- 18.5% of grid-cell centres are within 500m of a mapped healthcare point; 21.0% are within 500m of a mapped education point; 39.5% are within 500m of a mapped food-retail point.

These percentages are proportions of grid-cell centres, not proportions of residents or households.

## Important limitations

1. **OpenStreetMap completeness:** missing features may simply not have been mapped or tagged. A zero in a cell is not proof that no service exists there.
2. **Population:** the grid is not weighted by population, households, demand or building occupancy.
3. **Land and coast:** some grid cells cover coastal or non-residential areas.
4. **Routing:** distances are straight-line approximations. A road/walking network and access restrictions have not been modelled.
5. **Operating status:** a mapped location does not prove that it is open, active, accessible to the public or adequately resourced.
6. **Classification:** the service groups are based on a small set of OSM tag values and need local review.
7. **Geographic scope:** this is a small Victoria pilot bounding box, not all of Mahé or Seychelles.

## Outputs

Running `python src/accessibility_analysis.py` after the main pipeline creates:

- `data/processed/victoria_service_points.csv` — service features with analysis groups; suitable for filtering and point-map visualisations.
- `data/processed/victoria_service_summary.csv` — group counts and percentages; suitable for a bar chart.
- `data/processed/victoria_service_subcategory_summary.csv` — detailed OSM subcategory counts within each group; suitable for a more granular dashboard.
- `data/processed/victoria_accessibility_grid_500m.csv` — grid-cell counts, coordinates and nearest mapped service distances; suitable for exploratory grid/bubble maps.
- `data/processed/victoria_accessibility_metrics.json` — headline metrics and methodological caveats.
- `outputs/victoria_service_accessibility_map.html` — interactive map with a mapped-service grid and selectable service layers.

## Next analytical improvements

1. Validate service groups against local authoritative directories and local knowledge.
2. Add population or building-residential estimates to create population-weighted indicators.
3. Build a routable pedestrian network and calculate network distances or travel times.
4. Add data freshness and operational-status checks where reliable sources exist.
5. Expand the pilot area and test whether the methodology transfers to other districts.

## Attribution

Map data © OpenStreetMap contributors. See https://www.openstreetmap.org/copyright. OpenStreetMap data is made available under the Open Database License (ODbL). Ensure any redistributed OSM-derived database or map carries the required attribution and meets the licence terms.
