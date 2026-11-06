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



# ---------------------------------------------------
def create_driver(payload):

    with connection() as conn, conn.cursor() as cur:

        # Lock the table to prevent duplicate IDs
        cur.execute("""
            LOCK TABLE public.driver IN EXCLUSIVE MODE
        """)

        # Find the next available driver ID
        cur.execute("""
            SELECT COALESCE(MAX(driver_id), 0) + 1 AS next_id
            FROM public.driver
        """)

        next_id = cur.fetchone()["next_id"]

        # Insert driver with generated ID
        cur.execute(
            sql.SQL("""
                INSERT INTO {} (
                    driver_id,
                    first_name,
                    last_name,
                    license_number,
                    hired_at
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING
                    driver_id,
                    first_name,
                    last_name,
                    license_number,
                    hired_at
            """).format(
                table("driver")
            ),
            (
                next_id,
                payload["first_name"],
                payload["last_name"],
                payload["license_number"],
                payload["hired_at"]
            )
        )

        driver = cur.fetchone()

    return normalize_record(driver)



# -----------------------------------------------------
def update_driver(driver_id, payload):

    assignments = []
    values = []

    for field, value in payload.items():

        assignments.append(
            sql.SQL("{} = %s").format(
                sql.Identifier(field)
            )
        )

        values.append(value)

    query = sql.SQL("""
        UPDATE {}
        SET {}
        WHERE driver_id = %s
        RETURNING
            driver_id,
            first_name,
            last_name,
            license_number,
            hired_at
    """).format(
        table("driver"),
        sql.SQL(", ").join(assignments)
    )

    values.append(driver_id)

    with connection() as conn, conn.cursor() as cur:

        cur.execute(query, values)

        driver = cur.fetchone()

    return normalize_record(driver)


# ------------------------------------------------
def delete_driver(driver_id):

    query = sql.SQL("""
        DELETE FROM {}
        WHERE driver_id = %s
        RETURNING driver_id
    """).format(
        table("driver")
    )

    with connection() as conn, conn.cursor() as cur:

        cur.execute(
            query,
            (driver_id,)
        )

        return cur.fetchone() is not None
