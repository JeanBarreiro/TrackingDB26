import re
from datetime import datetime
import psycopg

def get_vehicle_assignments(
    limit,
    offset,
    vehicle_id=None,
    driver_id=None,
    active=None
):
    try:
        limit = int(limit)
        offset = int(offset)

        if limit < 0 or offset < 0:
            raise ValueError()

        if vehicle_id is not None:
            vehicle_id = int(vehicle_id)

            if vehicle_id <= 0:
                raise ValueError()

        if driver_id is not None:
            driver_id = int(driver_id)

            if driver_id <= 0:
                raise ValueError()

        if active is not None:
            if isinstance(active, bool):
                pass
            elif isinstance(active, str):
                active = active.lower()

                if active == "true":
                    active = True
                elif active == "false":
                    active = False
                else:
                    raise ValueError()
            else:
                raise ValueError()

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid query parameter values."
        )

    return vehicle_assignment_dao.get_vehicle_assignments(
        limit,
        offset,
        vehicle_id,
        driver_id,
        active
    )


from fastapi import HTTPException
from models import vehicle_assignment_dao


def get_vehicle_assignment(assignment_id):
    result = vehicle_assignment_dao.get_by_id(assignment_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="assignment_id does not exist."
        )

    return result

# ----------------------------------------------------------
def parse_rfc3339(value):
    if not isinstance(value, str):
        raise ValueError()

    pattern = (
        r"^\d{4}-\d{2}-\d{2}T"
        r"\d{2}:\d{2}:\d{2}"
        r"(?:\.\d+)?"
        r"(?:Z|[+-]\d{2}:\d{2})$"
    )

    if not re.fullmatch(pattern, value):
        raise ValueError()

    return datetime.fromisoformat(value.replace("Z", "+00:00"))

# ------------------------------------------------------------------------
def create_vehicle_assignment(payload):
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or invalid payload shape."
        )

    required_fields = {
        "vehicle_id",
        "driver_id",
        "assigned_from"
    }

    allowed_fields = required_fields | {"assigned_to"}

    if not required_fields.issubset(payload.keys()):
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or invalid payload shape."
        )

    if not set(payload.keys()).issubset(allowed_fields):
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or invalid payload shape."
        )

    for field in ("vehicle_id", "driver_id"):
        value = payload[field]

        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise HTTPException(
                status_code=400,
                detail="Malformed JSON or invalid payload shape."
            )

    try:
        assigned_from = parse_rfc3339(payload["assigned_from"])
    except (ValueError, TypeError, OverflowError):
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON or invalid payload shape."
        )

    assigned_to = None

    if "assigned_to" in payload and payload["assigned_to"] is not None:
        try:
            assigned_to = parse_rfc3339(payload["assigned_to"])

            if assigned_to <= assigned_from:
                raise ValueError()

        except (ValueError, TypeError, OverflowError):
            raise HTTPException(
                status_code=422,
                detail="The assignment time interval is invalid."
            )

    validated_payload = {
        "vehicle_id": payload["vehicle_id"],
        "driver_id": payload["driver_id"],
        "assigned_from": assigned_from,
        "assigned_to": assigned_to
    }

    try:
        result = vehicle_assignment_dao.create_vehicle_assignment(
            validated_payload
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Referenced vehicle_id or driver_id does not exist."
            )

        return result

    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(
            status_code=404,
            detail="Referenced vehicle_id or driver_id does not exist."
        )



def update_vehicle_assignment(assignment_id, payload):
    if not isinstance(payload, dict) or not payload:
        raise HTTPException(status_code=400, detail="Malformed JSON or empty update payload.")

    allowed_fields = {
        "vehicle_id",
        "driver_id",
        "assigned_from",
        "assigned_to"
    }

    if not set(payload.keys()).issubset(allowed_fields):
        raise HTTPException(status_code=400, detail="Malformed JSON or empty update payload.")

    existing = vehicle_assignment_dao.get_by_id(assignment_id)

    if existing is None:
        raise HTTPException(status_code=404, detail="assignment_id or a referenced foreign key does not exist.")

    for field in ("vehicle_id", "driver_id"):
        if field in payload:
            value = payload[field]

            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value <= 0
            ):
                raise HTTPException(status_code=400, detail="Malformed JSON or empty update payload.")

    if "assigned_from" in payload and payload["assigned_from"] is None:
        raise HTTPException(status_code=400, detail="Malformed JSON or empty update payload.")

    if "assigned_to" in payload and payload["assigned_to"] is not None:
        try:
            payload_assigned_to = parse_rfc3339(payload["assigned_to"])
        except (ValueError, TypeError, OverflowError):
            raise HTTPException(status_code=422, detail="The resulting assignment interval is invalid.")

    if "assigned_from" in payload:
        try:
            payload_assigned_from = parse_rfc3339(payload["assigned_from"])
        except (ValueError, TypeError, OverflowError):
            raise HTTPException(status_code=422, detail="The resulting assignment interval is invalid.")

    try:
        resulting_from = (
            payload_assigned_from
            if "assigned_from" in payload
            else parse_rfc3339(existing["assigned_from"])
        )

        if "assigned_to" in payload:
            resulting_to = (
                payload_assigned_to
                if payload["assigned_to"] is not None
                else None
            )
        else:
            resulting_to = (
                parse_rfc3339(existing["assigned_to"])
                if existing["assigned_to"] is not None
                else None
            )

        if resulting_to is not None and resulting_to <= resulting_from:
            raise ValueError()

    except (ValueError, TypeError, OverflowError):
        raise HTTPException(status_code=422, detail="The resulting assignment interval is invalid.")

    validated_payload = payload.copy()

    if "assigned_from" in validated_payload:
        validated_payload["assigned_from"] = payload_assigned_from

    if "assigned_to" in validated_payload:
        validated_payload["assigned_to"] = (
            payload_assigned_to
            if payload["assigned_to"] is not None
            else None
        )

    try:
        result = vehicle_assignment_dao.update_vehicle_assignment(
            assignment_id,
            validated_payload
        )

        if result is None:
            raise HTTPException(status_code=404, detail="assignment_id or a referenced foreign key does not exist.")

        return result

    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(status_code=404, detail="assignment_id or a referenced foreign key does not exist.")


def delete_vehicle_assignment(assignment_id):
    deleted = vehicle_assignment_dao.delete_vehicle_assignment(
        assignment_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Vehicle assignment does not exist."
        )

    return {
        "message": "Vehicle assignment deleted successfully.",
        "assignment_id": assignment_id
    }
