from src import mahe_bus_routes


def make_node(osm_id, lat, lon, **tags):
    return {"type": "node", "id": osm_id, "lat": lat, "lon": lon, "tags": tags}


def test_processes_bus_route_geometry_and_ordered_stops():
    payload = {
        "elements": [
            {
                "type": "relation",
                "id": 9001,
                "tags": {
                    "type": "route", "route": "bus", "ref": "21",
                    "name": "Victoria to Beau Vallon", "from": "Victoria",
                    "to": "Beau Vallon", "operator": "SPTC",
                },
                "members": [
                    {"type": "node", "ref": 10, "role": "platform"},
                    {"type": "way", "ref": 101, "role": ""},
                    {"type": "way", "ref": 102, "role": ""},
                    {"type": "node", "ref": 11, "role": "platform"},
                ],
            },
            {"type": "way", "id": 101, "nodes": [1, 2]},
            {"type": "way", "id": 102, "nodes": [3, 2]},
            make_node(1, -4.60, 55.45),
            make_node(2, -4.61, 55.46),
            make_node(3, -4.62, 55.47),
            make_node(10, -4.59, 55.44, name="Victoria Bus Terminal", public_transport="platform"),
            make_node(11, -4.63, 55.48, name="Beau Vallon", highway="bus_stop"),
            make_node(12, -4.64, 55.49, name="Independent Bus Stop", highway="bus_stop"),
        ],
    }

    routes, stops, rows = mahe_bus_routes.process_bus_elements(payload)

    assert len(routes) == 1
    assert routes[0]["geometry"]["type"] == "LineString"
    assert routes[0]["geometry"]["coordinates"] == [
        [55.45, -4.60], [55.46, -4.61], [55.47, -4.62]
    ]
    assert routes[0]["properties"]["ref"] == "21"
    assert routes[0]["properties"]["geometry_status"] == "mapped"
    assert len(rows) == 1
    assert rows[0]["stop_count"] == 2
    by_id = {stop["properties"]["osm_id"]: stop["properties"] for stop in stops}
    assert by_id["10"]["route_refs"] == ["21"]
    assert by_id["11"]["route_refs"] == ["21"]
    assert "12" in by_id


def test_keeps_route_inventory_when_route_has_stops_but_no_mapped_ways():
    payload = {
        "elements": [
            {
                "type": "relation",
                "id": 9002,
                "tags": {"type": "route", "route": "bus", "ref": "X"},
                "members": [{"type": "node", "ref": 20, "role": "platform"}],
            },
            make_node(20, -4.60, 55.45, name="Stop X", public_transport="platform"),
        ]
    }

    routes, stops, rows = mahe_bus_routes.process_bus_elements(payload)

    assert routes == []
    assert rows[0]["geometry_status"] == "stops_only"
    assert stops[0]["properties"]["route_refs"] == ["X"]
