-- Run explicitly after reviewing the schema change. The API never runs this script.
-- Preserve all Phase I records and foreign keys while moving the project tables.
BEGIN;

CREATE SCHEMA IF NOT EXISTS projectfall2026;

DO $$
DECLARE
    resource text;
BEGIN
    FOREACH resource IN ARRAY ARRAY[
        'road_segment', 'parking_area', 'vehicle_status', 'fuel_type',
        'vehicle_kind', 'vehicle_type', 'driver', 'vehicle',
        'trip', 'location_ping', 'vehicle_assignment'
    ] LOOP
        IF to_regclass(format('projectfall2026.%I', resource)) IS NOT NULL THEN
            IF to_regclass(format('public.%I', resource)) IS NOT NULL THEN
                RAISE EXCEPTION 'Both schemas contain %. Resolve the duplicate before continuing.', resource;
            END IF;
        ELSIF to_regclass(format('public.%I', resource)) IS NOT NULL THEN
            EXECUTE format('ALTER TABLE public.%I SET SCHEMA projectfall2026', resource);
        ELSE
            RAISE EXCEPTION 'Missing Phase I table: %', resource;
        END IF;
    END LOOP;
END $$;

CREATE SEQUENCE IF NOT EXISTS projectfall2026.road_segment_road_id_seq AS bigint;
ALTER SEQUENCE projectfall2026.road_segment_road_id_seq OWNED BY projectfall2026.road_segment.road_id;
ALTER TABLE projectfall2026.road_segment ALTER COLUMN road_id
    SET DEFAULT nextval('projectfall2026.road_segment_road_id_seq');
SELECT setval('projectfall2026.road_segment_road_id_seq', GREATEST(
    COALESCE((SELECT max(road_id) FROM projectfall2026.road_segment), 0) + 1,
    (SELECT last_value + CASE WHEN is_called THEN 1 ELSE 0 END
     FROM projectfall2026.road_segment_road_id_seq)
), false);
ALTER TABLE projectfall2026.road_segment ALTER COLUMN created_at
    SET DEFAULT timezone('UTC', now());

CREATE SEQUENCE IF NOT EXISTS projectfall2026.parking_area_parking_area_id_seq AS bigint;
ALTER SEQUENCE projectfall2026.parking_area_parking_area_id_seq OWNED BY projectfall2026.parking_area.parking_area_id;
ALTER TABLE projectfall2026.parking_area ALTER COLUMN parking_area_id
    SET DEFAULT nextval('projectfall2026.parking_area_parking_area_id_seq');
SELECT setval('projectfall2026.parking_area_parking_area_id_seq', GREATEST(
    COALESCE((SELECT max(parking_area_id) FROM projectfall2026.parking_area), 0) + 1,
    (SELECT last_value + CASE WHEN is_called THEN 1 ELSE 0 END
     FROM projectfall2026.parking_area_parking_area_id_seq)
), false);
ALTER TABLE projectfall2026.parking_area ALTER COLUMN created_at
    SET DEFAULT timezone('UTC', now());

CREATE SEQUENCE IF NOT EXISTS projectfall2026.trip_trip_id_seq AS bigint;
ALTER SEQUENCE projectfall2026.trip_trip_id_seq OWNED BY projectfall2026.trip.trip_id;
ALTER TABLE projectfall2026.trip ALTER COLUMN trip_id
    SET DEFAULT nextval('projectfall2026.trip_trip_id_seq');
SELECT setval('projectfall2026.trip_trip_id_seq', GREATEST(
    COALESCE((SELECT max(trip_id) FROM projectfall2026.trip), 0) + 1,
    (SELECT last_value + CASE WHEN is_called THEN 1 ELSE 0 END
     FROM projectfall2026.trip_trip_id_seq)
), false);

CREATE SEQUENCE IF NOT EXISTS projectfall2026.location_ping_ping_id_seq AS bigint;
ALTER SEQUENCE projectfall2026.location_ping_ping_id_seq OWNED BY projectfall2026.location_ping.ping_id;
ALTER TABLE projectfall2026.location_ping ALTER COLUMN ping_id
    SET DEFAULT nextval('projectfall2026.location_ping_ping_id_seq');
SELECT setval('projectfall2026.location_ping_ping_id_seq', GREATEST(
    COALESCE((SELECT max(ping_id) FROM projectfall2026.location_ping), 0) + 1,
    (SELECT last_value + CASE WHEN is_called THEN 1 ELSE 0 END
     FROM projectfall2026.location_ping_ping_id_seq)
), false);

COMMIT;
