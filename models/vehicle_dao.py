class VehicleDAO:

    @staticmethod
    def get_all(conn, limit=20, offset=0, status=None, plate_number=None):

        conditions = []
        params = []

        if plate_number:
            conditions.append("plate_number ILIKE %s")
            params.append(f"%{plate_number}%")

        if status is not None:
            conditions.append("vehicle_status_id = %s")
            params.append(status)

        where_clause = ""

        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        with conn.cursor() as cur:

            cur.execute("SET TRANSACTION READ ONLY")

            cur.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM public.vehicle
                {where_clause}
                """,
                params,
            )

            count = cur.fetchone()["count"]

            cur.execute(
                f"""
                SELECT
                    vehicle_id,
                    plate_number,
                    make,
                    model,
                    year,
                    vehicle_type_id,
                    vehicle_status_id,
                    created_at
                FROM public.vehicle
                {where_clause}
                ORDER BY vehicle_id
                LIMIT %s OFFSET %s
                """,
                params + [limit, offset],
            )

            vehicles = cur.fetchall()

        return {
            "items": vehicles,
            "limit": limit,
            "offset": offset,
            "count": count,
        }


    @staticmethod
    def get_by_id(conn, vehicle_id: int):

        with conn.cursor() as cur:

            cur.execute("SET TRANSACTION READ ONLY")

            cur.execute(
                """
                SELECT
                    vehicle_id,
                    vehicle_type_id,
                    vehicle_status_id,
                    plate_number,
                    make,
                    model,
                    year,
                    created_at
                FROM public.vehicle
                WHERE vehicle_id = %s
                """,
                [vehicle_id],
            )

            return cur.fetchone()
