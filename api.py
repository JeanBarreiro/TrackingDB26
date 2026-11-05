import psycopg
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import (
    request_validation_exception_handler
)
from fastapi.responses import JSONResponse

from routes.parking_routes import router as parking_router
from routes.road_routes import router as road_router
from backend.dao.status import StatusDAO
from backend.database import get_db
from backend.routes.trip import router as trip_router
from backend.routes.location_ping import router as location_ping_router

app = FastAPI(title="TrackingDB26 API")


app.include_router(parking_router)
app.include_router(road_router)
app.include_router(trip_router)
app.include_router(location_ping_router)


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
def check_database(connection=Depends(get_db, scope="function")):
    return {"status": "connected", **StatusDAO(connection).database()}


@app.get("/vehicles")
def get_vehicles(connection=Depends(get_db, scope="function")):
    return {"vehicles": StatusDAO(connection).vehicles()}


@app.exception_handler(RequestValidationError)
async def phase_ii_body_validation_handler(
    request: Request,
    exc: RequestValidationError
):
    path = request.url.path

    tracking_request = (
        path.startswith("/api/v1/trips")
        or path.startswith("/api/v1/location-pings")
    )
    if tracking_request or (
        request.method in {"POST", "PUT"}
        and (
            path.startswith("/api/v1/road-segments")
            or path.startswith("/api/v1/parking-areas")
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


@app.exception_handler(psycopg.Error)
async def database_error(_request, exc):
    unavailable = isinstance(exc, psycopg.OperationalError)
    return JSONResponse(
        status_code=503 if unavailable else 500,
        content={"detail": "Database connection unavailable." if unavailable else
                 "Database operation failed. Check the connection and schema setup."}
    )
