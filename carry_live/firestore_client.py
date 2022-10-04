import firebase_admin
from firebase_admin import credentials, firestore
from classes import StrategyStatus
from typing import Optional
import time


cred = credentials.Certificate("carrybot-2426e-firebase-adminsdk-woiqw-d35ffd970c.json")
firebase_admin.initialize_app(cred)


class FirestoreClient:
    strategy_settings = 'settings'
    strategies_status = 'strategies'

    settings_last_query_ts = time.time()
    settings = None

    def __init__(self):
        self._db = firestore.client()

    def get_strategy_settings(self):
        if self.settings is None or (time.time() - self.settings_last_query_ts > 10):
            res = self._db.collection(self.strategy_settings).document('strategy').get()
            if not res.exists:
                raise Exception('strategy settings not found in Firestore')
            self.settings = res.to_dict()
            self.settings_last_query_ts = time.time()
        return self.settings

    def set_strategy_status(self, value: StrategyStatus) -> None:
        data = value.to_dict()
        self._db.collection(self.strategies_status).document(value.coin).set(data)

    def get_strategy_status(self, key: str) -> Optional[StrategyStatus]:
        res = self._db.collection(self.strategies_status).document(key).get()
        if not res.exists:
            return None
        res_dict = res.to_dict()
        return StrategyStatus().from_dict(res_dict)
