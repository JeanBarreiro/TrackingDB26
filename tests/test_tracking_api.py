from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psycopg
import pytest

from backend.main import app

pytestmark = pytest.mark.integration
PREFIX = "/api/v1"


def test_all_twelve_endpoints_are_registered(client):
    for resource, key in (("trips", "trip_id"), ("location-pings", "ping_id")):
        paths = app.openapi()["paths"]
        assert {"get", "post"} <= paths[f"{PREFIX}/{resource}"].keys()
        assert {"get", "put", "delete"} <= paths[f"{PREFIX}/{resource}/{{{key}}}"].keys()
        nested = "trips" if resource == "trips" else "pings"
        assert "get" in paths[f"{PREFIX}/vehicles/{{vehicle_id}}/{nested}"]
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/db-check").json()["database"] == "tracking_phase2_test"
    assert len(client.get("/vehicles").json()["vehicles"]) == 30


def test_trip_crud_and_persistence(client, trip_body, database):
    response = client.post(f"{PREFIX}/trips", json=trip_body)
    assert response.status_code == 201, response.text
    trip = response.json()
    trip_id = trip["trip_id"]
    assert trip_id > 300
    assert trip == {"trip_id": trip_id, **trip_body}
    with psycopg.connect(database) as connection:
        assert connection.execute("SELECT ST_SRID(start_geom), ST_X(start_geom), distance_km FROM projectfall2026.trip WHERE trip_id=%s", (trip_id,)).fetchone() == (4326, -67.15, 6.7)
    assert client.get(f"{PREFIX}/trips/{trip_id}").json() == trip
    changed = client.put(f"{PREFIX}/trips/{trip_id}", json={"end_ts": "2030-03-14T09:00:00Z", "distance_km": 7.1})
    assert changed.status_code == 200
    assert changed.json()["start_ts"] == trip["start_ts"]
    assert changed.json()["distance_km"] == 7.1
    assert client.get(f"{PREFIX}/trips/{trip_id}").json() == changed.json()
    assert client.delete(f"{PREFIX}/trips/{trip_id}").json() == {"message": "Trip deleted successfully.", "trip_id": trip_id}
    assert client.get(f"{PREFIX}/trips/{trip_id}").status_code == 404
    assert client.delete(f"{PREFIX}/trips/{trip_id}").status_code == 404


def test_ping_crud_and_persistence(client, ping_body, database):
    response = client.post(f"{PREFIX}/location-pings", json=ping_body)
    assert response.status_code == 201, response.text
    ping = response.json()
    ping_id = ping["ping_id"]
    assert ping_id > 28041
    assert ping == {"ping_id": ping_id, **ping_body}
    with psycopg.connect(database) as connection:
        assert connection.execute("SELECT ST_SRID(geom), ST_Y(geom), speed_kph FROM projectfall2026.location_ping WHERE ping_id=%s", (ping_id,)).fetchone() == (4326, 18.2011, 42.8)
    assert client.get(f"{PREFIX}/location-pings/{ping_id}").json() == ping
    changed = client.put(f"{PREFIX}/location-pings/{ping_id}", json={"speed_kph": 45.1, "heading_deg": 190.0})
    assert changed.status_code == 200
    assert changed.json()["geom"] == ping["geom"]
    assert changed.json()["heading_deg"] == 190.0
    assert client.get(f"{PREFIX}/location-pings/{ping_id}").json() == changed.json()
    assert client.delete(f"{PREFIX}/location-pings/{ping_id}").json() == {"message": "Location ping deleted successfully.", "ping_id": ping_id}
    assert client.get(f"{PREFIX}/location-pings/{ping_id}").status_code == 404


@pytest.mark.parametrize("resource,body_fixture,key", [("trips", "trip_body", "trip_id"), ("location-pings", "ping_body", "ping_id")])
def test_full_updates_and_nullable_fields(client, request, resource, body_fixture, key):
    body = request.getfixturevalue(body_fixture)
    record = client.post(f"{PREFIX}/{resource}", json=body).json()
    body["vehicle_id"] = 2
    if resource == "trips":
        body.update(start_geom=None, end_geom=None, distance_km=None)
    else:
        body.update(speed_kph=None, heading_deg=None)
    response = client.put(f"{PREFIX}/{resource}/{record[key]}", json=body)
    assert response.status_code == 200, response.text
    assert response.json() == {key: record[key], **body}


@pytest.mark.parametrize("resource,body_fixture,key", [("trips", "trip_body", "trip_id"), ("location-pings", "ping_body", "ping_id")])
def test_list_and_vehicle_filters(client, request, resource, body_fixture, key):
    body = request.getfixturevalue(body_fixture)
    record = client.post(f"{PREFIX}/{resource}", json=body).json()
    query = {"vehicle_id": 1, "from_ts": "2030-03-14T00:00:00Z", "to_ts": "2030-03-14T23:59:59Z", "limit": 1, "offset": 0}
    response = client.get(f"{PREFIX}/{resource}", params=query)
    assert response.status_code == 200
    result = response.json()
    assert result["count"] == 1 and len(result["items"]) == 1
    assert result["limit"] == 1 and result["offset"] == 0
    assert result["items"][0][key] == record[key]
    assert not {"geom", "start_geom", "end_geom"}.intersection(result["items"][0])
    nested = "trips" if resource == "trips" else "pings"
    result = client.get(f"{PREFIX}/vehicles/1/{nested}", params=query).json()
    assert result["vehicle_id"] == 1 and result["count"] == 1
    assert "vehicle_id" not in result["items"][0]
    if resource == "location-pings":
        assert result["items"][0]["geom"] == body["geom"]
    assert client.get(f"{PREFIX}/vehicles/999999/{nested}").status_code == 404
    query["vehicle_id"] = 999999
    assert client.get(f"{PREFIX}/{resource}", params=query).json()["items"] == []
    query["vehicle_id"] = 1
    query["limit"] = 0
    result = client.get(f"{PREFIX}/{resource}", params=query).json()
    assert result["items"] == [] and result["count"] == 1
    query.update(limit=1, offset=1)
    assert client.get(f"{PREFIX}/{resource}", params=query).json()["items"] == []


def test_timezone_normalization_and_trip_overlap(client, trip_body, ping_body):
    trip_body.update(start_ts="2030-03-14T04:00:00-04:00", end_ts="2030-03-14T04:45:00-04:00")
    trip = client.post(f"{PREFIX}/trips", json=trip_body).json()
    assert trip["start_ts"] == "2030-03-14T08:00:00Z"
    query = {"from_ts": "2030-03-14T08:30:00Z", "to_ts": "2030-03-14T08:35:00Z"}
    assert client.get(f"{PREFIX}/trips", params=query).json()["count"] == 1
    ping_body["ts"] = "2030-03-14T05:58:20-04:00"
    ping = client.post(f"{PREFIX}/location-pings", json=ping_body).json()
    assert ping["ts"] == "2030-03-14T09:58:20Z"
    query = {"from_ts": ping["ts"], "to_ts": ping["ts"]}
    assert client.get(f"{PREFIX}/location-pings", params=query).json()["count"] == 1


def test_bbox_includes_boundary_and_combines_filters(client, ping_body):
    ping_body["geom"] = {"type": "Point", "coordinates": [-67.2, 18.2]}
    ping = client.post(f"{PREFIX}/location-pings", json=ping_body).json()
    query = {"vehicle_id": 1, "from_ts": ping["ts"], "to_ts": ping["ts"], "bbox": "-67.2,18.1,-67.1,18.3"}
    assert client.get(f"{PREFIX}/location-pings", params=query).json()["count"] == 1
    query["bbox"] = "-67.19,18.1,-67.1,18.3"
    assert client.get(f"{PREFIX}/location-pings", params=query).json()["items"] == []


@pytest.mark.parametrize("query", [
    {"limit": "-1"}, {"offset": "-1"}, {"limit": "1.2"}, {"limit": "x"},
    {"limit": "9223372036854775808"}, {"vehicle_id": "0"}, {"vehicle_id": "abc"},
    {"from_ts": "2030-01-01T00:00:00"}, {"to_ts": "invalid"},
    {"from_ts": "2030-01-02T00:00:00Z", "to_ts": "2030-01-01T00:00:00Z"},
    {"limit": "1; DROP TABLE trip"},
    {"limit": "9" * 5000}, {"vehicle_id": "9" * 5000},
])
@pytest.mark.parametrize("resource", ["trips", "location-pings"])
def test_invalid_query_parameters(client, resource, query):
    assert client.get(f"{PREFIX}/{resource}", params=query).status_code == 400


@pytest.mark.parametrize("bbox", ["", "1,2,3", "-67,18,-68,19", "0,1,2,1", "-181,0,1,1", "0,-91,1,1", "nan,0,1,1", "0,0,inf,1", "a,b,c,d"])
def test_invalid_bbox(client, bbox):
    assert client.get(f"{PREFIX}/location-pings", params={"bbox": bbox}).status_code == 400


@pytest.mark.parametrize("resource", ["trips", "location-pings"])
@pytest.mark.parametrize("record_id", ["0", "-1", "abc", "9223372036854775808", "99999999"])
def test_missing_or_invalid_ids(client, resource, record_id):
    path = f"{PREFIX}/{resource}/{record_id}"
    assert client.get(path).status_code == 404
    assert client.put(path, json={"vehicle_id": 1}).status_code == 404
    assert client.delete(path).status_code == 404


@pytest.mark.parametrize("resource,fixture_name", [("trips", "trip_body"), ("location-pings", "ping_body")])
@pytest.mark.parametrize("value", [None, True, "1", 0, -1, 1.5])
def test_invalid_vehicle_ids(client, request, resource, fixture_name, value):
    body = request.getfixturevalue(fixture_name)
    body["vehicle_id"] = value
    assert client.post(f"{PREFIX}/{resource}", json=body).status_code == 400


@pytest.mark.parametrize("resource,fixture_name,key", [("trips", "trip_body", "trip_id"), ("location-pings", "ping_body", "ping_id")])
def test_missing_vehicle_and_failed_update_rollback(client, request, resource, fixture_name, key):
    body = request.getfixturevalue(fixture_name)
    record = client.post(f"{PREFIX}/{resource}", json=body).json()
    body["vehicle_id"] = 99999999
    assert client.post(f"{PREFIX}/{resource}", json=body).status_code == 404
    assert client.put(f"{PREFIX}/{resource}/{record[key]}", json={"vehicle_id": 99999999}).status_code == 404
    assert client.get(f"{PREFIX}/{resource}/{record[key]}").json() == record


@pytest.mark.parametrize("resource,fixture_name,field", [("trips", "trip_body", "start_geom"), ("location-pings", "ping_body", "geom")])
@pytest.mark.parametrize("geometry", [
    {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
    {"type": "Point", "coordinates": [0]}, {"type": "Point", "coordinates": [0, 0, 1]},
    {"type": "Point", "coordinates": [181, 0]}, {"type": "Point", "coordinates": [0, 91]},
    {"type": "Point", "coordinates": [True, 1]}, {"type": "Point", "coordinates": ["0", 1]},
    {"type": "Point", "coordinates": [10**1000, 1]},
])
def test_invalid_geometry(client, request, resource, fixture_name, field, geometry):
    body = request.getfixturevalue(fixture_name)
    body[field] = geometry
    assert client.post(f"{PREFIX}/{resource}", json=body).status_code == 400


@pytest.mark.parametrize("resource,fixture_name,field", [("trips", "trip_body", "start_ts"), ("location-pings", "ping_body", "ts")])
@pytest.mark.parametrize("value", [None, "2030-01-01", "2030-03-14T08:00:00", "2030-02-30T08:00:00Z", "2030-03-14T08:00:00+01:99", "0001-01-01T00:00:00+01:00"])
def test_invalid_timestamps(client, request, resource, fixture_name, field, value):
    body = request.getfixturevalue(fixture_name)
    body[field] = value
    assert client.post(f"{PREFIX}/{resource}", json=body).status_code == 400


def test_trip_cross_field_validation_on_partial_update(client, trip_body):
    record = client.post(f"{PREFIX}/trips", json=trip_body).json()
    path = f"{PREFIX}/trips/{record['trip_id']}"
    for payload in [{"end_ts": trip_body["start_ts"]}, {"start_ts": "2030-03-15T00:00:00Z"}, {"distance_km": -1}]:
        assert client.put(path, json=payload).status_code == 422
        assert client.get(path).json() == record
    trip_body["end_ts"] = trip_body["start_ts"]
    assert client.post(f"{PREFIX}/trips", json=trip_body).status_code == 400


@pytest.mark.parametrize("payload", [{"speed_kph": -1}, {"heading_deg": -1}, {"heading_deg": 360}, {"heading_deg": True}, {"speed_kph": "12"}, {"geom": None}, {"speed_kph": 10**1000}])
def test_ping_telemetry_and_update_validation(client, ping_body, payload):
    record = client.post(f"{PREFIX}/location-pings", json=ping_body).json()
    assert client.post(f"{PREFIX}/location-pings", json={**ping_body, **payload}).status_code == 400
    path = f"{PREFIX}/location-pings/{record['ping_id']}"
    assert client.put(path, json=payload).status_code == 400
    assert client.get(path).json() == record


@pytest.mark.parametrize("resource,fixture_name,key", [("trips", "trip_body", "trip_id"), ("location-pings", "ping_body", "ping_id")])
def test_body_shape_and_required_fields(client, request, resource, fixture_name, key):
    body = request.getfixturevalue(fixture_name)
    path = f"{PREFIX}/{resource}"
    assert client.post(path, json={}).status_code == 400
    assert client.post(path, json=[]).status_code == 400
    assert client.post(path, content='{', headers={"content-type": "application/json"}).status_code == 400
    assert client.post(path, json={**body, "unexpected": 1}).status_code == 400
    for field in ["vehicle_id", "start_ts", "end_ts"] if resource == "trips" else ["vehicle_id", "ts", "geom"]:
        reduced = {k: v for k, v in body.items() if k != field}
        assert client.post(path, json=reduced).status_code == 400
    record = client.post(path, json=body).json()
    assert client.put(f"{path}/{record[key]}", json={}).status_code == 400
    assert client.put(f"{path}/{record[key]}", content='{', headers={"content-type": "application/json"}).status_code == 400


def test_optional_trip_geometry_and_ping_telemetry(client, trip_body, ping_body):
    for field in ["start_geom", "end_geom", "distance_km"]:
        del trip_body[field]
    trip = client.post(f"{PREFIX}/trips", json=trip_body)
    assert trip.status_code == 201
    assert trip.json()["start_geom"] is None and trip.json()["distance_km"] is None
    del ping_body["speed_kph"], ping_body["heading_deg"]
    ping = client.post(f"{PREFIX}/location-pings", json=ping_body)
    assert ping.status_code == 201
    assert ping.json()["speed_kph"] is None and ping.json()["heading_deg"] is None


def test_concurrent_creates_get_unique_ids(client, trip_body, ping_body):
    for resource, body, key in [("trips", trip_body, "trip_id"), ("location-pings", ping_body, "ping_id")]:
        with ThreadPoolExecutor(max_workers=6) as executor:
            responses = list(executor.map(lambda _: client.post(f"{PREFIX}/{resource}", json=body), range(12)))
        assert all(response.status_code == 201 for response in responses)
        assert len({response.json()[key] for response in responses}) == 12


def test_schema_setup_is_repeatable_without_resetting_ids(client, trip_body, database):
    first = client.post(f"{PREFIX}/trips", json=trip_body).json()["trip_id"]
    client.delete(f"{PREFIX}/trips/{first}")
    with psycopg.connect(database, autocommit=True) as connection:
        connection.execute((Path(__file__).resolve().parent.parent / "sql/phase2_setup.sql").read_text())
    second = client.post(f"{PREFIX}/trips", json=trip_body).json()["trip_id"]
    assert second > first
