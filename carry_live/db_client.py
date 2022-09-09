import sqlite3
from classes import Trade


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
                instrument TEXT NOT NULL,
                trade_id INTEGER NOT NULL UNIQUE,
                order_id INTEGER NOT NULL,
                side TEXT NOT NULL,
                price REAL NOT NULL,                
                amount REAL NOT NULL,
                fee REAL NOT NULL,
                maker BOOL NOT NULL,                
                timestamp INTEGER NOT NULL,
                date TEXT NOT NULL);
                '''
        self._conn.execute(query)

    def insert_trade(self, t: Trade) -> bool:
        query = f'''INSERT INTO {self.TRADES_TABLE} (instrument, trade_id, order_id, side, price, amount, fee, maker, timestamp, date)
                VALUES ('{t.instrument}', {t.trade_id}, {t.order_id}, '{t.side}', {t.price}, {t.amount}, {t.fee}, {t.maker}, {t.timestamp}, '{t.date}');
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
