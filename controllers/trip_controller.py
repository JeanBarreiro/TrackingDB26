from fastapi import HTTPException
from psycopg.errors import ForeignKeyViolation

from controllers.validation import (
    parse_id, parse_pagination, parse_time_range, parse_timestamp,
    validate_geom, validate_number
)
from models import trip_dao
from models.db import connection, normalize_record


class TripController:
    def validate_trip(self, payload, update=False):
        fields = {"vehicle_id", "start_ts", "end_ts", "start_geom", "end_geom", "distance_km"}
        if not isinstance(payload, dict) or not payload or not set(payload).issubset(fields):
            raise HTTPException(400, "Supply at least one supported trip field")
        if not update and not {"vehicle_id", "start_ts", "end_ts"}.issubset(payload):
            raise HTTPException(400, "vehicle_id, start_ts and end_ts are required")
        status = 422 if update else 400
        values = dict(payload)
        if "vehicle_id" in values:
            if type(values["vehicle_id"]) is not int or not 0 < values["vehicle_id"] <= 2**63 - 1:
                raise HTTPException(status, "vehicle_id must be a positive integer")
        for field in ("start_ts", "end_ts"):
            if field in values:
                values[field] = parse_timestamp(values[field], field, status)
        for field in ("start_geom", "end_geom"):
            if values.get(field) is not None:
                values[field] = validate_geom(values[field], "Point")
        if values.get("distance_km") is not None:
            validate_number(values["distance_km"], "distance_km", status)
        return values

    def create_trip(self, payload):
        values = self.validate_trip(payload)
        if values["end_ts"] <= values["start_ts"]:
            raise HTTPException(400, "end_ts must be later than start_ts")
        try:
            with connection() as conn:
                return normalize_record(trip_dao.create_trip(conn, values))
        except ForeignKeyViolation:
            raise HTTPException(404, "vehicle_id does not exist") from None

    def get_trip(self, trip_id):
        trip_id = parse_id(trip_id, "trip_id", 404)
        with connection() as conn:
            result = trip_dao.get_by_id(conn, trip_id)
        if result is None:
            raise HTTPException(404, "trip_id does not exist")
        return normalize_record(result)

    def get_trips(self, limit, offset, vehicle_id=None, from_ts=None, to_ts=None, for_vehicle=False):
        limit, offset = parse_pagination(limit, offset)
        start, end = parse_time_range(from_ts, to_ts)
        if vehicle_id is not None:
            vehicle_id = parse_id(vehicle_id, "vehicle_id", 404 if for_vehicle else 400)
        with connection() as conn:
            if for_vehicle and not trip_dao.vehicle_exists(conn, vehicle_id):
                raise HTTPException(404, "vehicle_id does not exist")
            rows, count = trip_dao.get_trips(conn, limit, offset, vehicle_id, start, end, for_vehicle)
        result = {"items": [normalize_record(row) for row in rows], "limit": limit, "offset": offset, "count": count}
        return {"vehicle_id": vehicle_id, **result} if for_vehicle else result

    def update_trip(self, trip_id, payload):
        trip_id = parse_id(trip_id, "trip_id", 404)
        values = self.validate_trip(payload, update=True)
        try:
            with connection() as conn:
                previous = trip_dao.get_by_id(conn, trip_id, lock=True)
                if previous is None:
                    raise HTTPException(404, "trip_id does not exist")
                merged = {**previous, **values}
                if merged["end_ts"] <= merged["start_ts"]:
                    raise HTTPException(422, "end_ts must be later than start_ts")
                return normalize_record(trip_dao.update_trip(conn, trip_id, values))
        except ForeignKeyViolation:
            raise HTTPException(404, "vehicle_id does not exist") from None

    def delete_trip(self, trip_id):
        trip_id = parse_id(trip_id, "trip_id", 404)
        with connection() as conn:
            deleted = trip_dao.delete_trip(conn, trip_id)
        if not deleted:
            raise HTTPException(404, "trip_id does not exist")
        return {"message": "Trip deleted successfully.", "trip_id": trip_id}
