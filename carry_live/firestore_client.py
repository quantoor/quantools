import firebase_admin
from firebase_admin import credentials, firestore
from classes import StrategyStatus
from typing import Optional


cred = credentials.Certificate("carrybot-2426e-firebase-adminsdk-woiqw-d35ffd970c.json")
firebase_admin.initialize_app(cred)


class FirestoreClient:
    collection = 'strategies'

    def __init__(self):
        self._db = firestore.client()

    def set(self, value: StrategyStatus) -> None:
        data = value.to_dict()
        self._db.collection(self.collection).document(value.coin).set(data)

    def get(self, key: str) -> Optional[StrategyStatus]:
        res = self._db.collection(self.collection).document(key).get()
        if not res.exists:
            return None
        res_dict = res.to_dict()
        return StrategyStatus().from_dict(res_dict)


# db = firestore.client()
# data = {'coin':'BTC'}
# db.collection('strategies').document('BTC').set(data)
# res = db.collection('strategies').get()
# r = res[0]
# print(res[0].to_dict())
