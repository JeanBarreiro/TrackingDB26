from fastapi import APIRouter, HTTPException, Query, Depends
from database import get_db

router = APIRouter()

STATUS_MAP = {
    "active": 1,
    "inactive": 2,
}


@router.get("/api/v1/vehicles")
def get_vehicles(
    limit: int = Query(default=20, ge=0),
    offset: int = Query(default=0, ge=0),
    status: str = None,
    plate_number: str = None,
    conn = Depends(get_db()),
):
    conditions = []
    params = []

    if plate_number:
        conditions.append("plate_number ILIKE %s")
        params.append(f"%{plate_number}%")

    if status is not None:
        normalized_status = status.strip().lower()

        if normalized_status in STATUS_MAP:
            status_id = STATUS_MAP[normalized_status]
        elif normalized_status.isdigit():
            status_id = int(normalized_status)
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid status parameter",
            )

        conditions.append("vehicle_status_id = %s")
        params.append(status_id)

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