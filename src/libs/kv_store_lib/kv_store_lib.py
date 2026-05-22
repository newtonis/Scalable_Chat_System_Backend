import asyncio
import redis.asyncio as aioredis
import logging

# Approach for kv store: simple redis database to handle cache strategy
# for data persistence

class RedisKVStore:
    def __init__(self, host):
        self.r = aioredis.from_url(f"redis://{host}:6379", decode_responses=True)

    async def get(self, key: str):
        data = await self.r.get(f"{key}:100")
        return data

    async def set(self, key: str, value):
        await self.r.set(f"{key}:100", value)

    async def delete(self, key: str):
        await self.r.delete(f"{key}:100")
    
    async def get_all_with_prefix(self, prefix: str):
        async for key in self.r.scan_iter(match=f"{prefix}*", count=100):
            value = await self.r.get(key)
            yield key[:-4], value

    async def delete_all_with_suffix(self, suffix: str):
        async for key in self.r.scan_iter(match=f"*{suffix}:100", count=100):
            await self.r.unlink(key)

    async def delete_all_with_prefix_and_suffix(self, prefix: str, suffix: str):
        async for key in self.r.scan_iter(match=f"{prefix}*{suffix}:100", count=100):
            await self.r.unlink(key)
    
    async def close(self):
        await self.r.aclose()

      