import json

from psycopg import sql

from models.db import connection, table, normalize_record


def _filters(name=None, bbox=None):
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

    if clauses:
        where = (
            sql.SQL(" WHERE ")
            + sql.SQL(" AND ").join(clauses)
        )
    else:
        where = sql.SQL("")

    return where, values


def list_parking_areas(limit, offset, name=None, bbox=None):
    where, values = _filters(name, bbox)
    tbl = table("parking_area")

    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                "SELECT count(*) AS n FROM {}{}"
            ).format(tbl, where),
            values
        )
        count = cur.fetchone()["n"]

        cur.execute(
            sql.SQL("""
                SELECT
                    parking_area_id,
                    name,
                    capacity,
                    created_at
                FROM {}{}
                ORDER BY parking_area_id
                LIMIT %s OFFSET %s
            """).format(tbl, where),
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


def get_parking_area_by_id(parking_area_id):
    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            sql.SQL("""
                SELECT
                    parking_area_id,
                    name,
                    capacity,
                    ST_AsGeoJSON(geom)::json AS geom,
                    created_at
                FROM {}
                WHERE parking_area_id = %s
            """).format(table("parking_area")),
            (parking_area_id,)
        )

        return normalize_record(cur.fetchone())


def create_parking_area(payload):
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
        RETURNING parking_area_id
    """).format(
        table("parking_area"),
        cols,
        expressions
    )

    with connection() as conn, conn.cursor() as cur:
        cur.execute(query, values)
        new_id = cur.fetchone()["parking_area_id"]

    return get_parking_area_by_id(new_id)


def update_parking_area(parking_area_id, payload):
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
        WHERE parking_area_id = %s
        RETURNING parking_area_id
    """).format(
        table("parking_area"),
        sql.SQL(",").join(assignments)
    )

    with connection() as conn, conn.cursor() as cur:
        cur.execute(query, [*values, parking_area_id])
        found = cur.fetchone()

    if found:
        return get_parking_area_by_id(parking_area_id)

    return None


def delete_parking_area(parking_area_id):
    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            sql.SQL("""
                DELETE FROM {}
                WHERE parking_area_id = %s
                RETURNING parking_area_id
            """).format(table("parking_area")),
            (parking_area_id,)
        )

        return cur.fetchone() is not None
