from psycopg import sql

from backend.dao.resource import ResourceDAO


class LocationPingDAO(ResourceDAO):
    table_name = "location_ping"
    id_column = "ping_id"
    time_column = "ts"
    geometry_columns = {"geom"}
    columns = ("ping_id", "vehicle_id", "ts", "geom", "speed_kph", "heading_deg")

    def list_pings(self, limit, offset, vehicle_id=None, start=None, end=None, bbox=None, for_vehicle=False):
        conditions, parameters = [], []
        if vehicle_id is not None:
            conditions.append(sql.SQL("vehicle_id = %s"))
            parameters.append(vehicle_id)
        if start is not None:
            conditions.append(sql.SQL("ts >= %s"))
            parameters.append(start)
        if end is not None:
            conditions.append(sql.SQL("ts <= %s"))
            parameters.append(end)
        if bbox is not None:
            conditions.append(sql.SQL("ST_Intersects(geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326))"))
            parameters.extend(bbox)
        columns = ["ping_id", "ts", "speed_kph", "heading_deg"]
        if for_vehicle:
            columns.insert(2, "geom")
        else:
            columns.insert(1, "vehicle_id")
        return self.list_records(conditions, parameters, limit, offset, columns)
