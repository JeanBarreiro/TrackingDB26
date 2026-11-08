from psycopg import sql
from models.db import connection, table, normalize_record

def get_vehicle_assignments(
    limit,
    offset,
    vehicle_id=None,
    driver_id=None,
    active=None
):
    conditions = []
    params = []

    if vehicle_id is not None:
        conditions.append(sql.SQL("vehicle_id = %s"))
        params.append(vehicle_id)

    if driver_id is not None:
        conditions.append(sql.SQL("driver_id = %s"))
        params.append(driver_id)

    if active is True:
        conditions.append(sql.SQL("assigned_to IS NULL"))

    elif active is False:
        conditions.append(sql.SQL("assigned_to IS NOT NULL"))

    where_clause = sql.SQL("")

    if conditions:
        where_clause = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conditions)

    query = sql.SQL("""
        SELECT
            assignment_id,
            vehicle_id,
            driver_id,
            assigned_from,
            assigned_to
        FROM {}
    """).format(table("vehicle_assignment")) + where_clause + sql.SQL("""
        ORDER BY assignment_id ASC
        LIMIT %s OFFSET %s
    """)

    count_query = sql.SQL("""
        SELECT COUNT(*) AS count
        FROM {}
    """).format(table("vehicle_assignment")) + where_clause

    with connection() as conn, conn.cursor() as cur:

        cur.execute(count_query, params)
        count = cur.fetchone()["count"]

        cur.execute(query, params + [limit, offset])
        rows = cur.fetchall()

    return {
        "items": [normalize_record(row) for row in rows],
        "limit": limit,
        "offset": offset,
        "count": count
    }


def get_by_id(assignment_id):
    query = sql.SQL("""
        SELECT
            assignment_id,
            vehicle_id,
            driver_id,
            assigned_from,
            assigned_to
        FROM {}
        WHERE assignment_id = %s
    """).format(table("vehicle_assignment"))

    with connection() as conn, conn.cursor() as cur:
        cur.execute(query, (assignment_id,))
        result = cur.fetchone()

    if result is None:
        return None

    return normalize_record(result)


def create_vehicle_assignment(payload):
    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            sql.SQL("SELECT 1 FROM {} WHERE vehicle_id = %s").format(
                table("vehicle")
            ),
            (payload["vehicle_id"],)
        )

        if cur.fetchone() is None:
            return None

        cur.execute(
            sql.SQL("SELECT 1 FROM {} WHERE driver_id = %s").format(
                table("driver")
            ),
            (payload["driver_id"],)
        )

        if cur.fetchone() is None:
            return None

        cur.execute(
            sql.SQL("LOCK TABLE {} IN EXCLUSIVE MODE").format(
                table("vehicle_assignment")
            )
        )

        cur.execute(
            sql.SQL("""
                SELECT COALESCE(MAX(assignment_id), 0) + 1 AS next_id
                FROM {}
            """).format(table("vehicle_assignment"))
        )

        next_id = cur.fetchone()["next_id"]
        cur.execute(
            sql.SQL("""
                INSERT INTO {} (
                    assignment_id,
                    vehicle_id,
                    driver_id,
                    assigned_from,
                    assigned_to
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING
                    assignment_id,
                    vehicle_id,
                    driver_id,
                    assigned_from,
                    assigned_to
            """).format(table("vehicle_assignment")),
            (
                next_id,
                payload["vehicle_id"],
                payload["driver_id"],
                payload["assigned_from"],
                payload["assigned_to"]
            )
        )

        result = cur.fetchone()
    return normalize_record(result)

def update_vehicle_assignment(assignment_id, payload):
    assignments = []
    params = []

    for field, value in payload.items():
        assignments.append(
            sql.SQL("{} = %s").format(sql.Identifier(field))
        )
        params.append(value)

    params.append(assignment_id)
    query = sql.SQL("""
        UPDATE {}
        SET {}
        WHERE assignment_id = %s
        RETURNING
            assignment_id,
            vehicle_id,
            driver_id,
            assigned_from,
            assigned_to
    """).format(
        table("vehicle_assignment"),
        sql.SQL(", ").join(assignments)
    )

    with connection() as conn, conn.cursor() as cur:
        cur.execute(query, params)
        result = cur.fetchone()

    if result is None:
        return None

    return normalize_record(result)


def delete_vehicle_assignment(assignment_id):
    query = sql.SQL("""
        DELETE FROM {}
        WHERE assignment_id = %s
        RETURNING assignment_id
    """).format(table("vehicle_assignment"))

    with connection() as conn, conn.cursor() as cur:
        cur.execute(query, (assignment_id,))
        result = cur.fetchone()

    return result is not None
