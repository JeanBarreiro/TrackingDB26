from psycopg import sql

from backend.dao.resource import ResourceDAO


class TripDAO(ResourceDAO):
    table_name = "trip"
    id_column = "trip_id"
    time_column = "start_ts"
    geometry_columns = {"start_geom", "end_geom"}
    columns = ("trip_id", "vehicle_id", "start_ts", "end_ts", "start_geom", "end_geom", "distance_km")

    def list_trips(self, limit, offset, vehicle_id=None, start=None, end=None, for_vehicle=False):
        conditions, parameters = [], []
        if vehicle_id is not None:
            conditions.append(sql.SQL("vehicle_id = %s"))
            parameters.append(vehicle_id)
        # Include trips that overlap the requested interval, including its edges.
        if start is not None:
            conditions.append(sql.SQL("end_ts >= %s"))
            parameters.append(start)
        if end is not None:
            conditions.append(sql.SQL("start_ts <= %s"))
            parameters.append(end)
        columns = ["trip_id", "start_ts", "end_ts", "distance_km"]
        if not for_vehicle:
            columns.insert(1, "vehicle_id")
        return self.list_records(conditions, parameters, limit, offset, columns)
