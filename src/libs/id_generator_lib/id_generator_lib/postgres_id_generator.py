# Generate a new id for a specific message group.
# If the message group is new then id will start form 0

import logging

import psycopg2
from pybreaker import CircuitBreaker
from tenacity import retry, stop_after_attempt, wait_exponential

id_gen_circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=60, name="IdGenerator")


class PostgresIdGenerator:
    def __init__(self, database_conn):
        logging.info("Starting postgres id generator instance ...")
        self.conn = database_conn.conn
        self.cursor = database_conn.cursor

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=5), reraise=True)
    def generate_new_id(self, message_group):
        return id_gen_circuit_breaker.call(self._generate_id_impl, message_group)

    def _generate_id_impl(self, message_group):
        # TODO: Input sanitize, only allow certain characters
        # File lock to block transactions reading the same row
        command = f"""
            SELECT
                counter
            FROM message_groups
            WHERE
                message_group_name = '{message_group}'
            FOR UPDATE
        """

        # If the row does not exist insert a new row, else update the row with the new count

        try:
            self.cursor.execute(command)
        except psycopg2.errors.LockNotAvailable:
            logging.info("Transaction in confict, cancelled")
            self.conn.rollback()
            raise

        fila = self.cursor.fetchone()

        if fila[0] is None:
            # Create the register if it does not exist (On conflict means the register was already created)
            command = f"""
                INSERT INTO message_groups(
                    message_group_name
                    ,counter
                    ,created_at
                    ,updated_at
                ) VALUES (
                    '{message_group}'
                    ,{0}
                    ,(now() AT TIME ZONE 'UTC')
                    ,(now() AT TIME ZONE 'UTC')
                ) ON CONFLICT (message_group_name) DO NOTHING
            """

            try:
                self.cursor.execute(command)
            except psycopg2.errors.LockNotAvailable:
                logging.info("Transaction in confict, cancelled")
                self.conn.rollback()
                raise

        command = f"""
            UPDATE
                message_groups
            SET
                counter={fila[0] + 1},
                updated_at=(now() AT TIME ZONE 'UTC')
            WHERE
                message_group_name = '{message_group}'
        """
        answer = fila[0] + 1
        logging.info(command)
        try:
            self.cursor.execute(command)
            self.conn.commit()
            logging.info("Transaccion completada")
        except psycopg2.DatabaseError:
            logging.info("Transaccion en conflicto, cancelada")
            self.conn.rollback()  # Declare for psycopg2 transaction failed
            raise

        return {"status": "id_generated", "result": answer}
