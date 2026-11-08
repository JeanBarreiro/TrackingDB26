from fastapi import APIRouter, Body, Query

from controllers.location_ping_controller import LocationPingController

router = APIRouter(prefix="/api/v1", tags=["Location Pings"])


@router.post("/location-pings", status_code=201)
def create_ping(body: dict = Body(...)):
    return LocationPingController().create_ping(body)


@router.get("/location-pings")
def get_pings(
    limit: str = Query("100"), offset: str = Query("0"), vehicle_id: str | None = None,
    from_ts: str | None = None, to_ts: str | None = None, bbox: str | None = None
):
    return LocationPingController().get_pings(limit, offset, vehicle_id, from_ts, to_ts, bbox)


@router.get("/vehicles/{vehicle_id}/pings")
def get_vehicle_pings(
    vehicle_id: str, limit: str = Query("100"), offset: str = Query("0"),
    from_ts: str | None = None, to_ts: str | None = None
):
    return LocationPingController().get_pings(limit, offset, vehicle_id, from_ts, to_ts, for_vehicle=True)


@router.get("/location-pings/{ping_id}")
def get_ping(ping_id: str):
    return LocationPingController().get_ping(ping_id)


@router.put("/location-pings/{ping_id}")
def update_ping(ping_id: str, body: dict = Body(...)):
    return LocationPingController().update_ping(ping_id, body)


@router.delete("/location-pings/{ping_id}")
def delete_ping(ping_id: str):
    return LocationPingController().delete_ping(ping_id)
