import os
import psycopg
from fastapi import FastAPI
from psycopg.rows import dict_row

app = FastAPI(title="TrackingDB26 API")


@app.get("/")
def home():
    return {"message": "TrackingDB26 API funcionando"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def check_database():
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user;")
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
                SELECT vehicle_id, plate_number, make, model, year
                FROM public.vehicle
                ORDER BY vehicle_id;
            """)
            vehicles = cur.fetchall()

    return {"vehicles": vehicles}