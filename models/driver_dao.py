from psycopg import sql

from models.db import connection, table, normalize_record


def get_drivers(
    limit=20,
    offset=0,
    name=None,
    license_number=None
):

    conditions = []
    values = []

    if name:
        conditions.append(
            sql.SQL(
                "(first_name ILIKE %s OR last_name ILIKE %s)"
            )
        )

        values.extend([
            f"%{name}%",
            f"%{name}%"
        ])

    if license_number:
        conditions.append(
            sql.SQL("license_number ILIKE %s")
        )

        values.append(f"%{license_number}%")

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
                table("driver"),
                where
            ),
            values
        )

        count = cur.fetchone()["count"]

        cur.execute(
            sql.SQL("""
                SELECT
                    driver_id,
                    first_name,
                    last_name,
                    license_number,
                    hired_at
                FROM {}{}
                ORDER BY driver_id
                LIMIT %s OFFSET %s
            """).format(
                table("driver"),
                where
            ),
            [*values, limit, offset]
        )

        drivers = [
            normalize_record(row)
            for row in cur.fetchall()
        ]

    return {
        "items": drivers,
        "limit": limit,
        "offset": offset,
        "count": count
    }


def get_by_id(driver_id):

    with connection() as conn, conn.cursor() as cur:

        cur.execute(
            sql.SQL("""
                SELECT
                    driver_id,
                    first_name,
                    last_name,
                    license_number,
                    hired_at
                FROM {}
                WHERE driver_id = %s
            """).format(
                table("driver")
            ),
            (driver_id,)
        )

        return normalize_record(cur.fetchone())