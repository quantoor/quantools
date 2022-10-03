import sqlite3
from classes import Trade, Position


class DbClient:
    TRADES_RAW_TABLE = 'trades_raw'
    TRADES_TABLE = 'trades'
    TRADE_BASIS = 'trades_basis'
    POSITIONS_TABLE = 'positions'

    def __init__(self, db_full_path: str):
        self._conn = sqlite3.connect(db_full_path)
        self._create_tables()

    def _create_tables(self):
        query = f'''CREATE TABLE IF NOT EXISTS {self.TRADES_RAW_TABLE} (
                instrument TEXT NOT NULL,
                trade_id INTEGER PRIMARY KEY,
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

        query = f'''CREATE TABLE IF NOT EXISTS {self.POSITIONS_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument TEXT NOT NULL UNIQUE,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL);
                '''
        self._conn.execute(query)

        query = f'''CREATE TABLE IF NOT EXISTS {self.TRADES_TABLE} (
                instrument TEXT NOT NULL,
                order_id INTEGER PRIMARY KEY,
                n_trades INTEGER NOT NULL,
                side TEXT NOT NULL,
                price REAL NOT NULL,                
                amount REAL NOT NULL,     
                fee REAL NOT NULL,       
                timestamp INTEGER NOT NULL);
                '''
        self._conn.execute(query)

    def insert_trade_raw(self, t: Trade) -> None:
        query = f'''INSERT INTO {self.TRADES_RAW_TABLE} (instrument, trade_id, order_id, side, price, amount, fee, maker, timestamp, date)
                VALUES ('{t.instrument}', {t.trade_id}, {t.order_id}, '{t.side}', {t.price}, {t.amount}, {t.fee}, {t.maker}, {t.timestamp}, '{t.date}');
                '''
        try:
            self._conn.execute(query)
            self._conn.commit()
        except sqlite3.IntegrityError:
            pass

    def insert_position(self, p: Position) -> bool:
        side = 'long' if p.is_long else 'short'
        query = f'''INSERT INTO {self.POSITIONS_TABLE} (instrument, side, entry_price)
                VALUES ('{p.symbol}', '{side}', {p.entry_price});
                '''
        try:
            self._conn.execute(query)
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def insert_trade(self, instrument, order_id, n_trades, side, price, amount, fee, timestamp) -> None:
        query = f'''INSERT INTO {self.TRADES_TABLE} (instrument, order_id, n_trades, side, price, amount, fee, timestamp)
                    VALUES ('{instrument}', {order_id}, {n_trades}, '{side}', {price}, {amount}, {fee}, {timestamp});
                    '''
        try:
            self._conn.execute(query)
            self._conn.commit()
        except sqlite3.IntegrityError:
            pass

    def insert_trades(self):
        query = f'''SELECT 
                        instrument,
                        order_id,
                        COUNT(*) as n_trades,
                        side,
                        SUM(price * amount) / SUM(amount) as price,
                        SUM(amount) as amount,
                        SUM(fee) as fee,
                        MIN(timestamp) / 1000 as timestamp
                    FROM {self.TRADES_RAW_TABLE}
                    GROUP BY order_id
                    ORDER BY timestamp ASC;
                    '''
        cur = self._conn.cursor()
        cur.execute(query)
        trades_raw = cur.fetchall()

        for trade_raw in trades_raw:
            self.insert_trade(*trade_raw)

    def get_all_trades(self):
        query = f'''SELECT
                    instrument,
                    side,
                    price,
                    amount,
                    fee,
                    timestamp
                FROM {self.TRADES_TABLE}
                ORDER BY timestamp ASC;
                '''
        cur = self._conn.cursor()
        cur.execute(query)
        trades = cur.fetchall()

        trades_dict = {}

        for trade in trades:
            instrument, side, price, amount, fee, timestamp = trade
            tmp = {"side": side, "price": price, "amount": amount, "fee": fee, "timestamp": timestamp}
            if instrument in trades_dict:
                trades_dict[instrument].append(tmp)
            else:
                trades_dict[instrument] = [tmp]

        return trades_dict


db_client = DbClient('./db/30SEP22.db')
trades_ = db_client.get_all_trades()
print(trades_)
