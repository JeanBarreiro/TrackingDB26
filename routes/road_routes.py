from fastapi import APIRouter, Path, Query

from controllers import road_controller


router = APIRouter(
    prefix="/api/v1/road-segments",
    tags=["Road Segments"]
)


@router.get("")
def read_roads(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    return road_controller.list_roads(
        limit,
        offset
    )


@router.get("/{road_id}")
def read_road(
    road_id: int = Path(ge=1)
):
    return road_controller.get_road(
        road_id
    )
