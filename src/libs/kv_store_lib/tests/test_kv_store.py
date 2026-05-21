import pytest
from kv_store_lib import RedisKVStore
import asyncio



def test_save_and_read():
    async def get_value():
        kv_store = RedisKVStore("localhost") 
        await kv_store.set("Test Key", "My Value")
        value = await kv_store.get("Test Key")
        await kv_store.close()

        return value

    value = asyncio.run(get_value())
    
    assert value == "My Value"


def test_replace_stored_value():

    async def get_value_2():
        kv_store = RedisKVStore("localhost") 
        await kv_store.set("Test Key", "My Value")
        await kv_store.set("Test Key", "My Value 2")
        await kv_store.set("Test Key", "My Value 3")

        value = await kv_store.get("Test Key")
        await kv_store.close()

        return value

    value = asyncio.run(get_value_2())

    assert value == "My Value 3"


def test_two_keys():

    async def test_two_keys_f():
        kv_store = RedisKVStore("localhost") 

        await kv_store.set("Test Key 1", "My Value 1")
        await kv_store.set("Test Key 2", "My Value 2")

        value1 = await kv_store.get("Test Key 1")
        value2 = await kv_store.get("Test Key 2")

        await kv_store.close()

        return value1, value2

    value1, value2 = asyncio.run(test_two_keys_f())

    assert value1 == "My Value 1" and value2 == "My Value 2"


def test_create_and_delete_key():
    async def test_create_and_delete_key():
        kv_store = RedisKVStore("localhost")

        await kv_store.set("Test Key A","My value A")
        value1 = await kv_store.get("Test Key A")

        await kv_store.delete("Test Key A")
        value2 = await kv_store.get("Test Key A")

        return value1, value2

    value1, value2 = asyncio.run(test_create_and_delete_key())

    assert value1 == "My value A" and value2 == None


def test_query_prefix():
    async def test_query_prefix():
        kv_store = RedisKVStore("localhost")

        await kv_store.set("Test345GR Key Ga1","My value A")
        await kv_store.set("Test345GR Key Ha1","My value B")
        await kv_store.set("Test345GR Key Ia1","My value C")

        answer = {}

        async for key, value in kv_store.get_all_with_prefix("Test345GR Key "):
            answer[key] = value
        return answer

        await kv_store.delete("Test345GR Key Ga1")
        await kv_store.delete("Test345GR Key Ha1")
        await kv_store.delete("Test345GR Key Ia1")
    
    answer = asyncio.run(test_query_prefix())

    assert len(answer) == 3 
    assert answer["Test345GR Key Ga1"] == "My value A"
    assert answer["Test345GR Key Ha1"] == "My value B"
    assert answer["Test345GR Key Ia1"] == "My value C"
