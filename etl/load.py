import pandas as pd


def db_value(value):
    """
    Convierte valores faltantes de pandas (NaN / NaT)
    a None para que PostgreSQL los guarde como NULL.
    """
    if pd.isna(value):
        return None

    return value


def load_driver(df, conn):
    sql = """
        INSERT INTO driver (
            driver_id,
            first_name,
            last_name,
            license_number,
            hired_at
        )
        VALUES (%s, %s, %s, %s, %s);
    """

    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute(
                sql,
                (
                    int(row["driver_id"]),
                    row["first_name"],
                    row["last_name"],
                    row["license_number"],
                    row["hired_at"]
                )
            )


def load_fuel_type(df, conn):
    sql = """
        INSERT INTO fuel_type (
            fuel_type_id,
            name
        )
        VALUES (%s, %s);
    """

    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute(
                sql,
                (
                    int(row["fuel_type_id"]),
                    row["name"]
                )
            )


def load_vehicle_status(df, conn):
    sql = """
        INSERT INTO vehicle_status (
            vehicle_status_id,
            name
        )
        VALUES (%s, %s);
    """

    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute(
                sql,
                (
                    int(row["vehicle_status_id"]),
                    row["name"]
                )
            )


def load_vehicle_kind(df, conn):
    sql = """
        INSERT INTO vehicle_kind (
            vehicle_kind_id,
            name
        )
        VALUES (%s, %s);
    """

    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute(
                sql,
                (
                    int(row["vehicle_kind_id"]),
                    row["name"]
                )
            )


def load_vehicle_type(df, conn):
    sql = """
        INSERT INTO vehicle_type (
            vehicle_type_id,
            vehicle_kind_id,
            fuel_type_id,
            emissions_rating,
            created_at
        )
        VALUES (%s, %s, %s, %s, %s);
    """

    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute(
                sql,
                (
                    int(row["vehicle_type_id"]),
                    int(row["vehicle_kind_id"]),
                    int(row["fuel_type_id"]),
                    float(row["emissions_rating"]),
                    row["created_at"]
                )
            )


def load_vehicle(df, conn):
    sql = """
        INSERT INTO vehicle (
            vehicle_id,
            vehicle_type_id,
            vehicle_status_id,
            plate_number,
            make,
            model,
            year,
            created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """

    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute(
                sql,
                (
                    int(row["vehicle_id"]),
                    int(row["vehicle_type_id"]),
                    int(row["vehicle_status_id"]),
                    row["plate_number"],
                    row["make"],
                    row["model"],
                    int(row["year"]),
                    row["created_at"]
                )
            )


def load_vehicle_assignment(df, conn):
    sql = """
        INSERT INTO vehicle_assignment (
            assignment_id,
            vehicle_id,
            driver_id,
            assigned_from,
            assigned_to
        )
        VALUES (%s, %s, %s, %s, %s);
    """

    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute(
                sql,
                (
                    int(row["assignment_id"]),
                    int(row["vehicle_id"]),
                    int(row["driver_id"]),
                    row["assigned_from"],
                    db_value(row["assigned_to"])
                )
            )


def load_parking_area(df, conn):
    sql = """
        INSERT INTO parking_area (
            parking_area_id,
            name,
            capacity,
            geom,
            created_at
        )
        VALUES (
            %s,
            %s,
            %s,
            ST_GeomFromEWKB(decode(%s, 'hex')),
            %s
        );
    """

    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute(
                sql,
                (
                    int(row["parking_area_id"]),
                    row["name"],
                    int(row["capacity"]),
                    row["geom"],
                    row["created_at"]
                )
            )


def load_road_segment(df, conn):
    sql = """
        INSERT INTO road_segment (
            road_id,
            name,
            speed_limit_kph,
            geom,
            created_at,
            is_oneway,
            direction
        )
        VALUES (
            %s,
            %s,
            %s,
            ST_GeomFromEWKB(decode(%s, 'hex')),
            %s,
            %s,
            %s
        );
    """

    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute(
                sql,
                (
                    int(row["road_id"]),
                    row["name"],
                    int(row["speed_limit_kph"]),
                    row["geom"],
                    row["created_at"],
                    bool(row["is_oneway"]),
                    row["direction"]
                )
            )


def load_location_ping(df, conn):
    sql = """
        INSERT INTO location_ping (
            ping_id,
            vehicle_id,
            ts,
            geom,
            speed_kph,
            heading_deg
        )
        VALUES (
            %s,
            %s,
            %s,
            ST_GeomFromEWKB(decode(%s, 'hex')),
            %s,
            %s
        );
    """

    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute(
                sql,
                (
                    int(row["ping_id"]),
                    int(row["vehicle_id"]),
                    row["ts"],
                    row["geom"],
                    float(row["speed_kph"]),
                    db_value(row["heading_deg"])
                )
            )


def load_trip(df, conn):
    sql = """
        INSERT INTO trip (
            trip_id,
            vehicle_id,
            start_ts,
            end_ts,
            start_geom,
            end_geom,
            distance_km
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            ST_GeomFromEWKB(decode(%s, 'hex')),
            ST_GeomFromEWKB(decode(%s, 'hex')),
            %s
        );
    """

    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute(
                sql,
                (
                    int(row["trip_id"]),
                    int(row["vehicle_id"]),
                    row["start_ts"],
                    row["end_ts"],
                    row["start_geom"],
                    row["end_geom"],
                    float(row["distance_km"])
                )
            )