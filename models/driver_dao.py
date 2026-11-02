class DriverDAO:

    @staticmethod
    def get_drivers(conn, limit=20, offset=0, name=None, license_number=None):

        conditions = []
        params = []

        if name:
            conditions.append(
                "(first_name ILIKE %s OR last_name ILIKE %s)"
            )
            params.extend([f"%{name}%", f"%{name}%"])

        if license_number:
            conditions.append("license_number ILIKE %s")
            params.append(f"%{license_number}%")

        where_clause = ""

        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        with conn.cursor() as cur:

            cur.execute("SET TRANSACTION READ ONLY")

            cur.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM public.driver
                {where_clause}
                """,
                params,
            )

            count = cur.fetchone()["count"]

            cur.execute(
                f"""
                SELECT
                    driver_id,
                    first_name,
                    last_name,
                    license_number,
                    hired_at
                FROM public.driver
                {where_clause}
                ORDER BY driver_id
                LIMIT %s OFFSET %s
                """,
                params + [limit, offset],
            )

            drivers = cur.fetchall()

        return {
            "items": drivers,
            "limit": limit,
            "offset": offset,
            "count": count,
        }

    @staticmethod
    def get_by_id(conn, driver_id: int):

        with conn.cursor() as cur:

            cur.execute("SET TRANSACTION READ ONLY")

            cur.execute(
                """
                SELECT
                    driver_id,
                    first_name,
                    last_name,
                    license_number,
                    hired_at
                FROM public.driver
                WHERE driver_id = %s
                """,
                [driver_id],
            )

            return cur.fetchone()