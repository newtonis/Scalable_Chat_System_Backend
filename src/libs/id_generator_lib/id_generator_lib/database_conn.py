import psycopg2
import psycopg2.extras

import os
from dotenv import load_dotenv
import logging
import atexit


### Database connection singleton

class DatabaseConn:
    def __init__(self, postgres_host):
        logging.info("Starting database connection ...")

        load_dotenv()
        POSTGRES_DB = os.environ["POSTGRES_DB"]
        POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
        POSTGRES_USER = os.environ["POSTGRES_USER"]

        conn_string = f"host='{postgres_host}' dbname='{POSTGRES_DB}' user='{POSTGRES_USER}' password='{POSTGRES_PASSWORD}'"
        self.conn = psycopg2.connect(conn_string)
        self.conn.autocommit = False

        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
    
    # Try to init the dabase (if already created has no effect)
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

        cursor.execute(
            command
        )

        fila = cursor.fetchone()
        conn.commit() # Cerramos la transaccion


        if fila[0] != True:
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

            cursor.execute(
                command
            )

            # Commit the transactions
            try:
                conn.commit()
                logging.info("Data model generated")
            except psycopg2.DatabaseError as e:
                conn.rollback() # Closing the transaction
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
