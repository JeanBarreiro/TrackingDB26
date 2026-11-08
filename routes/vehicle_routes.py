from fastapi import APIRouter, Body, Query

from controllers import vehicle_controller

from controllers.validation import (
    parse_pagination,
    parse_id
)


router = APIRouter(
    prefix="/api/v1/vehicles",
    tags=["Vehicles"]
)


@router.post("", status_code=201)
def create_vehicle(body: dict = Body(...)):

    return vehicle_controller.create_vehicle(body)


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


@router.get("/{vehicle_id}/current-location")
def get_current_location(vehicle_id: str):
    return vehicle_controller.VehicleController().get_current_location(
        parse_id(vehicle_id, "vehicle_id")
    )


@router.get("/{vehicle_id}")
def get_vehicle(vehicle_id: str):

    return vehicle_controller.get_vehicle(
        parse_id(vehicle_id, "vehicle_id")
    )


@router.put("/{vehicle_id}")
def update_vehicle(
    vehicle_id: str,
    body: dict = Body(...)
):

    return vehicle_controller.update_vehicle(
        parse_id(vehicle_id, "vehicle_id"),
        body
    )


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: str):

    return vehicle_controller.delete_vehicle(
        parse_id(vehicle_id, "vehicle_id")
    )
