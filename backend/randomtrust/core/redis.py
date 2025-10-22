import redis.asyncio as redis

from .config import Settings


def create_redis(settings: Settings) -> redis.Redis:
    return redis.from_url(str(settings.redis_url), decode_responses=False)


async def close_redis(client: redis.Redis) -> None:
    await client.aclose()
