from fastapi import HTTPException

from models import road_dao


def list_roads(limit: int, offset: int) -> dict:
    """Return a paginated list of road segments."""

    roads = road_dao.list_roads(limit, offset)

    return {
        "count": len(roads),
        "limit": limit,
        "offset": offset,
        "roads": roads
    }


def get_road(road_id: int) -> dict:
    """Return a road segment or raise HTTP 404."""

    road = road_dao.get_road_by_id(road_id)

    if road is None:
        raise HTTPException(
            status_code=404,
            detail="Road segment not found"
        )

    return road
