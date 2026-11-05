from fastapi import APIRouter, Body, Depends, Request

from backend.database import get_db
from backend.handler.location_ping import LocationPingHandler

router = APIRouter(prefix="/api/v1", tags=["Location Pings"])


@router.post("/location-pings", status_code=201)
def create_ping(payload: dict = Body(...), connection=Depends(get_db, scope="function")):
    return LocationPingHandler(connection).create(payload)


@router.get("/location-pings")
def list_pings(request: Request, connection=Depends(get_db, scope="function")):
    return LocationPingHandler(connection).list(request.query_params)


@router.get("/vehicles/{vehicle_id}/pings")
def vehicle_pings(vehicle_id: str, request: Request, connection=Depends(get_db, scope="function")):
    return LocationPingHandler(connection).list(request.query_params, vehicle_id)


@router.get("/location-pings/{ping_id}")
def get_ping(ping_id: str, connection=Depends(get_db, scope="function")):
    return LocationPingHandler(connection).get(ping_id)


@router.put("/location-pings/{ping_id}")
def update_ping(ping_id: str, payload: dict = Body(...), connection=Depends(get_db, scope="function")):
    return LocationPingHandler(connection).update(ping_id, payload)


@router.delete("/location-pings/{ping_id}")
def delete_ping(ping_id: str, connection=Depends(get_db, scope="function")):
    return LocationPingHandler(connection).delete(ping_id)
