from fastapi import APIRouter, Query

from controllers import driver_controller

from controllers.validation import (
    parse_pagination,
    parse_id
)


router = APIRouter(
    prefix="/api/v1/drivers",
    tags=["Drivers"]
)


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