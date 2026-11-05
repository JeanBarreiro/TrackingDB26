import json

from psycopg import sql

from models.db import connection, table, normalize_record


def _filters(name=None, bbox=None, min_speed=None, max_speed=None):
    clauses = []
    values = []

    if name:
        clauses.append(sql.SQL("name ILIKE %s"))
        values.append(f"%{name}%")

    if bbox:
        clauses.append(
            sql.SQL(
                "ST_Intersects(geom, ST_MakeEnvelope(%s,%s,%s,%s,4326))"
            )
        )
        values.extend(bbox)

    if min_speed is not None:
        clauses.append(sql.SQL("speed_limit_kph >= %s"))
        values.append(min_speed)

    if max_speed is not None:
        clauses.append(sql.SQL("speed_limit_kph <= %s"))
        values.append(max_speed)

    if clauses:
        where = (
            sql.SQL(" WHERE ")
            + sql.SQL(" AND ").join(clauses)
        )
    else:
        where = sql.SQL("")

    return where, values


def list_roads(
    limit,
    offset,
    name=None,
    bbox=None,
    min_speed=None,
    max_speed=None
):
    where, values = _filters(
        name,
        bbox,
        min_speed,
        max_speed
    )

    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            sql.SQL("""
                SELECT count(*) AS n
                FROM {}{}
            """).format(table("road_segment"), where),
            values
        )

        count = cur.fetchone()["n"]

        cur.execute(
            sql.SQL("""
                SELECT
                    road_id,
                    name,
                    speed_limit_kph,
                    created_at
                FROM {}{}
                ORDER BY road_id
                LIMIT %s OFFSET %s
            """).format(table("road_segment"), where),
            [*values, limit, offset]
        )

        items = [
            normalize_record(x) for x in cur.fetchall()
        ]

    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "count": count
    }


def get_road_by_id(road_id):
    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            sql.SQL("""
                SELECT
                    road_id,
                    name,
                    speed_limit_kph,
                    is_oneway,
                    direction,
                    ST_AsGeoJSON(geom)::json AS geom,
                    created_at
                FROM {}
                WHERE road_id = %s
            """).format(table("road_segment")),
            (road_id,)
        )

        return normalize_record(cur.fetchone())


def create_road(payload):
    fields = list(payload)

    values = [
        json.dumps(payload[k]) if k == "geom" else payload[k]
        for k in fields
    ]

    cols = sql.SQL(",").join(
        sql.Identifier(k) for k in fields
    )

    expressions = sql.SQL(",").join(
        sql.SQL("ST_SetSRID(ST_GeomFromGeoJSON(%s),4326)")
        if k == "geom" else sql.SQL("%s")
        for k in fields
    )

    query = sql.SQL("""
        INSERT INTO {} ({})
        VALUES ({})
        RETURNING road_id
    """).format(
        table("road_segment"),
        cols,
        expressions
    )

    with connection() as conn, conn.cursor() as cur:
        cur.execute(query, values)
        new_id = cur.fetchone()["road_id"]

    return get_road_by_id(new_id)


def update_road(road_id, payload):
    assignments = []
    values = []

    for key, value in payload.items():
        if key == "geom":
            assignments.append(
                sql.SQL(
                    "geom = ST_SetSRID(ST_GeomFromGeoJSON(%s),4326)"
                )
            )
            values.append(json.dumps(value))
        else:
            assignments.append(
                sql.SQL("{} = %s").format(sql.Identifier(key))
            )
            values.append(value)

    query = sql.SQL("""
        UPDATE {}
        SET {}
        WHERE road_id = %s
        RETURNING road_id
    """).format(
        table("road_segment"),
        sql.SQL(",").join(assignments)
    )

    with connection() as conn, conn.cursor() as cur:
        cur.execute(query, [*values, road_id])
        found = cur.fetchone()

    if found:
        return get_road_by_id(road_id)

    return None


def delete_road(road_id):
    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            sql.SQL("""
                DELETE FROM {}
                WHERE road_id = %s
                RETURNING road_id
            """).format(table("road_segment")),
            (road_id,)
        )

        return cur.fetchone() is not None


def roads_geojson(
    limit,
    offset,
    name=None,
    min_speed=None,
    max_speed=None
):
    where, values = _filters(
        name=name,
        min_speed=min_speed,
        max_speed=max_speed
    )

    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            sql.SQL("""
                SELECT count(*) AS n
                FROM {}{}
            """).format(table("road_segment"), where),
            values
        )

        count = cur.fetchone()["n"]

        cur.execute(
            sql.SQL("""
                SELECT
                    road_id,
                    name,
                    speed_limit_kph,
                    is_oneway,
                    direction,
                    created_at,
                    ST_AsGeoJSON(geom)::json AS geom
                FROM {}{}
                ORDER BY road_id
                LIMIT %s OFFSET %s
            """).format(table("road_segment"), where),
            [*values, limit, offset]
        )

        rows = [
            normalize_record(x) for x in cur.fetchall()
        ]

    features = []

    for row in rows:
        geom = row.pop("geom")

        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": row
        })

    return {
        "type": "FeatureCollection",
        "count": count,
        "limit": limit,
        "offset": offset,
        "features": features
    }
