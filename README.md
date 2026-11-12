# Africa Compass 🌍

Africa Compass is an interactive mapping project starting on Mahé, Seychelles. Many smaller communities, neighbourhoods and local routes across Africa are difficult to discover on digital maps, particularly when roads and paths are unnamed or only visible when zooming in closely. Africa Compass aims to bring these places into clearer view and make exploring unfamiliar areas easier for residents and visitors.

- **Explore Mahé:** Search mapped roads, inspect road details and discover smaller access roads, tracks, footpaths and trails.
- **Refresh every Monday:** GitHub Actions retrieves the latest available OpenStreetMap data at 03:00 UTC every Monday, compares it with the previous snapshot and flags newly mapped, updated and no-longer-present features.
- **Help improve map detail:** Identify missing or incorrect information and prepare a report for review on OpenStreetMap.
- **Built with:** Python, OpenStreetMap, Overpass API, GeoJSON, Leaflet, GitHub Actions and GitHub Pages.
- **Growing project:** Mahé is the starting point, with the longer-term aim of expanding to other islands, districts and countries. The earlier Victoria services dataset remains a supporting project.
- **Data note:** Changes show differences in OpenStreetMap records; they do not confirm that a road has been built or closed. Trail access and conditions are not independently verified. Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), licensed under the [ODbL](https://opendatacommons.org/licenses/odbl/).

[View the Mahé road-map refresh workflow](https://github.com/Larissab-creator/Africa-Compass/actions/workflows/refresh-mahe-roads.yml).

