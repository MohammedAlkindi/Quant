import json
import redis


class RedisCache:
    def __init__(self, redis_url: str):
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)

    def get(self, key: str):
        raw = self.client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def set(self, key: str, value, ttl: int = 5) -> None:
        self.client.setex(key, ttl, json.dumps(value))
