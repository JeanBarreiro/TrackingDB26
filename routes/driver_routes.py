
from fastapi import APIRouter, Query, Body

from controllers import driver_controller

from controllers.validation import (
    parse_pagination,
    parse_id
)


router = APIRouter(
    prefix="/api/v1/drivers",
    tags=["Drivers"]
)


@router.post("", status_code=201)
def create_driver(body: dict = Body(...)):

    return driver_controller.create_driver(body)


@router.get("")
def get_drivers(
    limit: str = Query("20"),
    offset: str = Query("0"),
    name: str | None = None,
    license_number: str | None = None
):

    n_limit, n_offset = parse_pagination(
        limit,
        offset
    )

    return driver_controller.get_drivers(
        n_limit,
        n_offset,
        name,
        license_number
    )


@router.get("/{driver_id}")
def get_driver(driver_id: str):

    return driver_controller.get_driver(
        parse_id(driver_id, "driver_id")
    )


@router.put("/{driver_id}")
def update_driver(
    driver_id: str,
    body: dict = Body(...)
):

    return driver_controller.update_driver(
        parse_id(driver_id, "driver_id"),
        body
    )

@router.delete("/{driver_id}")
def delete_driver(driver_id: str):

    return driver_controller.delete_driver(
        parse_id(driver_id, "driver_id")
    )
