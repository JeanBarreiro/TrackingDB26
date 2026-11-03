from fastapi import APIRouter, Body, Query

from controllers import parking_controller
from controllers.validation import (
    parse_pagination,
    parse_bbox,
    parse_id
)


router = APIRouter(
    prefix="/api/v1/parking-areas",
    tags=["Parking Areas"]
)


@router.post("", status_code=201)
def create_parking_area(body: dict = Body(...)):
    return parking_controller.create_parking_area(body)


@router.get("")
def list_parking_areas(
    limit: str = Query("20"),
    offset: str = Query("0"),
    name: str | None = None,
    bbox: str | None = None
):
    n_limit, n_offset = parse_pagination(limit, offset)
    bounds = parse_bbox(bbox)

    return parking_controller.list_parking_areas(
        n_limit,
        n_offset,
        name,
        bounds
    )


@router.get("/{parking_area_id}")
def get_parking_area(parking_area_id: str):
    return parking_controller.get_parking_area(
        parse_id(parking_area_id, "parking_area_id")
    )


@router.put("/{parking_area_id}")
def update_parking_area(
    parking_area_id: str,
    body: dict = Body(...)
):
    return parking_controller.update_parking_area(
        parse_id(parking_area_id, "parking_area_id"),
        body
    )


@router.delete("/{parking_area_id}")
def delete_parking_area(parking_area_id: str):
    return parking_controller.delete_parking_area(
        parse_id(parking_area_id, "parking_area_id")
    )
