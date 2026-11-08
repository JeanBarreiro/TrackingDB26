from fastapi import HTTPException
from psycopg.errors import ForeignKeyViolation

from controllers.validation import (
    parse_bbox, parse_id, parse_pagination, parse_time_range, parse_timestamp,
    validate_geom, validate_number
)
from models import location_ping_dao
from models.db import connection, normalize_record


class LocationPingController:
    def validate_ping(self, payload, update=False):
        fields = {"vehicle_id", "ts", "geom", "speed_kph", "heading_deg"}
        if not isinstance(payload, dict) or not payload or not set(payload).issubset(fields):
            raise HTTPException(400, "Supply at least one supported location ping field")
        if not update and not {"vehicle_id", "ts", "geom"}.issubset(payload):
            raise HTTPException(400, "vehicle_id, ts and geom are required")
        values = dict(payload)
        if "vehicle_id" in values:
            if type(values["vehicle_id"]) is not int or not 0 < values["vehicle_id"] <= 2**63 - 1:
                raise HTTPException(400, "vehicle_id must be a positive integer")
        if "ts" in values:
            values["ts"] = parse_timestamp(values["ts"], "ts")
        if "geom" in values:
            values["geom"] = validate_geom(values["geom"], "Point")
        for field in ("speed_kph", "heading_deg"):
            if values.get(field) is not None:
                validate_number(values[field], field)
        if values.get("heading_deg") is not None and values["heading_deg"] >= 360:
            raise HTTPException(400, "heading_deg must be at least 0 and less than 360")
        return values

    def create_ping(self, payload):
        values = self.validate_ping(payload)
        try:
            with connection() as conn:
                return normalize_record(location_ping_dao.create_ping(conn, values))
        except ForeignKeyViolation:
            raise HTTPException(404, "vehicle_id does not exist") from None

    def get_ping(self, ping_id):
        ping_id = parse_id(ping_id, "ping_id", 404)
        with connection() as conn:
            result = location_ping_dao.get_by_id(conn, ping_id)
        if result is None:
            raise HTTPException(404, "ping_id does not exist")
        return normalize_record(result)

    def get_pings(self, limit, offset, vehicle_id=None, from_ts=None, to_ts=None, bbox=None, for_vehicle=False):
        limit, offset = parse_pagination(limit, offset)
        start, end = parse_time_range(from_ts, to_ts)
        bounds = parse_bbox(bbox)
        if vehicle_id is not None:
            vehicle_id = parse_id(vehicle_id, "vehicle_id", 404 if for_vehicle else 400)
        with connection() as conn:
            if for_vehicle and not location_ping_dao.vehicle_exists(conn, vehicle_id):
                raise HTTPException(404, "vehicle_id does not exist")
            rows, count = location_ping_dao.get_pings(conn, limit, offset, vehicle_id, start, end, bounds, for_vehicle)
        result = {"items": [normalize_record(row) for row in rows], "limit": limit, "offset": offset, "count": count}
        return {"vehicle_id": vehicle_id, **result} if for_vehicle else result

    def update_ping(self, ping_id, payload):
        ping_id = parse_id(ping_id, "ping_id", 404)
        values = self.validate_ping(payload, update=True)
        try:
            with connection() as conn:
                if location_ping_dao.get_by_id(conn, ping_id, lock=True) is None:
                    raise HTTPException(404, "ping_id does not exist")
                return normalize_record(location_ping_dao.update_ping(conn, ping_id, values))
        except ForeignKeyViolation:
            raise HTTPException(404, "vehicle_id does not exist") from None

    def delete_ping(self, ping_id):
        ping_id = parse_id(ping_id, "ping_id", 404)
        with connection() as conn:
            deleted = location_ping_dao.delete_ping(conn, ping_id)
        if not deleted:
            raise HTTPException(404, "ping_id does not exist")
        return {"message": "Location ping deleted successfully.", "ping_id": ping_id}
