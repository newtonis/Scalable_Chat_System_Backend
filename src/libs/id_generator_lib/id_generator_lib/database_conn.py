import psycopg2
import psycopg2.extras

import os
from dotenv import load_dotenv


### Database connection singleton

class DatabaseConn:
    ### Exposed variables:
        # - conn
        # - cursor

    def __init__(self):

        load_dotenv()
        POSTGRES_DB = os.environ["POSTGRES_DB"]
        POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
        POSTGRES_USER = os.environ["POSTGRES_USER"]

        conn_string = f"host='localhost' dbname='{POSTGRES_DB}' user='{POSTGRES_USER}' password='{POSTGRES_PASSWORD}'"
        self.conn = psycopg2.connect(conn_string)
        self.conn.autocommit = False

        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

database_conn = DatabaseConn()
