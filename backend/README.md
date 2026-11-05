# Trips and Location Pings — Phase II

## Run in PyCharm

1. Open the repository and select `.venv` as the Python interpreter.
2. In the terminal, run `python -m pip install -r requirements.txt`.
3. Under **Run → Edit Configurations → + → Python**, select **Module name** and enter `uvicorn`. Set parameters to `api:app --reload` and the working directory to the repository root.
4. Add these environment variables in that run configuration:
   - `DATABASE_URL`: the Render **External Database URL**, with `?sslmode=require` appended. Use the Internal URL only when running inside Render.
   - `DB_SCHEMA=projectfall2026`.
5. Run the configuration. Open `http://127.0.0.1:8000/db-check` to check the connection and `http://127.0.0.1:8000/docs` to try the endpoints.

Connection settings are in `backend/database.py` and are shared with the Road and Parking code through `models/db.py`. Instead of `DATABASE_URL`, you can set `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`. Keep credentials in the run configuration or Render environment settings.

For terminal commands, set the same variables in the terminal; PyCharm run configuration variables apply only to that configuration.

On Render, the existing `uvicorn api:app --host 0.0.0.0 --port $PORT` start command still works. Both entry points use the same application, including Road, Parking, Trip, and Location Ping routes. Install dependencies from `requirements.txt` with Python 3.10 or newer.

## Database setup

Phase II requires the schema `projectfall2026`. After the Phase I tables and data exist, apply `sql/phase2_setup.sql` once using DataGrip's SQL console or:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/phase2_setup.sql
```

The script moves the 11 project tables from `public`, preserves their records and foreign keys, and enables automatic IDs for roads, parking areas, trips, and pings. New roads and parking areas also receive a creation timestamp. It can be run again without resetting IDs. Coordinate the move with teammates whose code uses `public` explicitly. The API does not run this script automatically.

The API defaults to `public` to support the existing Phase I database; creating records still requires ID defaults. After applying the script, set `DB_SCHEMA=projectfall2026` for every API route and the Phase II submission. Do not rerun the Phase I loader on populated tables.

## Endpoints

All paths start with `/api/v1`.

| Method | Path | Action |
| --- | --- | --- |
| POST / GET | `/trips` | Create / list trips |
| GET / PUT / DELETE | `/trips/{trip_id}` | Read / update / delete a trip |
| GET | `/vehicles/{vehicle_id}/trips` | List one vehicle's trips |
| POST / GET | `/location-pings` | Create / list pings |
| GET / PUT / DELETE | `/location-pings/{ping_id}` | Read / update / delete a ping |
| GET | `/vehicles/{vehicle_id}/pings` | List one vehicle's pings |

Trip creation requires `vehicle_id`, `start_ts`, and `end_ts`. Ping creation requires `vehicle_id`, `ts`, and `geom`. The vehicle must already exist. PUT accepts one or more supported fields.

- Timestamps need a timezone, such as `2026-11-02T10:00:00-04:00`; responses use UTC (`Z`).
- Geometry uses GeoJSON: `{"type":"Point","coordinates":[-67.15,18.20]}` (longitude, latitude).
- Lists accept `limit`, `offset`, `from_ts`, and `to_ts`; collection paths also accept `vehicle_id`. Trips match overlapping time intervals, including the boundaries.
- Ping lists also accept `bbox=minLon,minLat,maxLon,maxLat`, including points on its boundary.
- Default limits are 50 trips and 100 pings. `count` is the total matching records before pagination.

## Local tests

With Docker Desktop running, use the PyCharm terminal:

```bash
python -m pip install -r requirements-dev.txt
docker compose -f compose.test.yml up -d --wait
```

Run pytest with `TEST_DATABASE_URL=postgresql://tracking_test:local_test_password@127.0.0.1:8914/tracking_phase2_test` in a PyCharm pytest configuration, or on macOS/Linux:

```bash
TEST_DATABASE_URL='postgresql://tracking_test:local_test_password@127.0.0.1:8914/tracking_phase2_test' python -m pytest -q
```

Tests reset only this dedicated local database, load all 11 official Parquet files, apply the setup script, and exercise the API. They also verify that the original records remain unchanged. Stop the test database with `docker compose -f compose.test.yml down`.
