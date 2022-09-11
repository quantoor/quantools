import redis
import json


class RedisClient:
    def __init__(self, host='localhost', port=6379, db=0):
        self._r = redis.Redis(host=host, port=port, db=db)

    def get(self, key: str):
        return json.loads(self._r.get(key))

    def set(self, key: str, value: dict):
        self._r.set(key, json.dumps(value))

    def delete(self):
        pass
