import questionary
import data_extraction as de
import sqlite3
import applications as app

def skip(erase):
    res = questionary.select("Close ?", choices=["Yes"]).ask()
    if res == "Yes":
        print(erase, end="")

def yes_no(question):
    rep = questionary.select(question, ["No", "Yes"]).ask()
    return rep

def data_base(erase):

    symbol = input("Symbol : ")
    interval = input("Interval : ")
    source = questionary.select("Source : ", choices=["Binance", "HyperLiquid"]).ask()

    print(erase, end="")
    print(erase, end="")
    print(erase, end="")    

    symbol = symbol.upper() + "USDT"

    conn = sqlite3.connect(f"data_{symbol}_{interval}_{source}")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candles(

        open_time INTEGER PRIMARY KEY,

        open REAL,

        high REAL,
        low REAL,

        close REAL,

        volume REAL, 

        close_time REAL,
        
        vwema,
        vwema_savgol,

        quote_asset_vol REAL, 

        number_of_trades REAL,

        taker_buy_base_asset_volume REAL,
        taker_buy_quote_asset_volume REAL,

        statut REAL

    )
    """)

    conn.commit()

    return conn, cursor, source, symbol, interval



def download_data(cursor, symbol, interval, source, timestamp, erase, conn, history):
    print(erase, end="")
    print("💾 Download Data")
    
    if source == "Binance":
            de.extraction_binance(cursor, symbol, interval, timestamp)
            conn.commit()
    
    print("Data Downloaded !")
    
    if source == "Hyperliquid":
        de.extraction_hyperliquid(cursor, symbol, interval, timestamp)
        conn.commit()
    
        print("Data Downloaded !")
    
        history.append(f"{symbol} {interval} Downloaded From {source}")

        skip()
        print(erase, end="")
        print(erase, end="")
        print(erase, end="")
        print(erase, end="")


def calculate_indic(erase, function_dict, function_list, cursor, history, symbol, interval):

    print(erase, end="")
    print("📈 Calculate Indicators")

    name = input("Name : ")
    after_name = questionary.select("Adding an After Name ? : ",
                                        ["False", "True"]).ask()
    after_name = bool(after_name)

   

    function_ = questionary.autocomplete("Select a function :", choices=function_list).ask()
    function_ = function_dict[function_]

    window = input("Window : ")

    try:
        window = int(window)

    except ValueError:
        print("You must enter an inter greater than 0")


    parameters = []

    cursor.execute("""PRAGMA table_info(candles)""")
    existing_parameters = [row[1] for row in cursor.fetchall()]

    for i in range(function_[1]):
        parameters.append(questionary.autocomplete(f"Select parameter {i+1} : ", choices=existing_parameters).ask())

    app.general_application(cursor, name, after_name, function_[0], window, parameters)

    history.append(f"{name} {window} {parameters} Calculated on {symbol} {interval}")

    skip(erase)

    for i in range(6):
        print(erase, end="")


def delete_col(erase, cursor):

    print(erase, end="")
    print("🗑️  Delete Column")

    cursor.execute("""PRAGMA table_info(candles)""")
    existing_parameters = [row[1] for row in cursor.fetchall()]

    parameters = questionary.select(f"Select parameter : ", choices=existing_parameters+["Exit"]).ask()

    if parameters == "Exit":
        print(erase, end="")
        print(erase, end="")

    else:
        rep = yes_no(f"Deleting {parameters} ? For real 🤨 ?")

        if rep == "Yes":
            cursor.execute(f"""
                ALTER TABLE candles
                DROP COLUMN {parameters}""")
            print(erase, end="")
            print(erase, end="")
            print(erase, end="")

        else:
            print(erase, end="")
            print(erase, end="")
            print(erase, end="")

