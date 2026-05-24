import random

import pytest
from id_generator_lib import DatabaseConn, PostgresIdGenerator


@pytest.fixture
def database_conn():
    db_conn = DatabaseConn("localhost")
    db_conn.try_init_database()

    try:
        yield db_conn
    finally:
        db_conn.close_connection()


# Verifies that a valid ID is generated for a new message group.
def test_generate_single_id(database_conn):

    postgres_id_generator = PostgresIdGenerator(database_conn)
    code = str(random.randrange(1000))
    result = postgres_id_generator.generate_new_id(f"Test msg group {code}")

    assert result["status"] == "id_generated"


# Verifies that ID generation for the same group increments correctly by 1.
def test_increment_id(database_conn):

    postgres_id_generator = PostgresIdGenerator(database_conn)
    code = str(random.randrange(1000))

    result1 = postgres_id_generator.generate_new_id(f"Test msg group {code}")
    result2 = postgres_id_generator.generate_new_id(f"Test msg group {code}")
    result3 = postgres_id_generator.generate_new_id(f"Test msg group {code}")

    assert result1["result"] + 1 == result2["result"] and result2["result"] + 1 == result3["result"]
