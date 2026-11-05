from fastapi import HTTPException
from psycopg.errors import ForeignKeyViolation

from backend.dao.location_ping import LocationPingDAO
from backend.validation import body_id, bounding_box, nonnegative, pagination, point, record_id, serialize, time_range, timestamp


class LocationPingHandler:
    fields = {"vehicle_id", "ts", "geom", "speed_kph", "heading_deg"}

    def __init__(self, connection):
        self.dao = LocationPingDAO(connection)

    def require_vehicle(self, vehicle_id):
        if not self.dao.vehicle_exists(vehicle_id):
            raise HTTPException(404, "vehicle_id does not exist.")

    def get(self, ping_id):
        ping_id = record_id(ping_id, "ping_id")
        row = self.dao.get_by_id(ping_id)
        if row is None:
            raise HTTPException(404, "ping_id does not exist.")
        return serialize(row)

    def validate(self, payload, update=False):
        if not payload or set(payload) - self.fields:
            raise HTTPException(400, "Supply at least one supported location ping field.")
        if not update and not {"vehicle_id", "ts", "geom"}.issubset(payload):
            raise HTTPException(400, "vehicle_id, ts and geom are required.")
        values = dict(payload)
        if "vehicle_id" in values:
            values["vehicle_id"] = body_id(values["vehicle_id"], "vehicle_id")
            self.require_vehicle(values["vehicle_id"])
        if "ts" in values:
            values["ts"] = timestamp(values["ts"], "ts")
        if "geom" in values:
            values["geom"] = point(values["geom"], "geom")
        for name in ("speed_kph", "heading_deg"):
            if name in values:
                values[name] = nonnegative(values[name], name)
        if values.get("heading_deg") is not None and values["heading_deg"] >= 360:
            raise HTTPException(400, "heading_deg must be at least 0 and less than 360.")
        return values

    def create(self, payload):
        values = self.validate(payload)
        try:
            return serialize(self.dao.create(values))
        except ForeignKeyViolation:
            raise HTTPException(404, "vehicle_id does not exist.") from None

    def update(self, ping_id, payload):
        ping_id = record_id(ping_id, "ping_id")
        if not payload or set(payload) - self.fields:
            raise HTTPException(400, "Supply at least one supported location ping field.")
        if self.dao.get_by_id(ping_id, lock=True) is None:
            raise HTTPException(404, "ping_id does not exist.")
        values = self.validate(payload, update=True)
        try:
            return serialize(self.dao.update(ping_id, values))
        except ForeignKeyViolation:
            raise HTTPException(404, "vehicle_id does not exist.") from None

    def delete(self, ping_id):
        ping_id = record_id(ping_id, "ping_id")
        if not self.dao.delete(ping_id):
            raise HTTPException(404, "ping_id does not exist.")
        return {"message": "Location ping deleted successfully.", "ping_id": ping_id}

    def list(self, query, vehicle_id=None):
        limit, offset = pagination(query, 100)
        start, end = time_range(query)
        bbox = bounding_box(query.get("bbox"))
        for_vehicle = vehicle_id is not None
        if for_vehicle:
            vehicle_id = record_id(vehicle_id, "vehicle_id")
            self.require_vehicle(vehicle_id)
        elif "vehicle_id" in query:
            vehicle_id = record_id(query["vehicle_id"], "vehicle_id", 400)
        rows, count = self.dao.list_pings(limit, offset, vehicle_id, start, end, bbox, for_vehicle)
        result = {"items": [serialize(row) for row in rows], "limit": limit, "offset": offset, "count": count}
        if for_vehicle:
            result = {"vehicle_id": vehicle_id, **result}
        return result
