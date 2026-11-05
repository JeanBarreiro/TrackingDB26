from fastapi import HTTPException

from models import driver_dao


def get_drivers(
    limit,
    offset,
    name=None,
    license_number=None
):
    return driver_dao.get_drivers(
        limit,
        offset,
        name,
        license_number
    )


def get_driver(driver_id):

    result = driver_dao.get_by_id(driver_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Driver does not exist"
        )

    return result