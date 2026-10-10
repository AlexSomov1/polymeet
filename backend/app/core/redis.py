from redis.asyncio import Redis
from starlette.requests import Request


def create_redis(url: str) -> Redis:
    client: Redis = Redis.from_url(url, decode_responses=True, socket_connect_timeout=1)
    return client


async def get_redis(request: Request) -> Redis:
    redis: Redis = request.app.state.redis
    return redis
