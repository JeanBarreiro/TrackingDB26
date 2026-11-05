from fastapi import HTTPException
from psycopg.errors import ForeignKeyViolation

from backend.dao.trip import TripDAO
from backend.validation import body_id, nonnegative, pagination, point, record_id, serialize, time_range, timestamp


class TripHandler:
    fields = {"vehicle_id", "start_ts", "end_ts", "start_geom", "end_geom", "distance_km"}

    def __init__(self, connection):
        self.dao = TripDAO(connection)

    def require_vehicle(self, vehicle_id):
        if not self.dao.vehicle_exists(vehicle_id):
            raise HTTPException(404, "vehicle_id does not exist.")

    def get(self, trip_id):
        trip_id = record_id(trip_id, "trip_id")
        row = self.dao.get_by_id(trip_id)
        if row is None:
            raise HTTPException(404, "trip_id does not exist.")
        return serialize(row)

    def validate(self, payload, update=False, previous=None):
        if not payload or set(payload) - self.fields:
            raise HTTPException(400, "Supply at least one supported trip field.")
        required = {"vehicle_id", "start_ts", "end_ts"}
        if not update and not required.issubset(payload):
            raise HTTPException(400, "vehicle_id, start_ts and end_ts are required.")
        status = 422 if update else 400
        values = dict(payload)
        for name in ("start_ts", "end_ts"):
            if name in values:
                values[name] = timestamp(values[name], name, status)
        if "vehicle_id" in values:
            values["vehicle_id"] = body_id(values["vehicle_id"], "vehicle_id", status)
            self.require_vehicle(values["vehicle_id"])
        for name in ("start_geom", "end_geom"):
            if name in values:
                # Malformed geometry has the explicit 400 response in the spec.
                values[name] = point(values[name], name, nullable=True)
        if "distance_km" in values:
            values["distance_km"] = nonnegative(values["distance_km"], "distance_km", status)
        merged = {**(previous or {}), **values}
        if merged["end_ts"] <= merged["start_ts"]:
            raise HTTPException(status, "end_ts must be later than start_ts.")
        return values

    def create(self, payload):
        values = self.validate(payload)
        try:
            return serialize(self.dao.create(values))
        except ForeignKeyViolation:
            raise HTTPException(404, "vehicle_id does not exist.") from None

    def update(self, trip_id, payload):
        trip_id = record_id(trip_id, "trip_id")
        if not payload or set(payload) - self.fields:
            raise HTTPException(400, "Supply at least one supported trip field.")
        previous = self.dao.get_by_id(trip_id, lock=True)
        if previous is None:
            raise HTTPException(404, "trip_id does not exist.")
        values = self.validate(payload, update=True, previous=previous)
        try:
            return serialize(self.dao.update(trip_id, values))
        except ForeignKeyViolation:
            raise HTTPException(404, "vehicle_id does not exist.") from None

    def delete(self, trip_id):
        trip_id = record_id(trip_id, "trip_id")
        if not self.dao.delete(trip_id):
            raise HTTPException(404, "trip_id does not exist.")
        return {"message": "Trip deleted successfully.", "trip_id": trip_id}

    def list(self, query, vehicle_id=None):
        limit, offset = pagination(query, 50)
        start, end = time_range(query)
        for_vehicle = vehicle_id is not None
        if for_vehicle:
            vehicle_id = record_id(vehicle_id, "vehicle_id")
            self.require_vehicle(vehicle_id)
        elif "vehicle_id" in query:
            vehicle_id = record_id(query["vehicle_id"], "vehicle_id", 400)
        rows, count = self.dao.list_trips(limit, offset, vehicle_id, start, end, for_vehicle)
        result = {"items": [serialize(row) for row in rows], "limit": limit, "offset": offset, "count": count}
        if for_vehicle:
            result = {"vehicle_id": vehicle_id, **result}
        return result
