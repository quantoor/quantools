import sqlite3


class DbTrade:
    def __init__(self, trade_id: int, instrument: str, side: str, price: float, amount: float, timestamp: int,
                 maker: bool):
        self.trade_id = trade_id
        self.instrument = instrument
        self.side = side
        self.price = price
        self.amount = amount
        self.timestamp = timestamp
        self.maker = maker


class DbClient:
    TRADES_TABLE = 'trades'
    ORDERS_TABLE = 'orders'
    POSITIONS = 'positions'

    def __init__(self, db_full_path: str):
        self._conn = sqlite3.connect(db_full_path)
        self._create_tables()

    def _create_tables(self):
        query = f'''CREATE TABLE IF NOT EXISTS {self.TRADES_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER NOT NULL UNIQUE,
                instrument TEXT NOT NULL,
                side TEXT NOT NULL,
                price REAL NOT NULL,                
                amount REAL NOT NULL,
                timestamp INTEGER NOT NULL,
                maker BOOL NOT NULL);
                '''
        self._conn.execute(query)

    def insert_trade(self, t: DbTrade) -> bool:
        query = f'''INSERT INTO {self.TRADES_TABLE} (trade_id, instrument, side, price, amount, timestamp, maker)
                VALUES ({t.trade_id},'{t.instrument}', '{t.side}', {t.price}, {t.amount}, {t.timestamp}, {t.maker});
                '''
        try:
            self._conn.execute(query)
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_trade(self):
        query = f'''SELECT * FROM {self.TRADES_TABLE};'''
        cur = self._conn.cursor()
        cur.execute(query)
        return cur.fetchall()


if __name__ == '__main__':
    db_client = DbClient('./db/30SEP22.db')
    db_client.insert_trade(DbTrade(42, 'BTC-PERP', 'Buy', 21000, 0.01, 12345, False))
    print(db_client.get_trade())
