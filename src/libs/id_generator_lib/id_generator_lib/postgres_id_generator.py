
# Generate a new id for a specific message group.
# If the message group is new then id will start form 0

from .database_conn import database_conn
import psycopg2
import logging


class PostgresIdGenerator:
    def __init__(self):
        logging.info("Starting postgres id generator instance ...")
        self.conn = database_conn.conn
        self.cursor = database_conn.cursor

    def generate_new_id(self, message_group):
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
            return {
                "status": "failed_txn (select counter)"
            }

        fila = self.cursor.fetchone()

        if fila is None:
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
                )
            """
            answer = 0
        else:
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
        except psycopg2.DatabaseError as e:
            logging.info("Transaccion en conflicto, cancelada")
            self.conn.rollback() # Declare for psycopg2 transaction failed
            return {
                "status": "failed_txn (insert/update counter)"
            }

        return {   
            "status": "id_generated",
            "result": answer
        }
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.info("Ending postgres ID generator")
        database_conn.close_connection()

