from fastapi import HTTPException

from models import parking_dao


def list_parking_areas(limit: int, offset: int) -> dict:
    """Return a paginated list of parking areas."""

    areas = parking_dao.list_parking_areas(limit, offset)

    return {
        "count": len(areas),
        "limit": limit,
        "offset": offset,
        "parking_areas": areas
    }


def get_parking_area(parking_area_id: int) -> dict:
    """Return a parking area or raise HTTP 404."""

    area = parking_dao.get_parking_area_by_id(parking_area_id)

    if area is None:
        raise HTTPException(
            status_code=404,
            detail="Parking area not found"
        )

    return area
