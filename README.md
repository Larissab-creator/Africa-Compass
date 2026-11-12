# Africa Compass 🌍

Africa Compass is an interactive mapping project starting on Mahé, Seychelles. Many smaller communities, neighbourhoods and local routes across Africa are difficult to discover on digital maps. The project aims to bring local roads, access routes, paths and public transport into clearer view, making it easier for residents and visitors to explore unfamiliar places.

- **Explore Mahé:** Search roads, smaller access routes, footpaths and trails. Hover over mapped features to see their names; unnamed features are identified clearly.
- **Find public transport:** View bus routes and mapped stops where route information is available in OpenStreetMap. Check the [official SPTC timetable](https://sptc.sc/timetable/) for current departures and service updates.
- **Refresh every Monday:** GitHub Actions retrieves the latest available road and bus data at 03:00 UTC, compares road data with the previous snapshot and republishes the map.
- **Improve map detail:** Identify missing or incorrect information and prepare a report for review on OpenStreetMap.
- **Built with:** Python, OpenStreetMap, Overpass API, GeoJSON, Leaflet, GitHub Actions and GitHub Pages.
- **Growing project:** Mahé is the starting point, with the longer-term aim of expanding to other islands, districts and countries. The earlier Victoria services dataset remains a supporting project.
- **Data note:** Coverage depends on what contributors have mapped. Bus route lines, stops and road names may be incomplete; snapshot changes do not prove physical road construction or closure. Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), licensed under the [ODbL](https://opendatacommons.org/licenses/odbl/).

[View the Mahé road-map refresh workflow](https://github.com/Larissab-creator/Africa-Compass/actions/workflows/refresh-mahe-roads.yml).
