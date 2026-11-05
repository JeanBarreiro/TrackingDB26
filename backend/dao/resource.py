"""Shared SQL operations for the two tracking resources."""
import json

from psycopg import sql

from backend.database import database_schema


class ResourceDAO:
    def __init__(self, connection):
        self.connection = connection
        self.schema = database_schema()
        self.table = sql.Identifier(self.schema, self.table_name)

    def projection(self, columns=None):
        return sql.SQL(", ").join(
            sql.SQL("ST_AsGeoJSON({}, 15)::json AS {}").format(
                sql.Identifier(column), sql.Identifier(column))
            if column in self.geometry_columns else sql.Identifier(column)
            for column in (columns or self.columns)
        )

    def vehicle_exists(self, vehicle_id):
        return self.connection.execute(
            sql.SQL("SELECT 1 FROM {} WHERE vehicle_id = %s").format(
                sql.Identifier(self.schema, "vehicle")), (vehicle_id,)
        ).fetchone() is not None

    def get_by_id(self, record_id, lock=False):
        return self.connection.execute(
            sql.SQL("SELECT {} FROM {} WHERE {} = %s{}").format(
                self.projection(), self.table, sql.Identifier(self.id_column),
                sql.SQL(" FOR UPDATE" if lock else "")), (record_id,)
        ).fetchone()

    def list_records(self, conditions, parameters, limit, offset, columns):
        where = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conditions) if conditions else sql.SQL("")
        count = self.connection.execute(
            sql.SQL("SELECT count(*) AS count FROM {}{}").format(self.table, where), parameters
        ).fetchone()["count"]
        rows = self.connection.execute(
            sql.SQL("SELECT {} FROM {}{} ORDER BY {}, {} LIMIT %s OFFSET %s").format(
                self.projection(columns), self.table, where,
                sql.Identifier(self.time_column), sql.Identifier(self.id_column)),
            [*parameters, limit, offset],
        ).fetchall()
        return rows, count

    def value_expression(self, column):
        return (sql.SQL("ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)")
                if column in self.geometry_columns else sql.Placeholder())

    def parameters(self, values):
        return [json.dumps(value) if column in self.geometry_columns and value is not None else value
                for column, value in values.items()]

    def create(self, values):
        return self.connection.execute(
            sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING {}").format(
                self.table, sql.SQL(", ").join(map(sql.Identifier, values)),
                sql.SQL(", ").join(self.value_expression(column) for column in values),
                self.projection()), self.parameters(values),
        ).fetchone()

    def update(self, record_id, values):
        assignments = sql.SQL(", ").join(
            sql.SQL("{} = {}").format(sql.Identifier(column), self.value_expression(column))
            for column in values
        )
        return self.connection.execute(
            sql.SQL("UPDATE {} SET {} WHERE {} = %s RETURNING {}").format(
                self.table, assignments, sql.Identifier(self.id_column), self.projection()),
            [*self.parameters(values), record_id],
        ).fetchone()

    def delete(self, record_id):
        return self.connection.execute(
            sql.SQL("DELETE FROM {} WHERE {} = %s RETURNING {}").format(
                self.table, sql.Identifier(self.id_column), sql.Identifier(self.id_column)),
            (record_id,),
        ).fetchone() is not None
