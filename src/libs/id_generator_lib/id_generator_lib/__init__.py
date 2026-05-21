from .init_database import try_init_database

try_init_database()

from .postgres_id_generator import PostgresIdGenerator

__all__ = ["PostgresIdGenerator"]
