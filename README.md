# TrackingDB26

## 1. Prerequisites

Before running the project, make sure the following tools are installed:

- **Docker Desktop** — To run PostgreSQL and PostGIS locally.
- **Python** — To execute the ETL pipeline.
- **PyCharm** — To open and run the Python project.
- **Git** — To clone the project repository.

The project uses PostgreSQL 17 with PostGIS 3.5.

The project should have the following structure:

```text
CarTracking/
├── data/
│   ├── driver.parquet
│   ├── fuel_type.parquet
│   ├── location_ping.parquet
│   ├── parking_area.parquet
│   ├── road_segment.parquet
│   ├── trip.parquet
│   ├── vehicle.parquet
│   ├── vehicle_assignment.parquet
│   ├── vehicle_kind.parquet
│   ├── vehicle_status.parquet
│   └── vehicle_type.parquet
├── etl/
│   ├── __init__.py
│   ├── extract.py
│   ├── transform.py
│   └── load.py
├── sql/
│   └── schema.sql
└── main.py
```

Make sure all 11 Parquet files are available in the `data/` directory.

## 2. Configure Python

Open the PyCharm terminal.

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it.

**macOS / Linux:**

```bash
source .venv/bin/activate
```

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

Install the required Python packages:

```bash
python -m pip install pandas pyarrow "psycopg[binary]"
```

These packages are used for:

- `pandas`: Reading and validating data.
- `pyarrow`: Supporting Parquet files.
- `psycopg`: Connecting Python to PostgreSQL.

In PyCharm, select the virtual environment as the project's Python interpreter.

## 3. Start Docker

Open Docker Desktop and wait until the Docker engine is running.

Verify that Docker works:

```bash
docker ps
```

For a first-time setup, the container may not exist yet. This is normal.

## 4. Create the PostgreSQL + PostGIS container

Execute the following command in the PyCharm terminal:

**macOS with Apple Silicon (M1/M2/M3/M4):**

```bash
docker run --platform linux/amd64 \
  --name cartracking-db \
  -e POSTGRES_USER=caradmin \
  -e POSTGRES_PASSWORD=carpassword \
  -e POSTGRES_DB=car_tracking \
  -p 8902:5432 \
  -d postgis/postgis:17-3.5
```

**Windows or Linux with x86-64:**

```bash
docker run \
  --name cartracking-db \
  -e POSTGRES_USER=caradmin \
  -e POSTGRES_PASSWORD=carpassword \
  -e POSTGRES_DB=car_tracking \
  -p 8902:5432 \
  -d postgis/postgis:17-3.5
```

This creates a local database with the following configuration:

| Setting | Value |
|---|---|
| Container | `cartracking-db` |
| Database | `car_tracking` |
| Username | `caradmin` |
| Password | `carpassword` |
| Host | `localhost` |
| Port | `8902` |
| PostgreSQL | 17 |
| PostGIS | 3.5 |

These are local development credentials only.

Verify that the container is running:

```bash
docker ps
```

If it is stopped, run:

```bash
docker start cartracking-db
```

**Important:** The `docker run` command is only needed the first time. After creating the container, use `docker start`.

## 5. Verify PostgreSQL and PostGIS

Connect to the database:

```bash
docker exec -it cartracking-db psql -U caradmin -d car_tracking
```

Check the PostgreSQL version:

```sql
SELECT version();
```

Check PostGIS:

```sql
SELECT PostGIS_Version();
```

If PostGIS is not enabled, execute:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

Exit PostgreSQL:

```text
\q
```

## 6. Create the database tables

Make sure you are in the project's root directory (`CarTracking`).

Run:

```bash
docker exec -i cartracking-db \
  psql -v ON_ERROR_STOP=1 -U caradmin -d car_tracking \
  < sql/schema.sql
```

If successful, the terminal should display `CREATE TABLE` for the 11 project tables.

Verify the tables:

```bash
docker exec -it cartracking-db psql -U caradmin -d car_tracking
```

Inside PostgreSQL:

```text
\dt public.*
```

You should see the 11 project tables and the PostGIS system table `spatial_ref_sys`.

Exit with `\q`.

**Do not run `schema.sql` repeatedly**, since the tables will already exist.

## 7. Run the ETL pipeline

Before running the pipeline, verify that `main.py` uses the same local database configuration:

```python
with psycopg.connect(
    host="localhost",
    port=8902,
    dbname="car_tracking",
    user="caradmin",
    password="carpassword"
) as conn:
```

From the PyCharm terminal, execute:

```bash
python main.py
```

The program automatically performs three stages:

**Extract:** Reads the 11 Parquet files using pandas.

**Transform:** Validates the expected columns, primary keys and duplicate IDs.

**Load:** Inserts records into PostgreSQL in foreign-key dependency order. Geospatial values are converted using PostGIS.

Expected final message:

```text
ETL completado correctamente.
```

The first complete execution should load:

| Table | Expected rows |
|---|---:|
| road_segment | 4,086 |
| parking_area | 224 |
| vehicle_status | 2 |
| fuel_type | 2 |
| vehicle_kind | 5 |
| vehicle_type | 8 |
| driver | 12 |
| vehicle | 30 |
| trip | 300 |
| location_ping | 28,041 |
| vehicle_assignment | 42 |

**Important:** Do not execute `python main.py` a second time against an already populated database. The current ETL uses regular `INSERT` statements, so duplicate primary keys will cause an error.

## 8. Verify the imported data

Connect to PostgreSQL:

```bash
docker exec -it cartracking-db psql -U caradmin -d car_tracking
```

Check the number of vehicles:

```sql
SELECT COUNT(*) FROM vehicle;
```

Expected result: `30`.

Check location pings:

```sql
SELECT COUNT(*) FROM location_ping;
```

Expected result: `28041`.

Verify geospatial data:

```sql
SELECT
    ST_GeometryType(geom),
    ST_SRID(geom),
    COUNT(*)
FROM road_segment
GROUP BY ST_GeometryType(geom), ST_SRID(geom);
```

Expected result:

```text
ST_LineString | 4326 | 4086
```

Verify missing values:

```sql
SELECT COUNT(*)
FROM location_ping
WHERE heading_deg IS NULL;
```

Expected result: `300`.

If these checks pass, the database has been successfully initialized.

## 9. Running the project on subsequent days

After the initial setup, you do not need to recreate the database or reload the Parquet files.

Simply:

1. Open Docker Desktop.
2. Open the CarTracking project in PyCharm.
3. Run `docker start cartracking-db` if the container is stopped.
4. Activate the Python virtual environment when necessary.
5. Use PostgreSQL or DataGrip to query the existing data.

The Docker database preserves its data when the container is stopped and restarted.

## Important notes

- Use Docker for local development and testing.
- Do not use Render production credentials for local testing.
- Do not run `TRUNCATE`, `DROP TABLE`, or experimental inserts on the production database.
- Do not delete the Docker container unless you intend to recreate the database and reload the dataset.
- This guide initializes the Phase I database and ETL. It does not start a FastAPI server or web dashboard.
