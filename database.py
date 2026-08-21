import sqlite3
import json as js
import questionary



class MarketLabDataBase:

    def __init__(self, name):
        self.name = name
        self.conn = sqlite3.connect(self.name)
        self.cursor = self.conn.cursor()

    def get_symbol(self):
        row = self.cursor.execute("""SELECT symbol FROM database_metadata""").fetchone()[0]
        return row

    def get_timeframe(self):
        row = self.cursor.execute("""SELECT timeframe FROM database_metadata""").fetchone()[0]
        return row
        
    def add_column(self, column, table):
        self.cursor.execute(f"""
        ALTER TABLE {table}
        ADD COLUMN {column}""")
        self.conn.commit()

    def drop_column(self, column, table):
        self.cursor.execute(f"""
        ALTER TABLE {table}
        DROP COLUMN {column}""")
        self.conn.commit()

    def database_commit(self):
        self.conn.commit()

    def get_start_timestamp(self):
        start_timestamp = self.cursor.execute("""SELECT MAX(open_time) 
                                                FROM candles""").fetchone()[0]
        return start_timestamp

    def get_columns(self, table):
        rows = self.cursor.execute(f"""PRAGMA table_info({table})""").fetchall()
        columns = [r[0] for r in rows]
        return columns

    def close_database(self):
        self.database_commit()
        self.conn.close()

    def save_indicator(self, name, results, parameters):

        cursor = self.cursor
        json_para = js.dumps(parameters)
        
        cursor.executemany(f"""
        UPDATE candles
        SET {name} = ?
        WHERE open_time = ?
    """, results)

        cursor.execute(f"""
            INSERT INTO indicators_metadata (column_name, function_name, parameters)
            VALUES (?, ?, ?)
    """, (name, function.__name__, json_para))

        self.conn.commit()

    def save_event(self, name, results, parameters):

        cursor = self.cursor
        json_para = js.dumps(parameters)
        
        cursor.executemany(f"""
        UPDATE status
        SET {name} = ?
        WHERE open_time = ?
    """, results)

        cursor.execute(f"""
            INSERT INTO indicators_metadata (column_name, function_name, parameters)
            VALUES (?, ?, ?)
    """, (name, function.__name__, json_para))

        self.conn.commit()

    def get_data(self, table, column):
        cursor = self.cursor

        if column_exists(cursor, table=table, column="open_time"):
            rows = cursor.execute(f"""
                    SELECT {column}
                    FROM {table}
                    ORDER BY open_time
    """).fetchall()
        else:
            rows = cursor.execute(f"""
                    SELECT {column}
                    FROM {table}
                    ORDER BY open_time
    """).fetchall()

        data = [r[0] for r in rows]

        return data

    def create_database(self, symbol, timeframe):

        self.cursor.execute("""
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
        
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS status(
                    open_time INTEGER PRIMARY KEY)""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS database_metadata(for_marketlab INTEGER,
        symbol TEXT,
        timeframe TEXT)""")

        self.database_commit()

        self.cursor.execute("""
                INSERT INTO database_metadata(symbol, timeframe, for_marketlab)
                VALUES (?, ?, ?)
        """, (symbol, timeframe, 1))

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS indicators_metadata(indicator_name TEXT PRIMARY KEY, 
        function_name TEXT, 
        parameters TEXT)""")

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS events_metadata(event_name TEXT PRIMARY KEY, 
        function_name TEXT, 
        parameters TEXT)""")

        self.database_commit()

    def delete_values(self, table, name):
        self.cursor.execute(f"""
                        DELETE FROM ({table})
                        WHERE column_name = ?
                """, (name,))

    def insert_download_data(self, values, open_time):

        features = "open_time, open, high, low, close, volume, close_time, quote_asset_vol, number_of_trades, taker_buy_base_asset_volume, taker_buy_quote_asset_volume"
        
        self.cursor.execute(
            f"INSERT OR IGNORE INTO candles ({features}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
            values
            )

        self.cursor.execute(
            "INSERT OR IGNORE INTO status (open_time) VALUES (?)", (open_time,))

    def get_open_times(self):
        rows = self.cursor.execute(f"""
            SELECT open_time
            FROM candles
            ORDER BY open_time
            """).fetchall()

        rows = [r[0] for r in rows]

        return rows

    def add_calculated_indicator(self, results: list, name: str, json_para, function_name):
        self.cursor.executemany(f"""
        UPDATE candles
        SET {name} = ?
        WHERE open_time = ?
    """, results)

        self.cursor.execute(f"""
        INSERT INTO indicators_metadata (indicator_name, function_name, parameters)
        VALUES (?, ?, ?)
""", (name, function_name, json_para))

    def column_exists(cursor, table, column):
        cursor.execute(f"PRAGMA table_info({table})")
        return column in {row[1] for row in cursor.fetchall()}


class MarketLabRessources:

    def __init__(self, name):

        self.name = name
        self.conn = sqlite3.connect(self.name)
        self.cursor = self.conn.cursor

    def create_ressources_database(self):
        self.cursor.execute("""
            CREATE TABLE indicator_dict(
            indicator_name PRIMARY KEY,
            nb_parameters REAL,
            recommended_parameters TEXT,
            type TEXT,
            indicator_list TEXT
            )
            """)

        self.cursor.execute("""
            CREATE TABLE event_dict(
            event_name PRIMARY KEY,
            nb_parameters REAL,
            recommended_parameters TEXT,
            type TEXT,
            event_list TEXT
            )
""")
        self.conn.commit()

    def get_indicator_nb_parameters(self, name: str) -> int:
        nb = self.cursor.execute(f"""
        SELECT nb_parameters
        FROM indicator_dict
        WHERE indicator_name = {name}""").fetchone()[0]
        return nb

    def get_indicator_recommended_parameters(self, name: str) -> list:
        r = self.cursor.execute(f"""
        SELECT recommended parameters
        FROM indicator_dict
        WHERE indicator_name = {name}""").fetchone()[0]

        r = js.loads(r)
        r = r["r"]
        r = [i[0] for i in r]
        return r

    def get_indicator_prompt(self, name: str) -> list:
        r = self.cursor.execute(f"""
        SELECT recommended parameters
        FROM indicator_dict
        WHERE indicator_name = {name}""").fetchone()[0]

        r = js.loads(r)
        r = r["r"]

        r = [i[1] for i in r]
        
        return r

    def get_indicator_prompt_verification(self, name: str) ->list:
        r = self.cursor.execute(f"""
        SELECT recommended parameters
        FROM indicator_dict
        WHERE indicator_name = {name}""").fetchone()[0]

        r = js.loads(r)
        r = r["r"]

        r = [i[2] for i in r]
        
        return r

    def get_indicator_type(self, name: str) -> str:
        t = self.cursor.exectue(f"""
        SELECT type
        FROM indicator_dict
        WHERE indicator_name = {name}""").fetchone()[0]
        return t

    def get_indicator_dict(self) -> dict:
        l = self.cursor.execute("""SELECT indicator_list FROM indicator_dict""").fetchone()[0]
        l = js.loads(l)
        return l 

    def get_indicator_function(self, name: str) -> function:
        f = self.get_indicator_dict()
        f = f[name]
        return f
    
    def get_event_nb_parameters(self, name: str) -> int:
        nb = self.cursor.execute(f"""
        SELECT nb_parameters
        FROM event_dict
        WHERE event_name = {name}""").fetchone()[0]
        return nb

    def get_event_recommended_parameters(self, name: str) -> dict:
        r = self.cursor.execute(f"""
        SELECT recommended_parameters
        FROM event_dict
        WHERE event_name = {name}""").fetchone()[0]
 
        r = r["r"]

        return r

    def get_event_type(self, name):
        t = self.cursor.exectue(f"""
        SELECT type
        FROM event_dict
        WHERE event_name = {name}""").fetchone()[0]
        return t

    def get_event_dict(self):
        l = self.cursor.execute("""SELECT event_list FROM event_dict""").fetchone()[0]
        l = js.loads(l)
        return l 
        
    def add_indicator(self, ressources: dict):

        name = ressources["name"]
        nb = ressources["nb"]
        r = ressources["r"]
        f = ressources["f"]
        t = ressources["t"]

        r = {"r" : r}
        r = js.dumps(r)

        indicator_list = self.cursor.execute("""SELECT indicator_list FROM indicator_dict""").fetchone()[0]
        indicator_list[f.__name__] = f
        indicator_list = js.dumps(indicator_list)

        self.cursor.execute("""
        INSERT INTO indicator_dict (indicator_name, nb_parameters, recommended_parameters, type)
        VALUES (?, ?, ?, ?)""", (name, nb, r, t))

        self.cursor.execute(f"""
        UPDATE indicator_dict
        SET indicator_list = {indicator_list}""")

        self.conn.commit()

    def add_events(self, ressources):

        name = ressources["name"]
        nb = ressources["nb"]
        r = ressources["r"]
        f = ressources["f"]
        t = ressources["t"]

        r = {"r" : r}
        r = js.dumps(r)

        event_list = self.cursor.execute("""SELECT indicator_list FROM indicator_dict""").fetchone()[0]
        event_list[f.__name__] = f
        event_list = js.dumps(event_list)

        self.cursor.execute(""""
        INSERT INTO events_dict (event_name, nb_parameters, recommended_parameters, type)
        VALUES (?, ?, ?, ?)""", (name, nb, r, t))

        self.conn.commit()

    def create_ressources(self, nb: int, r: list, f: function, t: str) -> dict:
        ressources = {
            "name" : f.__name__,
            "nb" : nb,
            "r" : r,
            "f" : f,
            "t" : t, 
        }
        return ressources

    def create_recommended_parameters(self, recommended: list, prompt: list, verification: list) -> list:
        r = []

        if len(recommended) != len(prompt) or len(recommended) != len(verification) or len(prompt) != len(verification):
            return None

        for i in range(len(recommended)):
            r.append((recommended[i], prompt[i], verification[i]))

        return r

def is_marketlad_database(file):

    try:
        conn = sqlite3.connect(file)

    except sqlite3.DatabaseError:
        return False

    cursor = conn.cursor()

    rows = cursor.execute("""SELECT name FROM sqlite_master WHERE type = 'table';""")
    tables = [r[0] for r in rows]

    print(tables)

    if "database_metadata" in tables:
        print("test database")
        if column_exists(cursor, "database_metadata", "for_marketlab"):
            print("good")
            return True
        else:
            print("no for_marketlab")
            False
    else: 
        print("no database metadata")
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
