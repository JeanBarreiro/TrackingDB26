from fastapi import APIRouter, Query

from controllers import vehicle_controller

from controllers.validation import (
    parse_pagination,
    parse_id
)


router = APIRouter(
    prefix="/api/v1/vehicles",
    tags=["Vehicles"]
)


@router.get("")
def get_vehicles(
    limit: str = Query("20"),
    offset: str = Query("0"),
    status: str | None = None,
    plate_number: str | None = None
):

    n_limit, n_offset = parse_pagination(
        limit,
        offset
    )

    return vehicle_controller.get_vehicles(
        n_limit,
        n_offset,
        status,
        plate_number
    )


@router.get("/{vehicle_id}")
def get_vehicle(vehicle_id: str):

    return vehicle_controller.get_vehicle(
        parse_id(vehicle_id, "vehicle_id")
    )