def validate_dataframe(df, expected_columns, primary_key, table_name):
    # 1. Verificar que las columnas sean exactamente las esperadas
    if list(df.columns) != expected_columns:
        raise ValueError(
            f"{table_name}: las columnas no coinciden con el schema esperado."
        )

    # 2. La Primary Key nunca puede ser NULL
    if df[primary_key].isnull().any():
        raise ValueError(
            f"{table_name}: {primary_key} contiene valores NULL."
        )

    # 3. La Primary Key no puede tener valores duplicados
    if df[primary_key].duplicated().any():
        raise ValueError(
            f"{table_name}: {primary_key} contiene valores duplicados."
        )

    return df


SCHEMAS = {
    "driver": {
        "columns": [
            "driver_id",
            "first_name",
            "last_name",
            "license_number",
            "hired_at"
        ],
        "primary_key": "driver_id"
    },

    "fuel_type": {
        "columns": [
            "fuel_type_id",
            "name"
        ],
        "primary_key": "fuel_type_id"
    },

    "location_ping": {
        "columns": [
            "ping_id",
            "vehicle_id",
            "ts",
            "geom",
            "speed_kph",
            "heading_deg"
        ],
        "primary_key": "ping_id"
    },

    "parking_area": {
        "columns": [
            "parking_area_id",
            "name",
            "capacity",
            "geom",
            "created_at"
        ],
        "primary_key": "parking_area_id"
    },

    "road_segment": {
        "columns": [
            "road_id",
            "name",
            "speed_limit_kph",
            "geom",
            "created_at",
            "is_oneway",
            "direction"
        ],
        "primary_key": "road_id"
    },

    "trip": {
        "columns": [
            "trip_id",
            "vehicle_id",
            "start_ts",
            "end_ts",
            "start_geom",
            "end_geom",
            "distance_km"
        ],
        "primary_key": "trip_id"
    },

    "vehicle": {
        "columns": [
            "vehicle_id",
            "vehicle_type_id",
            "vehicle_status_id",
            "plate_number",
            "make",
            "model",
            "year",
            "created_at"
        ],
        "primary_key": "vehicle_id"
    },

    "vehicle_assignment": {
        "columns": [
            "assignment_id",
            "vehicle_id",
            "driver_id",
            "assigned_from",
            "assigned_to"
        ],
        "primary_key": "assignment_id"
    },

    "vehicle_kind": {
        "columns": [
            "vehicle_kind_id",
            "name"
        ],
        "primary_key": "vehicle_kind_id"
    },

    "vehicle_status": {
        "columns": [
            "vehicle_status_id",
            "name"
        ],
        "primary_key": "vehicle_status_id"
    },

    "vehicle_type": {
        "columns": [
            "vehicle_type_id",
            "vehicle_kind_id",
            "fuel_type_id",
            "emissions_rating",
            "created_at"
        ],
        "primary_key": "vehicle_type_id"
    }
}


def transform(df, table_name):
    if table_name not in SCHEMAS:
        raise ValueError(f"Tabla desconocida: {table_name}")

    schema = SCHEMAS[table_name]

    return validate_dataframe(
        df,
        schema["columns"],
        schema["primary_key"],
        table_name
    )