from database import get_db
from fastapi import APIRouter, Depends, Query
from controllers.vehicle_controller import VehicleController

router = APIRouter()


# GET all vehicles
@router.get("/api/v1/vehicles")
def get_vehicles(
    limit: int = Query(default=20, ge=0),
    offset: int = Query(default=0, ge=0),
    status: str = None,
    plate_number: str = None,
    conn=Depends(get_db),
):

    return VehicleController.get_vehicles(
        conn,
        limit,
        offset,
        status,
        plate_number,
    )


# GET vehicle by ID
@router.get("/api/v1/vehicles/{vehicle_id}")
def get_vehicle_by_id(
    vehicle_id: int,
    conn=Depends(get_db),
):

    return VehicleController.get_vehicle_by_id(
        conn,
        vehicle_id,
    )