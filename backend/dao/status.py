from psycopg import sql

from backend.database import database_schema


class StatusDAO:
    def __init__(self, connection):
        self.connection = connection

    def database(self):
        return self.connection.execute(
            "SELECT current_database() AS database, current_user AS user"
        ).fetchone()

    def vehicles(self):
        return self.connection.execute(sql.SQL(
            "SELECT vehicle_id, plate_number, make, model, year FROM {} ORDER BY vehicle_id"
        ).format(sql.Identifier(database_schema(), "vehicle"))).fetchall()
