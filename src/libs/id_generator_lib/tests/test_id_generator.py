from id_generator_lib import PostgresIdGenerator
import random


# Generate a single count of a group
def test_generate_single_id():
    postgres_id_generator = PostgresIdGenerator()
    code = str(random.randrange(1000))
    result = postgres_id_generator.generate_new_id(f"Test msg group {code}")

    assert result["status"] == "id_generated"


# Generate multiple increments of the group
def test_increment_id():
    postgres_id_generator = PostgresIdGenerator()
    code = str(random.randrange(1000))

    result1 = postgres_id_generator.generate_new_id(f"Test msg group {code}")
    result2 = postgres_id_generator.generate_new_id(f"Test msg group {code}")
    result3 = postgres_id_generator.generate_new_id(f"Test msg group {code}")

    assert result1["result"] + 1 == result2["result"] and result2["result"] + 1 == result3["result"]
