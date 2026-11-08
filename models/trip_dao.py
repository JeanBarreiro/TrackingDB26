from psycopg import sql

from models.db import table

TRIP_COLUMNS = sql.SQL("""
    trip_id, vehicle_id, start_ts, end_ts,
    ST_AsGeoJSON(start_geom, 15)::json AS start_geom,
    ST_AsGeoJSON(end_geom, 15)::json AS end_geom, distance_km
""")


def vehicle_exists(conn, vehicle_id):
    return conn.execute(
        sql.SQL("SELECT 1 FROM {} WHERE vehicle_id = %s").format(table("vehicle")),
        (vehicle_id,)
    ).fetchone() is not None


def get_by_id(conn, trip_id, lock=False):
    return conn.execute(sql.SQL("SELECT {} FROM {} WHERE trip_id = %s{}").format(
        TRIP_COLUMNS, table("trip"), sql.SQL(" FOR UPDATE" if lock else "")
    ), (trip_id,)).fetchone()


def get_trips(conn, limit, offset, vehicle_id=None, start=None, end=None, for_vehicle=False):
    conditions, values = [], []
    if vehicle_id is not None:
        conditions.append(sql.SQL("vehicle_id = %s"))
        values.append(vehicle_id)
    if start is not None:
        conditions.append(sql.SQL("end_ts >= %s"))
        values.append(start)
    if end is not None:
        conditions.append(sql.SQL("start_ts <= %s"))
        values.append(end)
    where = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conditions) if conditions else sql.SQL("")
    count = conn.execute(
        sql.SQL("SELECT count(*) AS count FROM {}{}").format(table("trip"), where), values
    ).fetchone()["count"]
    columns = sql.SQL("trip_id, start_ts, end_ts, distance_km" if for_vehicle else
                      "trip_id, vehicle_id, start_ts, end_ts, distance_km")
    rows = conn.execute(sql.SQL("""
        SELECT {} FROM {}{} ORDER BY start_ts, trip_id LIMIT %s OFFSET %s
    """).format(columns, table("trip"), where), [*values, limit, offset]).fetchall()
    return rows, count


def create_trip(conn, payload):
    conn.execute(sql.SQL("LOCK TABLE {} IN EXCLUSIVE MODE").format(table("trip")))
    trip_id = conn.execute(sql.SQL(
        "SELECT COALESCE(MAX(trip_id), 0) + 1 AS next_id FROM {}"
    ).format(table("trip"))).fetchone()["next_id"]
    return conn.execute(sql.SQL("""
        INSERT INTO {} (trip_id, vehicle_id, start_ts, end_ts, start_geom, end_geom, distance_km)
        VALUES (%s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326),
                ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), %s)
        RETURNING {}
    """).format(table("trip"), TRIP_COLUMNS), (
        trip_id, payload["vehicle_id"], payload["start_ts"], payload["end_ts"],
        payload.get("start_geom"), payload.get("end_geom"), payload.get("distance_km")
    )).fetchone()


def update_trip(conn, trip_id, payload):
    assignments = []
    for field in payload:
        expression = "{} = ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)" if field in {"start_geom", "end_geom"} else "{} = %s"
        assignments.append(sql.SQL(expression).format(sql.Identifier(field)))
    return conn.execute(sql.SQL("UPDATE {} SET {} WHERE trip_id = %s RETURNING {}").format(
        table("trip"), sql.SQL(", ").join(assignments), TRIP_COLUMNS
    ), [*payload.values(), trip_id]).fetchone()


def delete_trip(conn, trip_id):
    return conn.execute(sql.SQL("DELETE FROM {} WHERE trip_id = %s RETURNING trip_id").format(
        table("trip")
    ), (trip_id,)).fetchone() is not None
