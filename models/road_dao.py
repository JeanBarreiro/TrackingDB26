import os

import psycopg
from psycopg.rows import dict_row


def list_roads(limit: int, offset: int) -> list[dict]:
    """Retrieve road segments with GeoJSON geometry."""

    query = """
        SELECT
            road_id,
            name,
            speed_limit_kph,
            is_oneway,
            direction,
            created_at,
            ST_AsGeoJSON(geom)::json AS geometry
        FROM public.road_segment
        ORDER BY road_id
        LIMIT %s OFFSET %s;
    """

    with psycopg.connect(
        os.environ["DATABASE_URL"],
        row_factory=dict_row
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (limit, offset))
            return cur.fetchall()


def get_road_by_id(road_id: int) -> dict | None:
    """Retrieve a road segment by its ID."""

    query = """
        SELECT
            road_id,
            name,
            speed_limit_kph,
            is_oneway,
            direction,
            created_at,
            ST_AsGeoJSON(geom)::json AS geometry
        FROM public.road_segment
        WHERE road_id = %s;
    """

    with psycopg.connect(
        os.environ["DATABASE_URL"],
        row_factory=dict_row
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (road_id,))
            return cur.fetchone()
