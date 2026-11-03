import psycopg

from fastapi import HTTPException

from controllers.validation import validate_payload, validate_geom
from models import parking_dao
from models.db import check_postgis_geometry


def _validate_geom_if_present(payload):
    if "geom" in payload:
        geom_json = validate_geom(
            payload["geom"],
            "Polygon"
        )

        try:
            check_postgis_geometry(geom_json, "Polygon")
        except (psycopg.Error, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid Polygon geometry"
            ) from exc


def list_parking_areas(limit, offset, name=None, bbox=None):
    return parking_dao.list_parking_areas(
        limit,
        offset,
        name,
        bbox
    )


def get_parking_area(parking_area_id):
    result = parking_dao.get_parking_area_by_id(
        parking_area_id
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Parking area not found"
        )

    return result


def create_parking_area(payload):
    validate_payload(payload, "parking")
    _validate_geom_if_present(payload)

    return parking_dao.create_parking_area(payload)


def update_parking_area(parking_area_id, payload):
    validate_payload(
        payload,
        "parking",
        update=True
    )
    _validate_geom_if_present(payload)

    result = parking_dao.update_parking_area(
        parking_area_id,
        payload
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Parking area not found"
        )

    return result


def delete_parking_area(parking_area_id):
    if not parking_dao.delete_parking_area(parking_area_id):
        raise HTTPException(
            status_code=404,
            detail="Parking area not found"
        )

    return {
        "message": "Parking area deleted successfully.",
        "parking_area_id": parking_area_id
    }
