from psycopg import sql

from models.db import connection, table, normalize_record


def get_vehicles(
    limit=20,
    offset=0,
    status=None,
    plate_number=None
):

    conditions = []
    values = []

    if plate_number:

        conditions.append(
            sql.SQL("plate_number ILIKE %s")
        )

        values.append(f"%{plate_number}%")

    if status is not None:

        conditions.append(
            sql.SQL("vehicle_status_id = %s")
        )

        values.append(status)

    if conditions:
        where = (
            sql.SQL(" WHERE ")
            + sql.SQL(" AND ").join(conditions)
        )
    else:
        where = sql.SQL("")

    with connection() as conn, conn.cursor() as cur:

        cur.execute(
            sql.SQL("""
                SELECT COUNT(*) AS count
                FROM {}{}
            """).format(
                table("vehicle"),
                where
            ),
            values
        )

        count = cur.fetchone()["count"]

        cur.execute(
            sql.SQL("""
                SELECT
                    vehicle_id,
                    plate_number,
                    make,
                    model,
                    year,
                    vehicle_type_id,
                    vehicle_status_id,
                    created_at
                FROM {}{}
                ORDER BY vehicle_id
                LIMIT %s OFFSET %s
            """).format(
                table("vehicle"),
                where
            ),
            [*values, limit, offset]
        )

        vehicles = [
            normalize_record(row)
            for row in cur.fetchall()
        ]

    return {
        "items": vehicles,
        "limit": limit,
        "offset": offset,
        "count": count
    }


def get_by_id(vehicle_id):

    with connection() as conn, conn.cursor() as cur:

        cur.execute(
            sql.SQL("""
                SELECT
                    vehicle_id,
                    vehicle_type_id,
                    vehicle_status_id,
                    plate_number,
                    make,
                    model,
                    year,
                    created_at
                FROM {}
                WHERE vehicle_id = %s
            """).format(
                table("vehicle")
            ),
            (vehicle_id,)
        )

        return normalize_record(cur.fetchone())