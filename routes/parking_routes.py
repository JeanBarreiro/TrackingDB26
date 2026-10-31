from fastapi import APIRouter, Path, Query

from controllers import parking_controller


router = APIRouter(
    prefix="/api/v1/parking-areas",
    tags=["Parking Areas"]
)


@router.get("")
def read_parking_areas(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    return parking_controller.list_parking_areas(
        limit,
        offset
    )


@router.get("/{parking_area_id}")
def read_parking_area(
    parking_area_id: int = Path(ge=1)
):
    return parking_controller.get_parking_area(
        parking_area_id
    )
