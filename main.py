from pathlib import Path

import pandas as pd
import psycopg

from etl.transform import transform
from etl.load import (
    load_road_segment,
    load_parking_area,
    load_vehicle_status,
    load_fuel_type,
    load_vehicle_kind,
    load_vehicle_type,
    load_driver,
    load_vehicle,
    load_trip,
    load_location_ping,
    load_vehicle_assignment
)


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


# Orden importante por las Foreign Keys
LOAD_ORDER = [
    ("road_segment", load_road_segment),
    ("parking_area", load_parking_area),
    ("vehicle_status", load_vehicle_status),
    ("fuel_type", load_fuel_type),
    ("vehicle_kind", load_vehicle_kind),
    ("vehicle_type", load_vehicle_type),
    ("driver", load_driver),
    ("vehicle", load_vehicle),
    ("trip", load_trip),
    ("location_ping", load_location_ping),
    ("vehicle_assignment", load_vehicle_assignment)
]


def main():

    print("Iniciando ETL...\n")

    with psycopg.connect(
        host="localhost",
        port=8902,
        dbname="car_tracking",
        user="caradmin",
        password="carpassword"
    ) as conn:

        for table_name, load_function in LOAD_ORDER:

            # E - Extract
            file_path = DATA_DIR / f"{table_name}.parquet"
            df = pd.read_parquet(file_path)

            print(f"{table_name}:")
            print(f"  Extract: {len(df)} filas leídas.")

            # T - Transform / Validate
            df = transform(df, table_name)

            print("  Transform: validación correcta.")

            # L - Load
            load_function(df, conn)

            print("  Load: completado.\n")

    print("ETL completado correctamente.")


if __name__ == "__main__":
    main()