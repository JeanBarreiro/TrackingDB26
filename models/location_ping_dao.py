from psycopg import sql

from models.db import table

PING_COLUMNS = sql.SQL("""
    ping_id, vehicle_id, ts, ST_AsGeoJSON(geom, 15)::json AS geom, speed_kph, heading_deg
""")


def vehicle_exists(conn, vehicle_id):
    return conn.execute(
        sql.SQL("SELECT 1 FROM {} WHERE vehicle_id = %s").format(table("vehicle")),
        (vehicle_id,)
    ).fetchone() is not None


def get_by_id(conn, ping_id, lock=False):
    return conn.execute(sql.SQL("SELECT {} FROM {} WHERE ping_id = %s{}").format(
        PING_COLUMNS, table("location_ping"), sql.SQL(" FOR UPDATE" if lock else "")
    ), (ping_id,)).fetchone()


def get_pings(conn, limit, offset, vehicle_id=None, start=None, end=None, bbox=None, for_vehicle=False):
    conditions, values = [], []
    if vehicle_id is not None:
        conditions.append(sql.SQL("vehicle_id = %s"))
        values.append(vehicle_id)
    if start is not None:
        conditions.append(sql.SQL("ts >= %s"))
        values.append(start)
    if end is not None:
        conditions.append(sql.SQL("ts <= %s"))
        values.append(end)
    if bbox is not None:
        conditions.append(sql.SQL("ST_Intersects(geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326))"))
        values.extend(bbox)
    where = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conditions) if conditions else sql.SQL("")
    count = conn.execute(
        sql.SQL("SELECT count(*) AS count FROM {}{}").format(table("location_ping"), where), values
    ).fetchone()["count"]
    columns = sql.SQL("ping_id, ts, ST_AsGeoJSON(geom, 15)::json AS geom, speed_kph, heading_deg"
                      if for_vehicle else "ping_id, vehicle_id, ts, speed_kph, heading_deg")
    rows = conn.execute(sql.SQL("""
        SELECT {} FROM {}{} ORDER BY ts, ping_id LIMIT %s OFFSET %s
    """).format(columns, table("location_ping"), where), [*values, limit, offset]).fetchall()
    return rows, count


def create_ping(conn, payload):
    conn.execute(sql.SQL("LOCK TABLE {} IN EXCLUSIVE MODE").format(table("location_ping")))
    ping_id = conn.execute(sql.SQL(
        "SELECT COALESCE(MAX(ping_id), 0) + 1 AS next_id FROM {}"
    ).format(table("location_ping"))).fetchone()["next_id"]
    return conn.execute(sql.SQL("""
        INSERT INTO {} (ping_id, vehicle_id, ts, geom, speed_kph, heading_deg)
        VALUES (%s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), %s, %s)
        RETURNING {}
    """).format(table("location_ping"), PING_COLUMNS), (
        ping_id, payload["vehicle_id"], payload["ts"], payload["geom"],
        payload.get("speed_kph"), payload.get("heading_deg")
    )).fetchone()


def update_ping(conn, ping_id, payload):
    assignments = []
    for field in payload:
        expression = "{} = ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)" if field == "geom" else "{} = %s"
        assignments.append(sql.SQL(expression).format(sql.Identifier(field)))
    return conn.execute(sql.SQL("UPDATE {} SET {} WHERE ping_id = %s RETURNING {}").format(
        table("location_ping"), sql.SQL(", ").join(assignments), PING_COLUMNS
    ), [*payload.values(), ping_id]).fetchone()


def delete_ping(conn, ping_id):
    return conn.execute(sql.SQL("DELETE FROM {} WHERE ping_id = %s RETURNING ping_id").format(
        table("location_ping")
    ), (ping_id,)).fetchone() is not None
