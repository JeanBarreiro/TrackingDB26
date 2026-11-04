from fastapi import (
    APIRouter,
    Body,
    HTTPException,
    Query,
    Request
)
from fastapi.responses import JSONResponse

from controllers import road_controller
from controllers.validation import (
    parse_pagination,
    parse_bbox,
    parse_id,
    parse_speed,
    check_speed_bounds
)


router = APIRouter(
    prefix="/api/v1/road-segments",
    tags=["Road Segments"]
)


@router.post("", status_code=201)
def create_road(body: dict = Body(...)):
    return road_controller.create_road(body)


@router.get("")
def list_roads(
    limit: str = Query("20"),
    offset: str = Query("0"),
    name: str | None = None,
    bbox: str | None = None,
    min_speed_kph: str | None = None,
    max_speed_kph: str | None = None
):
    n_limit, n_offset = parse_pagination(limit, offset)
    bounds = parse_bbox(bbox)

    low = parse_speed(
        min_speed_kph,
        "min_speed_kph"
    )

    high = parse_speed(
        max_speed_kph,
        "max_speed_kph"
    )

    check_speed_bounds(low, high)

    return road_controller.list_roads(
        n_limit,
        n_offset,
        name,
        bounds,
        low,
        high
    )


# Static route must come before /{road_id}
@router.get("/geojson")
def read_geojson(
    request: Request,
    limit: int = Query(default=15000, ge=0),
    offset: int = Query(default=0, ge=0),
    name: str | None = None,
    min_speed_kph: float | None = Query(default=None, ge=0),
    max_speed_kph: float | None = Query(default=None, ge=0)
):
    if "bbox" in request.query_params:
        raise HTTPException(
            status_code=400,
            detail="bbox not supported by this endpoint"
        )

    check_speed_bounds(
        min_speed_kph,
        max_speed_kph
    )

    payload = road_controller.road_geojson(
        limit,
        offset,
        name,
        min_speed_kph,
        max_speed_kph
    )

    return JSONResponse(
        content=payload,
        media_type="application/geo+json"
    )


@router.get("/{road_id}")
def get_road(road_id: str):
    return road_controller.get_road(
        parse_id(road_id, "road_id")
    )


@router.put("/{road_id}")
def update_road(
    road_id: str,
    body: dict = Body(...)
):
    return road_controller.update_road(
        parse_id(road_id, "road_id"),
        body
    )


@router.delete("/{road_id}")
def delete_road(road_id: str):
    return road_controller.delete_road(
        parse_id(road_id, "road_id")
    )
