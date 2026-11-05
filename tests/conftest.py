import asyncio
import os
from pathlib import Path

import httpx
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
import pyarrow.parquet as pq
import pytest

from backend.main import app

ROOT = Path(__file__).resolve().parent.parent
TABLES = (
    "road_segment", "parking_area", "vehicle_status", "fuel_type", "vehicle_kind",
    "vehicle_type", "driver", "vehicle", "trip", "location_ping", "vehicle_assignment",
)
RESOURCE_KEYS = {
    "road_segment": "road_id", "parking_area": "parking_area_id",
    "trip": "trip_id", "location_ping": "ping_id",
}
OFFICIAL_MAX_IDS = {
    name: max(pq.read_table(ROOT / "data" / f"{name}.parquet", columns=[key]).column(key).to_pylist())
    for name, key in RESOURCE_KEYS.items()
}


def table_digests(connection, schema):
    return {
        name: connection.execute(sql.SQL(
            "SELECT md5(string_agg(t::text, ',' ORDER BY t::text)) FROM {} AS t"
        ).format(sql.Identifier(schema, name))).fetchone()[0]
        for name in TABLES
    }


@pytest.fixture(scope="session")
def database():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to the dedicated Docker database.")
    settings = conninfo_to_dict(url)
    if (settings.get("host") not in {"localhost", "127.0.0.1", "::1"}
            or settings.get("dbname") != "tracking_phase2_test"):
        pytest.fail("Integration tests require the local Docker database tracking_phase2_test.")
    with psycopg.connect(url, options="-c timezone=UTC") as connection:
        assert connection.execute("SELECT current_database()").fetchone()[0] == "tracking_phase2_test"
        assert connection.info.server_version // 10000 == 17
        connection.execute("DROP SCHEMA IF EXISTS projectfall2026 CASCADE")
        for name in reversed(TABLES):
            connection.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier("public", name)))
        connection.execute((ROOT / "sql/schema.sql").read_text())
        for name in TABLES:
            table = pq.read_table(ROOT / "data" / f"{name}.parquet")
            columns = table.column_names
            with connection.cursor() as cursor:
                with cursor.copy(sql.SQL("COPY {} ({}) FROM STDIN").format(
                    sql.Identifier("public", name), sql.SQL(", ").join(map(sql.Identifier, columns)))) as copy:
                    for row in table.to_pylist():
                        copy.write_row(tuple(row[column] for column in columns))
        baseline = table_digests(connection, "public")
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute((ROOT / "sql/phase2_setup.sql").read_text())
    with psycopg.connect(url, options="-c timezone=UTC") as connection:
        assert table_digests(connection, "projectfall2026") == baseline
    yield url
    # Test records are removed by the client fixture. Recheck every official value.
    with psycopg.connect(url, options="-c timezone=UTC") as connection:
        assert table_digests(connection, "projectfall2026") == baseline


class APIClient:
    def request(self, method, path, **kwargs):
        async def call():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                return await client.request(method, path, **kwargs)
        return asyncio.run(call())

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)


@pytest.fixture
def client(database, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", database)
    monkeypatch.setenv("DB_SCHEMA", "projectfall2026")
    yield APIClient()
    with psycopg.connect(database) as connection:
        for name, key in RESOURCE_KEYS.items():
            connection.execute(sql.SQL("DELETE FROM {} WHERE {} > %s").format(
                sql.Identifier("projectfall2026", name), sql.Identifier(key)
            ), (OFFICIAL_MAX_IDS[name],))


@pytest.fixture
def trip_body():
    return {
        "vehicle_id": 1, "start_ts": "2030-03-14T08:00:00Z", "end_ts": "2030-03-14T08:45:00Z",
        "start_geom": {"type": "Point", "coordinates": [-67.15, 18.205]},
        "end_geom": {"type": "Point", "coordinates": [-67.141, 18.21]}, "distance_km": 6.7,
    }


@pytest.fixture
def ping_body():
    return {
        "vehicle_id": 1, "ts": "2030-03-14T09:58:20Z",
        "geom": {"type": "Point", "coordinates": [-67.1453, 18.2011]},
        "speed_kph": 42.8, "heading_deg": 185.4,
    }
