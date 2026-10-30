import os
import psycopg

from psycopg.rows import dict_row


def get_db():
    with psycopg.connect(
        host="dpg-dau56j893c1s73cpaaj0-a.virginia-postgres.render.com",
        port=5432,
        dbname="dbclass_hanm",
        user="edgar1",
        password=os.environ["DB_PASSWORD"],
        sslmode="require",
        connect_timeout=10,
        row_factory=dict_row,
    ) as conn:
        yield conn