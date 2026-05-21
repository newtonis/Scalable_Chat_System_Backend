import psycopg2
import psycopg2.extras
from psycopg2 import DatabaseError

from dotenv import load_dotenv
import os
from .database_conn import database_conn


def try_init_database():
    conn = database_conn.conn
    cursor = database_conn.cursor

    command = """
        SELECT exists (
            SELECT FROM information_schema.tables 
                WHERE  table_schema = 'public' -- O el nombre de tu esquema
                AND    table_name   = 'message_groups'
        )
    """

    cursor.execute(
        command
    )

    fila = cursor.fetchone()
    conn.commit() # Cerramos la transaccion


    if fila[0] != True:
        print("Generating data model for message groups")
        command = """
            CREATE TABLE message_groups 
                (
                    message_group_name VARCHAR(50),
                    counter INTEGER,
                    created_at TIME,
                    updated_at TIME
                )
        """

        cursor.execute(
            command
        )

        # Commit the transactions
        try:
            conn.commit()
            print("Transaction completed")
        except DatabaseError as e:
            conn.rollback() # Closing the transaction
            print("Transaction in conflict, cancelled")

    else:
        print("Data model already generated")


    command = """
        SELECT exists (
            SELECT FROM information_schema.tables 
                WHERE  table_schema = 'public' -- O el nombre de tu esquema
                AND    table_name   = 'message_groups'
        )
    """

    cursor.execute(
        command
    )

    fila = cursor.fetchone()
    conn.commit() # Closing transaction

    if fila[0] != True:
        print("Generating data model for message_groups")
        command = """
            CREATE TABLE ecobici_landing_work_queue(
                message_group_name VARCHAR(50),
                counter INTEGER,
                created_at TIME,
                updated_at TIME
            );
        """
        cursor.execute(
            command
        )
        
        # Commit the transaction
        try:
            conn.commit()
            print("Transaction completed")
        except DatabaseError as e:
            conn.rollback() # We declare a psycopg2 transaction faliure
            print("Transaction in conflict, cancelled")

    else:
        print("Modelo de datos ya generado")

def close_connection():
    cursor.close()
    conn.close()
