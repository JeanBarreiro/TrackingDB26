from fastapi import HTTPException

from models import vehicle_dao


STATUS_MAP = {
    "active": 1,
    "inactive": 2,
}


def get_vehicles(
    limit,
    offset,
    status=None,
    plate_number=None
):

    status_id = None

    if status is not None:

        normalized_status = status.strip().lower()

        if normalized_status in STATUS_MAP:
            status_id = STATUS_MAP[normalized_status]

        elif normalized_status.isdigit():
            status_id = int(normalized_status)

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameter values"
            )

    return vehicle_dao.get_vehicles(
        limit,
        offset,
        status_id,
        plate_number
    )


def get_vehicle(vehicle_id):

    result = vehicle_dao.get_by_id(vehicle_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle does not exist"
        )

    return result