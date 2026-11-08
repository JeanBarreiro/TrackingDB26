from fastapi import APIRouter, Body, Query

from controllers.trip_controller import TripController

router = APIRouter(prefix="/api/v1", tags=["Trips"])


@router.post("/trips", status_code=201)
def create_trip(body: dict = Body(...)):
    return TripController().create_trip(body)


@router.get("/trips")
def get_trips(
    limit: str = Query("50"), offset: str = Query("0"),
    vehicle_id: str | None = None, from_ts: str | None = None, to_ts: str | None = None
):
    return TripController().get_trips(limit, offset, vehicle_id, from_ts, to_ts)


@router.get("/vehicles/{vehicle_id}/trips")
def get_vehicle_trips(
    vehicle_id: str, limit: str = Query("50"), offset: str = Query("0"),
    from_ts: str | None = None, to_ts: str | None = None
):
    return TripController().get_trips(limit, offset, vehicle_id, from_ts, to_ts, for_vehicle=True)


@router.get("/trips/{trip_id}")
def get_trip(trip_id: str):
    return TripController().get_trip(trip_id)


@router.put("/trips/{trip_id}")
def update_trip(trip_id: str, body: dict = Body(...)):
    return TripController().update_trip(trip_id, body)


@router.delete("/trips/{trip_id}")
def delete_trip(trip_id: str):
    return TripController().delete_trip(trip_id)
