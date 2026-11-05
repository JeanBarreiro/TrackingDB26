from fastapi import APIRouter, Body, Depends, Request

from backend.database import get_db
from backend.handler.trip import TripHandler

router = APIRouter(prefix="/api/v1", tags=["Trips"])


@router.post("/trips", status_code=201)
def create_trip(payload: dict = Body(...), connection=Depends(get_db, scope="function")):
    return TripHandler(connection).create(payload)


@router.get("/trips")
def list_trips(request: Request, connection=Depends(get_db, scope="function")):
    return TripHandler(connection).list(request.query_params)


@router.get("/vehicles/{vehicle_id}/trips")
def vehicle_trips(vehicle_id: str, request: Request, connection=Depends(get_db, scope="function")):
    return TripHandler(connection).list(request.query_params, vehicle_id)


@router.get("/trips/{trip_id}")
def get_trip(trip_id: str, connection=Depends(get_db, scope="function")):
    return TripHandler(connection).get(trip_id)


@router.put("/trips/{trip_id}")
def update_trip(trip_id: str, payload: dict = Body(...), connection=Depends(get_db, scope="function")):
    return TripHandler(connection).update(trip_id, payload)


@router.delete("/trips/{trip_id}")
def delete_trip(trip_id: str, connection=Depends(get_db, scope="function")):
    return TripHandler(connection).delete(trip_id)
