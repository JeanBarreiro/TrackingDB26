import psycopg

from fastapi import HTTPException

from controllers.validation import validate_payload, validate_geom
from models import road_dao
from models.db import check_postgis_geometry


def _validate_geom_if_present(payload):
    if "geom" in payload:
        geom_json = validate_geom(
            payload["geom"],
            "LineString"
        )

        try:
            check_postgis_geometry(geom_json, "LineString")
        except (psycopg.Error, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid LineString geometry"
            ) from exc


def list_roads(
    limit,
    offset,
    name=None,
    bbox=None,
    min_speed=None,
    max_speed=None
):
    return road_dao.list_roads(
        limit,
        offset,
        name,
        bbox,
        min_speed,
        max_speed
    )


def get_road(road_id):
    result = road_dao.get_road_by_id(road_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Road segment not found"
        )

    return result


def create_road(payload):
    validate_payload(payload, "road")
    _validate_geom_if_present(payload)

    return road_dao.create_road(payload)


def update_road(road_id, payload):
    validate_payload(
        payload,
        "road",
        update=True
    )
    _validate_geom_if_present(payload)

    result = road_dao.update_road(
        road_id,
        payload
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Road segment not found"
        )

    return result


def delete_road(road_id):
    if not road_dao.delete_road(road_id):
        raise HTTPException(
            status_code=404,
            detail="Road segment not found"
        )

    return {
        "message": "Road segment deleted successfully.",
        "road_id": road_id
    }


def road_geojson(
    limit,
    offset,
    name=None,
    min_speed=None,
    max_speed=None
):
    return road_dao.roads_geojson(
        limit,
        offset,
        name,
        min_speed,
        max_speed
    )
