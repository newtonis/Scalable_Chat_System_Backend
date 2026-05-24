import pytest
from kv_store_lib import RedisKVStore
import asyncio



# Verifies that a saved value can be read back from the Redis key-value store.
def test_save_and_read():
    async def get_value():
        kv_store = RedisKVStore("localhost") 
        await kv_store.set("Test Key", "My Value")
        value = await kv_store.get("Test Key")
        await kv_store.close()

        return value

    value = asyncio.run(get_value())
    
    assert value == "My Value"


# Verifies that setting the same key multiple times replaces its stored value.
def test_replace_stored_value():

    async def get_value_2():
        kv_store = RedisKVStore("localhost") 
        await kv_store.set("Test Key", "My Value")
        await kv_store.set("Test Key", "My Value 2")
        await kv_store.set("Test Key", "My Value 3")

        value = await kv_store.get("Test Key")
        
        await kv_store.delete("Test Key")
        await kv_store.close()

        return value

    value = asyncio.run(get_value_2())

    assert value == "My Value 3"


# Verifies that multiple keys can be stored and retrieved independently.
def test_two_keys():

    async def test_two_keys_f():
        kv_store = RedisKVStore("localhost") 

        await kv_store.set("Test Key 1", "My Value 1")
        await kv_store.set("Test Key 2", "My Value 2")

        value1 = await kv_store.get("Test Key 1")
        value2 = await kv_store.get("Test Key 2")

        await kv_store.delete("Test Key 1")
        await kv_store.delete("Test Key 2")

        await kv_store.close()

        return value1, value2

    value1, value2 = asyncio.run(test_two_keys_f())

    assert value1 == "My Value 1" and value2 == "My Value 2"


# Verifies that a key can be created and deleted, and that deleted keys return None.
def test_create_and_delete_key():
    async def test_create_and_delete_key():
        kv_store = RedisKVStore("localhost")

        await kv_store.set("Test Key A","My value A")
        value1 = await kv_store.get("Test Key A")

        await kv_store.delete("Test Key A")
        value2 = await kv_store.get("Test Key A")
        
        await kv_store.delete("Test Key A")
        await kv_store.delete("Test Key B")
        
        await kv_store.close()

        return value1, value2

    value1, value2 = asyncio.run(test_create_and_delete_key())

    assert value1 == "My value A" and value2 == None


# Verifies that keys can be queried by prefix and all matching values are returned.
def test_query_prefix():
    async def test_query_prefix():
        kv_store = RedisKVStore("localhost")

        await kv_store.set("Test345GR Key Ga1","My value A")
        await kv_store.set("Test345GR Key Ha1","My value B")
        await kv_store.set("Test345GR Key Ia1","My value C")

        answer = {}

        async for key, value in kv_store.get_all_with_prefix("Test345GR Key "):
            answer[key] = value

        await kv_store.delete("Test345GR Key Ga1")
        await kv_store.delete("Test345GR Key Ha1")
        await kv_store.delete("Test345GR Key Ia1")

        await kv_store.close()

        return answer
    
    answer = asyncio.run(test_query_prefix())

    assert len(answer) == 3 
    assert answer["Test345GR Key Ga1"] == "My value A"
    assert answer["Test345GR Key Ha1"] == "My value B"
    assert answer["Test345GR Key Ia1"] == "My value C"


# Verifies that keys with a specific suffix can be deleted and other keys remain intact.
def test_query_delete_with_suffix():
    async def write_keys():
        kv_store = RedisKVStore("localhost")

        await kv_store.set("egrergerge____Mysuffix","My value A")
        await kv_store.set("sdfsdfsdfsdf_____Mysuffix","My value B")
        await kv_store.set("egresdfsdfe____Mysuffix","My value C")
        await kv_store.set("other_key","My value D")

        v1 = await kv_store.get("egrergerge____Mysuffix")
        v2 = await kv_store.get("sdfsdfsdfsdf_____Mysuffix")
        v3 = await kv_store.get("egresdfsdfe____Mysuffix")
        v4 = await kv_store.get("other_key")

        
        await kv_store.close()

        return v1, v2, v3, v4
    

    v1, v2, v3, v4 = asyncio.run(write_keys())

    assert v1 == "My value A" and v2 == "My value B" and v3 == "My value C" and v4 == "My value D"

    async def delete_keys():
        kv_store = RedisKVStore("localhost")
        
        await kv_store.delete_all_with_suffix("Mysuffix")

        v1 = await kv_store.get("egrergerge____Mysuffix")
        v2 = await kv_store.get("sdfsdfsdfsdf_____Mysuffix")
        v3 = await kv_store.get("egresdfsdfe____Mysuffix")
        v4 = await kv_store.get("other_key")

        await kv_store.delete("other_key")
        await kv_store.close()

        return v1, v2, v3, v4
    
    v1_, v2_, v3_, v4_ = asyncio.run(delete_keys())

    assert v1_ is None and v2_ is None and v3_ is None and v4_ == "My value D"


# Verifies combined prefix and suffix delete operations maintain correct key behavior.
def test_query_delete_with_prefix_and_suffix():
     
    async def write_keys():
        kv_store = RedisKVStore("localhost")

        await kv_store.set("MyPrefix______egrergerge____Mysuffix","My value A")
        await kv_store.set("MyPrefix______sdfsdfsdfsdf_____Mysuffix","My value B")
        await kv_store.set("egresdfsdfe____Mysuffix","My value C")
        await kv_store.set("MyPrefix______other_key","My value D")

        v1 = await kv_store.get("MyPrefix______egrergerge____Mysuffix")
        v2 = await kv_store.get("MyPrefix______sdfsdfsdfsdf_____Mysuffix")
        v3 = await kv_store.get("egresdfsdfe____Mysuffix")
        v4 = await kv_store.get("MyPrefix______other_key")

        await kv_store.close()

        return v1, v2, v3, v4
    

    v1, v2, v3, v4 = asyncio.run(write_keys())

    assert v1 == "My value A" and v2 == "My value B" and v3 == "My value C" and v4 == "My value D"

    async def delete_keys():
        kv_store = RedisKVStore("localhost")
        
        await kv_store.delete_all_with_suffix("Mysuffix")

        v1 = await kv_store.get("MyPrefix______egrergerge____Mysuffix")
        v2 = await kv_store.get("MyPrefix______sdfsdfsdfsdf_____Mysuffix")
        v3 = await kv_store.get("egresdfsdfe____Mysuffix")
        v4 = await kv_store.get("MyPrefix______other_key")

        await kv_store.delete("egresdfsdfe____Mysuffix")
        await kv_store.delete("MyPrefix______other_key")
        
        await kv_store.close()

        return v1, v2, v3, v4
    
    v1_, v2_, v3_, v4_ = asyncio.run(delete_keys())

    assert v1_ is None and v2_ is None and v3_ is None and v4_ == "My value D"
