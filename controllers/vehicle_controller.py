import psycopg

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


def create_vehicle(payload):

    allowed_fields = {
        "vehicle_type_id",
        "vehicle_status_id",
        "plate_number",
        "make",
        "model",
        "year"
    }

    required_fields = {
        "vehicle_type_id",
        "vehicle_status_id",
        "plate_number"
    }

    # Check payload structure
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or invalid payload shape."
        )

    if not required_fields.issubset(payload):
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or invalid payload shape."
        )

    if not set(payload).issubset(allowed_fields):
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or invalid payload shape."
        )

    # Validate foreign key IDs
    for field in (
        "vehicle_type_id",
        "vehicle_status_id"
    ):

        value = payload[field]

        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise HTTPException(
                status_code=400,
                detail="Malformed JSON or invalid payload shape."
            )

    # Validate plate number
    plate_number = payload["plate_number"]

    if not isinstance(plate_number, str):
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or invalid payload shape."
        )

    plate_number = plate_number.strip()

    if not plate_number:
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or invalid payload shape"
        )

    # Normalize optional text fields
    for field in ("make", "model"):

        if field in payload:

            value = payload[field]

            if value is not None and not isinstance(value, str):
                raise HTTPException(
                    status_code=400,
                    detail="Malformed JSON or invalid payload shape."
                )

            if isinstance(value, str):
                payload[field] = value.strip()

    # Validate year if provided
    if "year" in payload:

        year = payload["year"]

        if (
            not isinstance(year, int)
            or isinstance(year, bool)
            or not 1950 <= year <= 2100
        ):
            raise HTTPException(
                status_code=400,
                detail="year must be between 1950 and 2100"
            )

    payload["plate_number"] = plate_number
    existing_vehicles = vehicle_dao.get_vehicles(
        limit=1,
        offset=0,
        plate_number=payload["plate_number"]
    )

    if existing_vehicles["count"] > 0:
        raise HTTPException(
            status_code=409,
            detail="plate_number already exists"
        )

    try:
        return vehicle_dao.create_vehicle(payload)

    except psycopg.errors.ForeignKeyViolation as exc:
        raise HTTPException(
            status_code=404,
            detail="Referenced vehicle_type_id or vehicle_status_id does not exist"
        ) from exc

    except psycopg.errors.UniqueViolation as exc:
        raise HTTPException(
            status_code=409,
            detail="plate_number already exists"
        ) from exc

# -----------------------------------------------------------------
def update_vehicle(vehicle_id, payload):

    allowed_fields = {
        "vehicle_type_id",
        "vehicle_status_id",
        "plate_number",
        "make",
        "model",
        "year"
    }

    if not isinstance(payload, dict) or not payload:
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or empty payload."
        )

    if not set(payload).issubset(allowed_fields):
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or empty payload."
        )

    # Validate foreign key IDs
    for field in ("vehicle_type_id", "vehicle_status_id"):
        if field in payload:
            value = payload[field]

            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value <= 0
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Malformed JSON or empty payload."
                )

    # Validate plate number
    if "plate_number" in payload:
        plate_number = payload["plate_number"]

        if not isinstance(plate_number, str):
            raise HTTPException(
                status_code=400,
                detail="Malformed JSON or empty payload."
            )

        plate_number = plate_number.strip()

        if not plate_number:
            raise HTTPException(
                status_code=400,
                detail="Malformed JSON or empty payload."
            )

        # Check for duplicate plate numbers
        existing_vehicles = vehicle_dao.get_vehicles(
            limit=1000,
            offset=0,
            plate_number=plate_number
        )

        for vehicle in existing_vehicles["items"]:
            if vehicle["vehicle_id"] != vehicle_id:
                raise HTTPException(
                    status_code=409,
                    detail="plate_number already exists."
                )

        payload["plate_number"] = plate_number

    # Validate optional text fields
    for field in ("make", "model"):
        if field in payload:
            value = payload[field]

            if value is not None and not isinstance(value, str):
                raise HTTPException(
                    status_code=400,
                    detail="Malformed JSON or empty payload."
                )

            if isinstance(value, str):
                payload[field] = value.strip()

    # Validate year
    if "year" in payload:
        year = payload["year"]

        if (
            not isinstance(year, int)
            or isinstance(year, bool)
            or not 1950 <= year <= 2100
        ):
            raise HTTPException(
                status_code=400,
                detail="Malformed JSON or empty payload"
            )

    try:
        result = vehicle_dao.update_vehicle(vehicle_id, payload)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="vehicle_id or referenced foreign key does not exist."
            )

        return result

    except psycopg.errors.ForeignKeyViolation as exc:
        raise HTTPException(
            status_code=404,
            detail="vehicle_id or referenced foreign key does not exist"
        ) from exc

    except psycopg.errors.UniqueViolation as exc:
        raise HTTPException(
            status_code=409,
            detail="plate_number already exists"
        ) from exc

# ---------------------------------------------------
def delete_vehicle(vehicle_id):

    try:

        deleted = vehicle_dao.delete_vehicle(vehicle_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Vehicle does not exist"
            )

        return {
            "message": "Vehicle deleted successfully.",
            "vehicle_id": vehicle_id
        }

    except psycopg.errors.ForeignKeyViolation as exc:
        raise HTTPException(
            status_code=409,
            detail="Vehicle deletion blocked by foreign key constraints"
        ) from exc
