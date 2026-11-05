"""Check that the current main application and tracking routes work together."""
import psycopg
from psycopg import sql
import pytest

from api import app
from backend.main import app as alternate_app

pytestmark = pytest.mark.integration
PREFIX = "/api/v1"


@pytest.fixture
def road_body():
    return {
        "name": "Local integration road", "speed_limit_kph": 60,
        "is_oneway": True, "direction": "forward",
        "geom": {"type": "LineString", "coordinates": [[-67.16, 18.21], [-67.15, 18.20]]},
    }


@pytest.fixture
def parking_body():
    return {
        "name": "Local integration parking", "capacity": 10,
        "geom": {"type": "Polygon", "coordinates": [[
            [-67.15, 18.20], [-67.14, 18.20], [-67.14, 18.21],
            [-67.15, 18.21], [-67.15, 18.20],
        ]]},
    }


def test_both_entry_points_use_one_application(client):
    assert app is alternate_app
    paths = app.openapi()["paths"]
    for resource, key in (
        ("road-segments", "road_id"), ("parking-areas", "parking_area_id"),
        ("trips", "trip_id"), ("location-pings", "ping_id"),
    ):
        assert {"get", "post"} <= paths[f"{PREFIX}/{resource}"].keys()
        assert {"get", "put", "delete"} <= paths[f"{PREFIX}/{resource}/{{{key}}}"].keys()
    assert "get" in paths[f"{PREFIX}/road-segments/geojson"]
    assert "delete" in paths[f"{PREFIX}/road-segments/{{road_id}}/remove"]


@pytest.mark.parametrize("resource,expected_count", [("road-segments", 4086), ("parking-areas", 224)])
def test_main_collection_routes_keep_official_data(client, resource, expected_count):
    response = client.get(f"{PREFIX}/{resource}")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["count"] == expected_count
    assert payload["limit"] == 20 and len(payload["items"]) == 20


@pytest.mark.parametrize("resource,body_fixture,key,changes", [
    ("road-segments", "road_body", "road_id", {"speed_limit_kph": 80}),
    ("parking-areas", "parking_body", "parking_area_id", {"capacity": 15}),
])
def test_road_and_parking_crud(client, request, resource, body_fixture, key, changes, database):
    body = request.getfixturevalue(body_fixture)
    collection = f"{PREFIX}/{resource}"
    created = client.post(collection, json=body)
    assert created.status_code == 201, created.text
    record = created.json()
    assert isinstance(record[key], int) and record[key] > 0
    assert record["geom"] == body["geom"]
    assert record["created_at"].endswith("Z")
    for name in body:
        assert record[name] == body[name]
    path = f"{collection}/{record[key]}"
    assert client.get(path).json() == record
    updated = client.put(path, json=changes)
    assert updated.status_code == 200, updated.text
    assert updated.json() == {**record, **changes}
    assert client.get(path).json() == updated.json()
    with psycopg.connect(database) as connection:
        table = "road_segment" if resource == "road-segments" else "parking_area"
        stored = connection.execute(sql.SQL(
            "SELECT ST_SRID(geom), created_at FROM {} WHERE {} = %s"
        ).format(sql.Identifier("projectfall2026", table), sql.Identifier(key)), (record[key],)).fetchone()
        assert stored[0] == 4326 and stored[1] is not None
    deleted = client.delete(path)
    assert deleted.status_code == 200
    assert deleted.json()[key] == record[key]
    assert client.get(path).status_code == 404
    assert client.put(path, json=changes).status_code == 404
    assert client.delete(path).status_code == 404


def test_road_delete_uses_required_remove_path(client, road_body):
    created = client.post(f"{PREFIX}/road-segments", json=road_body).json()
    response = client.delete(f"{PREFIX}/road-segments/{created['road_id']}/remove")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Road segment deleted successfully.", "road_id": created["road_id"],
    }


def test_road_geojson_and_validation_statuses(client):
    response = client.get(f"{PREFIX}/road-segments/geojson", params={"limit": 1})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    body = response.json()
    assert body["type"] == "FeatureCollection" and body["count"] == 4086
    assert len(body["features"]) == 1
    assert body["features"][0]["geometry"]["type"] == "LineString"
    assert client.get(f"{PREFIX}/road-segments/geojson?limit=-1").status_code == 422
    assert client.get(f"{PREFIX}/road-segments/geojson?bbox=0,0,1,1").status_code == 400
    assert client.get(f"{PREFIX}/road-segments/geojson?min_speed_kph=80&max_speed_kph=60").status_code == 400


@pytest.mark.parametrize("resource", ["road-segments", "parking-areas"])
@pytest.mark.parametrize("query", [{"limit": "-1"}, {"offset": "1.2"}, {"limit": "9" * 30}, {"offset": "9" * 30}])
def test_main_pagination_errors_are_bad_requests(client, resource, query):
    assert client.get(f"{PREFIX}/{resource}", params=query).status_code == 400


@pytest.mark.parametrize("resource,fixture_name,field", [
    ("road-segments", "road_body", "speed_limit_kph"), ("parking-areas", "parking_body", "capacity"),
])
def test_main_invalid_numbers_and_geometry_are_bad_requests(client, request, resource, fixture_name, field):
    body = request.getfixturevalue(fixture_name)
    path = f"{PREFIX}/{resource}"
    assert client.post(path, json={**body, field: 10**1000}).status_code == 400
    if resource == "road-segments":
        body["geom"]["coordinates"][0].append(0)
    else:
        for position in body["geom"]["coordinates"][0]:
            position.append(0)
    assert client.post(path, json=body).status_code == 400
    assert client.post(path, content='{', headers={"content-type": "application/json"}).status_code == 400
