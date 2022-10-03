# -*- coding: utf-8 -*-
"""
@Time 24.09.22 18:15
@Author: emanuele.bolognesi
"""
import redis
import json
from typing import List, Optional
from classes import StrategyStatus


class RedisClient:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 3):
        self._r = redis.Redis(host=host, port=port, db=db)

    def set(self, value: StrategyStatus) -> None:
        self._r.set(value.coin, json.dumps(value.to_dict()))

    def get(self, key: str) -> Optional[StrategyStatus]:
        res = self._r.get(key)
        if res is None:
            return None
        return StrategyStatus().from_dict(json.loads(res))

    def get_all_keys(self) -> List[str]:
        return [key.decode() for key in self._r.scan_iter("*")]

    def get_all_values(self) -> List[StrategyStatus]:
        return [self.get(key) for key in self.get_all_keys()]

    def delete(self, key: str) -> None:
        self._r.delete(key)
