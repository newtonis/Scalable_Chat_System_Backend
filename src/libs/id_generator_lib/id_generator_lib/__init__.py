from .database_conn import database_conn

database_conn.try_init_database()

from .postgres_id_generator import PostgresIdGenerator

__all__ = ["PostgresIdGenerator"]
