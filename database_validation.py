import sqlite3

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return column in {row[1] for row in cursor.fetchall()}


class MarketLabDataBase:

    def __init__(self, name, symbol, timeframe):

        self.name = name
        self.conn = sqlite3.connect(self.name)

        self.cursor = self.data_base.cursor()

        self.symbol = symbol

        self.timeframe = timeframe
        
        self.candles_table = self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS candles(
                    open_time INTEGER PRIMARY KEY,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL, 
                    close_time REAL,
                    quote_asset_vol REAL, 
                    number_of_trades REAL,
                    taker_buy_base_asset_volume REAL,
                    taker_buy_quote_asset_volume REAL)""")
        
        self.status_table = self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS status(
                    open_time INTEGER PRIMARY KEY)""")
        
        self.indicators_metadata_table = self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS indicators_metadata(
                    column_name TEXT PRIMARY KEY,
                    function_name TEXT,
                    parameters TEXT)""")

        self.database_metadata = self.cursor.execute(""""
                CREATE TABLE IF NOT EXISTS database_metadata(
                    for_marketlab INTEGER,
                    symbol TEXT = ?
                    timeframe TEXT = ?)""")


        

    def add_column(self, column, table):
        self.cursor.execute(f"""
        ALTER TABLE {table}
        ADD COLUMN {column}""")
        self.conn.commit()

    def drop_column(self, column, table):
        self.cursor.exexute(f"""
        ALTER TABLE {table}
        DROP COLUMN {column}""")
        self.conn.commit()

    def database_commit(self):
        self.conn.commit()

    def get_start_timestamp(self):
        start_timestamp = self.cursor.execute("""SELECT MAX(open_time) 
                                                FROM candles""").fetchone()[0]
        return start_timestamp

def is_marketlad_database(file):

    try:
        conn = sqlite3.connect(file)

    except sqlite3.DatabaseError:
        return False

    cursor = conn.cursor()

    rows = cursor.execute("""SELECT name FROM sqlite_master WHERE type = 'table';""")
    tables = [r[0] for r in rows]

    if "database_metadata" in tables:
        if column_exists(cursor, "database_metadata, for_marketlab"):
            return True
        else:
            False

    else: 
        return False
    
def validate_tables(tables_list, tables):
    missing_tables = []
    for i in range(tables_list):
        if tables[i] not in tables_list:
            missing_tables.append(tables[i])

    if len(missing_tables) > 0:
        return False, missing_tables

    else:
        return True, missing_tables
    
def column_type(cursor, column, table_name):
    rows = cursor.execute(f"""PRAGMA table_info({table_name})""").fetchall()

    for r in rows:
        if r[1] == column:
            return r[2]

def validate_table_candles(cursor):
    return column_exists(cursor=cursor, table="candles", column="open_time")

def validate_table_status(cursor):
    validate = column_exists(cursor=cursor, table="status", column="open_time")
    return validate

def validate_table_indicatorsmetadata(cursor):
    validate = (None, None, None,)
    validate[0] = column_exists(cursor=cursor, table="indicators_metadata", column="column_name")
    validate[1] = column_exists(cursor=cursor, table="indicators_metadata", column="function_name")
    validate[2] = column_exists(cursor=cursor, table="indicators_metadata", column="parameters")

    if False in validate:
        return 
    else:
        return True
