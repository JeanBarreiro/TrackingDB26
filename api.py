import os

import psycopg
from fastapi import FastAPI
from psycopg.rows import dict_row
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import (
    request_validation_exception_handler
)
from fastapi.responses import JSONResponse

from routes.parking_routes import router as parking_router
from routes.road_routes import router as road_router
from routes.vehicle_routes import router as vehicle_router
from routes.driver_routes import router as driver_router
from routes.location_ping_routes import router as location_ping_router
from routes.trip_routes import router as trip_router

app = FastAPI(title="TrackingDB26 API")


# Register Parking and Road routes
app.include_router(parking_router)
app.include_router(road_router)
app.include_router(vehicle_router)
app.include_router(driver_router)
app.include_router(location_ping_router)
app.include_router(trip_router)

@app.get("/")
def home():
    return {
        "message": "TrackingDB26 API funcionando"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.get("/db-check")
def check_database():
    with psycopg.connect(
        os.environ["DATABASE_URL"]
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT current_database(), current_user;"
            )
            database, user = cur.fetchone()

    return {
        "status": "connected",
        "database": database,
        "user": user
    }


@app.get("/vehicles")
def get_vehicles():
    with psycopg.connect(
        os.environ["DATABASE_URL"],
        row_factory=dict_row
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    vehicle_id,
                    plate_number,
                    make,
                    model,
                    year
                FROM public.vehicle
                ORDER BY vehicle_id;
            """)

            vehicles = cur.fetchall()

    return {
        "vehicles": vehicles
    }


@app.exception_handler(RequestValidationError)
async def phase_ii_body_validation_handler(
    request: Request,
    exc: RequestValidationError
):
    path = request.url.path

    if (
        request.method in {"POST", "PUT"}
        and (
            path.startswith("/api/v1/road-segments")
            or path.startswith("/api/v1/parking-areas")
            or path.startswith("/api/v1/vehicles")
            or path.startswith("/api/v1/drivers")
            or path.startswith("/api/v1/location-pings")
            or path.startswith("/api/v1/trips")
        )
    ):
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Malformed JSON or invalid request body"
            }
        )

    return await request_validation_exception_handler(
        request,
        exc
    )
