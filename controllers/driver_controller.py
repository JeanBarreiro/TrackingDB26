import re
import psycopg

from datetime import datetime
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


# ---------------------------------------------------
def create_driver(payload):

    allowed_fields = {
        "first_name",
        "last_name",
        "license_number",
        "hired_at"
    }

    required_fields = {
        "first_name",
        "last_name",
        "license_number",
        "hired_at"
    }

    # Validate payload structure
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or invalid payload shape."
        )

    if not set(payload).issubset(allowed_fields):
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or invalid payload shape."
        )

    # Validate required fields
    if not required_fields.issubset(payload):
        raise HTTPException(
            status_code=422,
            detail="A required field is null or invalid."
        )

    # Validate first_name, last_name and license_number
    for field in (
        "first_name",
        "last_name",
        "license_number"
    ):

        value = payload[field]

        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise HTTPException(
                status_code=422,
                detail="A required field is null or invalid."
            )

        payload[field] = value.strip()

    # Validate hired_at (RFC 3339)
    hired_at = payload["hired_at"]

    if not isinstance(hired_at, str):
        raise HTTPException(
            status_code=422,
            detail="A required field is null or invalid."
        )

    hired_at = hired_at.strip()

    rfc3339_pattern = (
        r"^\d{4}-\d{2}-\d{2}T"
        r"\d{2}:\d{2}:\d{2}"
        r"(?:\.\d+)?"
        r"(?:Z|[+-]\d{2}:\d{2})$"
    )

    if not re.fullmatch(rfc3339_pattern, hired_at):
        raise HTTPException(
            status_code=422,
            detail="A required field is null or invalid."
        )

    try:
        payload["hired_at"] = datetime.fromisoformat(
            hired_at.replace("Z", "+00:00")
        )

    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="A required field is null or invalid."
        )

    # Insert driver
    try:
        return driver_dao.create_driver(payload)

    except psycopg.errors.UniqueViolation as exc:
        raise HTTPException(
            status_code=409,
            detail="license_number already exists."
        ) from exc


# ---------------------------------------------------
def update_driver(driver_id, payload):

    allowed_fields = {
        "first_name",
        "last_name",
        "license_number",
        "hired_at"
    }

    if not isinstance(payload, dict) or not payload:
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or empty update payload."
        )

    if not set(payload).issubset(allowed_fields):
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or empty update payload."
        )

    for field in (
        "first_name",
        "last_name",
        "license_number"
    ):

        if field in payload:

            value = payload[field]

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise HTTPException(
                    status_code=422,
                    detail="A supplied field is null or invalid."
                )

            payload[field] = value.strip()

    if "hired_at" in payload:

        hired_at = payload["hired_at"]

        if not isinstance(hired_at, str):
            raise HTTPException(
                status_code=422,
                detail="A supplied field is null or invalid."
            )

        hired_at = hired_at.strip()

        rfc3339_pattern = (
            r"^\d{4}-\d{2}-\d{2}T"
            r"\d{2}:\d{2}:\d{2}"
            r"(?:\.\d+)?"
            r"(?:Z|[+-]\d{2}:\d{2})$"
        )

        if not re.fullmatch(rfc3339_pattern, hired_at):
            raise HTTPException(
                status_code=422,
                detail="A supplied field is null or invalid."
            )

        try:
            payload["hired_at"] = datetime.fromisoformat(
                hired_at.replace("Z", "+00:00")
            )

        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="A supplied field is null or invalid."
            )

    # Update driver
    try:

        result = driver_dao.update_driver(
            driver_id,
            payload
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Driver does not exist."
            )

        return result

    except psycopg.errors.UniqueViolation as exc:
        raise HTTPException(
            status_code=409,
            detail="license_number already exists."
        ) from exc


# ----------------------------------------------
def delete_driver(driver_id):

    try:

        deleted = driver_dao.delete_driver(driver_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Driver does not exist."
            )

        return {
            "message": "Driver deleted successfully.",
            "driver_id": driver_id
        }

    except psycopg.errors.ForeignKeyViolation as exc:
        raise HTTPException(
            status_code=409,
            detail="The driver is referenced by a vehicle assignment."
        ) from exc
