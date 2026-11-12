# Flourish dashboard plan — Victoria pilot

## Working title

**Africa Compass: Mapping essential services and transport in Victoria, Seychelles**

## Story

Show what has been mapped in the Victoria pilot, where service records are concentrated, and how mapped healthcare, education, food retail and bus stops are distributed across an approximate 500m grid.

This is a map-coverage and exploratory spatial-analysis story. It is not a claim about population access or real-world service availability.

## Suggested dashboard sections

### 1. Pilot snapshot — KPI cards

Use the following headline values:
- 931 validated mapped features
- 217 mapped service features
- 206 mapped bus stops
- 81 approximate 500m grid cells
- 30 grid cells with one or more mapped service features

### 2. What kinds of services are mapped? — bar chart

**Dataset:** `data/processed/victoria_service_summary.csv`

Recommended fields:
- Category: `analysis_group_label`
- Value: `mapped_locations`
- Optional tooltip: `share_of_mapped_services_pct`

Use a horizontal bar chart, sorted descending. Keep “Other mapped services” visible, but explain that this broad group contains dining, retail, hospitality and other service tags.

### 3. What sits inside each group? — detailed bar chart

**Dataset:** `data/processed/victoria_service_subcategory_summary.csv`

Recommended fields:
- Category: `subcategory`
- Value: `mapped_locations`
- Tooltip / filter: `analysis_group_label`

Use a top-10 view or a group filter. This reveals the actual OSM tag types behind the high-level group totals.

### 4. Where are mapped services? — point map

**Dataset:** `data/processed/victoria_service_points.csv`

Recommended fields:
- Latitude: `latitude`
- Longitude: `longitude`
- Marker label: `name`
- Colour/category: `analysis_group_label`
- Tooltip: `subcategory`, `name`

Use category filters for healthcare, education, food retail, finance, civic/safety and other mapped services. Include OpenStreetMap attribution.

### 5. How close are grid centres to mapped locations? — comparison chart

**Dataset:** `data/processed/victoria_proximity_summary.csv`

Chart A:
- Category: `service_label`
- Value: `median_distance_km`
- Title: “Median straight-line distance to the nearest mapped location”

Chart B:
- Category: `service_label`
- Value: `share_of_grid_cells_within_500m_pct`
- Title: “Grid-cell centres within 500m of a mapped location”

Keep bus stops in the chart as the transport comparison. Add a note that these are grid-cell-centre measures, not percentages of residents.

### 6. Where do mapped services cluster? — grid / bubble map

**Dataset:** `data/processed/victoria_accessibility_grid_500m.csv`

Map fields:
- Latitude: `latitude`
- Longitude: `longitude`
- Size or colour: `mapped_service_count`
- Tooltip: `grid_id`, `mapped_service_count`, `mapped_bus_stop_count`, `nearest_healthcare_km`, `nearest_education_km`, `nearest_food_retail_km`, `nearest_bus_stop_km`

A proportional-symbol map of cell centres is a Flourish-friendly alternative to a polygon grid map. The full square-grid view is already available in `outputs/victoria_service_accessibility_map.html`.

## Suggested visual hierarchy

1. Large title and one-sentence explanation.
2. KPI cards.
3. Service group bar chart beside the map.
4. Detailed service subcategory chart.
5. Median-distance and 500m proximity comparison.
6. Grid / bubble map and methodology note.

Use a restrained palette with a distinct colour per service group. Keep the map legend and filters visible; avoid treating missing map records as confirmed absence.

## Required source note

“Map data © OpenStreetMap contributors. OpenStreetMap data is made available under the Open Database License (ODbL). Coverage may be incomplete or out of date.”

## Caveat to display on the dashboard

“The 500m grid is not population-weighted and includes coastal/non-residential cells. Distances are straight-line estimates from cell centres, not walking or driving routes. A mapped place is not proof that a service is open or operational.”
