from database import get_db
from fastapi import APIRouter, Depends, Query
from controllers.driver_controller import DriverController
router = APIRouter()

@router.get("/api/v1/drivers")
def get_drivers(
    limit: int = Query(default=20, ge=0),
    offset: int = Query(default=0, ge=0),
    name: str = None,
    license_number: str = None,
    conn=Depends(get_db),
):

    return DriverController.get_drivers(
        conn,
        limit,
        offset,
        name,
        license_number,
    )

@router.get("/api/v1/drivers/{driver_id}")
def get_driver(
    driver_id: int,
    conn=Depends(get_db),
):

    return DriverController.get_driver(
        conn,
        driver_id,
    )