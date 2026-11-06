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

# ------------------------------------------
def create_vehicle(payload):

    fields = list(payload)

    with connection() as conn, conn.cursor() as cur:

        # Lock the table to prevent duplicate IDs
        cur.execute("""
            LOCK TABLE public.vehicle IN EXCLUSIVE MODE
        """)

        # Find the next available vehicle ID
        cur.execute("""
            SELECT COALESCE(MAX(vehicle_id), 0) + 1 AS next_id
            FROM public.vehicle
        """)

        next_id = cur.fetchone()["next_id"]

        # Add vehicle_id to the INSERT fields
        fields.insert(0, "vehicle_id")

        values = [
            next_id,
            *[payload[field] for field in payload]
        ]

        columns = sql.SQL(", ").join(
            sql.Identifier(field) for field in fields
        )

        placeholders = sql.SQL(", ").join(
            sql.Placeholder() for _ in fields
        )

        query = sql.SQL("""
            INSERT INTO {} ({})
            VALUES ({})
            RETURNING
                vehicle_id,
                vehicle_type_id,
                vehicle_status_id,
                plate_number,
                make,
                model,
                year,
                created_at
        """).format(
            table("vehicle"),
            columns,
            placeholders
        )

        cur.execute(query, values)

        vehicle = cur.fetchone()

    return normalize_record(vehicle)

# ------------------------------------------------------
def update_vehicle(vehicle_id, payload):

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
        WHERE vehicle_id = %s
        RETURNING
            vehicle_id,
            vehicle_type_id,
            vehicle_status_id,
            plate_number,
            make,
            model,
            year,
            created_at
    """).format(
        table("vehicle"),
        sql.SQL(", ").join(assignments)
    )

    values.append(vehicle_id)

    with connection() as conn, conn.cursor() as cur:

        cur.execute(query, values)

        vehicle = cur.fetchone()

    return normalize_record(vehicle)

# --------------------------------------------------

def delete_vehicle(vehicle_id):

    query = sql.SQL("""
        DELETE FROM {}
        WHERE vehicle_id = %s
        RETURNING vehicle_id
    """).format(
        table("vehicle")
    )

    with connection() as conn, conn.cursor() as cur:

        cur.execute(
            query,
            (vehicle_id,)
        )

        return cur.fetchone() is not None

