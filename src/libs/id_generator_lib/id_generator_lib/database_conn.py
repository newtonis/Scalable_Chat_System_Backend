import logging
import os

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from pybreaker import CircuitBreaker
from tenacity import retry, stop_after_attempt, wait_exponential

### Database connection singleton

db_circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=60, name="PostgreSQL")


class DatabaseConn:
    def __init__(self, postgres_host):
        logging.info("Starting database connection ...")

        load_dotenv()
        POSTGRES_DB = os.environ["POSTGRES_DB"]
        POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
        POSTGRES_USER = os.environ["POSTGRES_USER"]

        conn_string = (
            f"host='{postgres_host}' dbname='{POSTGRES_DB}' user='{POSTGRES_USER}' password='{POSTGRES_PASSWORD}'"
        )

        self.conn = self._connect_with_retry(conn_string)
        self.conn.autocommit = False
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=5), reraise=True)
    def _connect_with_retry(self, conn_string):
        """Establish database connection with retry logic and circuit breaker"""
        return db_circuit_breaker.call(psycopg2.connect, conn_string)

    # Try to init the dabase (if already created has no effect)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=5), reraise=True)
    def try_init_database(self):
        logging.info("Trying to start database ...")

        conn = self.conn
        cursor = self.cursor

        command = """
            SELECT exists (
                SELECT FROM information_schema.tables
                    WHERE  table_schema = 'public' -- O el nombre de tu esquema
                    AND    table_name   = 'message_groups'
            )
        """

        cursor.execute(command)

        fila = cursor.fetchone()
        conn.commit()  # Cerramos la transaccion

        if not fila or not fila[0]:
            logging.info("Generating data model for message groups")
            command = """
                CREATE TABLE message_groups
                    (
                        message_group_name VARCHAR(50),
                        counter INTEGER,
                        created_at TIME,
                        updated_at TIME,

                        CONSTRAINT uq_message_group_name UNIQUE (message_group_name)
                    )
            """

            cursor.execute(command)

            # Commit the transactions
            try:
                conn.commit()
                logging.info("Data model generated")
            except psycopg2.DatabaseError:
                conn.rollback()  # Closing the transaction
                logging.info("Transaction in conflict, cancelled")

        else:
            logging.info("Data model already generated")

    def close_connection(self):
        logging.info("Ending pg database connection ...")
        if self.cursor is not None:
            self.cursor.close()
            logging.info("Closing cursor")

        if self.conn is not None:
            self.conn.close()
            logging.info("Closing postgresql connection")
