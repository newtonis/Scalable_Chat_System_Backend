
# Generate a new id for a specific message group.
# If the message group is new then id will start form 0

from .database_conn import database_conn
from .init_database import try_init_database
import psycopg2

try_init_database()

conn = database_conn.conn
cursor = database_conn.cursor


class PostgresIdGenerator:
    def __init__(self):
        pass

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
            cursor.execute(command)
        except psycopg2.errors.LockNotAvailable:
            print("Transaction in confict, cancelled")
            conn.rollback()
            return {
                "status": "failed_txn (select counter)"
            }

        fila = cursor.fetchone()

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
        print(command)
        try:
            cursor.execute(command)
            conn.commit()
            print("Transaccion completada")
        except psycopg2.DatabaseError as e:
            print("Transaccion en conflicto, cancelada")
            conn.rollback() # Declare for psycopg2 transaction failed
            return {
                "status": "failed_txn (insert/update counter)"
            }

        return {   
            "status": "id_generated",
            "result": answer
        }