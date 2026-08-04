import math_formula as mf
import event as ev
import stat_making as sm
import applications as app
import sqlite3
import data_extraction as de
from datetime import *
import questionary 

start = datetime(2017, 8, 17)             # limites temporelles de l'exctraction des donnés 
timestamp = int(start.timestamp() * 1000)
erase = "\033[F\033[K"

function_dict = {
    "sma" : (mf.sma, 1),
    "ema" : (mf.ema, 1),
    "atr" : (mf.atr, 1),
    "rsi" : (mf.rsi, 2),
    "vwma" : (mf.vwma, 2),
    "amplitude" : (mf.amplitude, 2)
}

function_list = list(function_dict.keys())

values_list = []

print(" ")
print(" ")

questionary.print("-- MARKET LAB --", style="fg:pink")

def data_base():

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

    print("")
    questionary.print(f"Working on {symbol} {interval} {source}", style="fg:yellow") 
    print("")

    conn.commit()

    return conn, cursor, source, symbol, interval


conn, cursor, source, symbol, interval = data_base()

history = []

while True :

    command = questionary.select("Actions : ", 
                                choices = [
                                "📁 Change or Create a DataBase",
                                "💾 Download Data",
                                "📈 Calculate Indicators",
                                "📊 Calculate Stats",
                                "📉 Plot",
                                "🗑️  Delete Column", 
                                "📘 History",
                                "❌ Exit"]).ask()

    print(erase)

    if command == "📁 Change or Create a DataBase":

        data_base()

        cursor.commit()
        conn.close()

    if command == "💾 Download Data":

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

    if command == "📈 Calculate Indicators":

        name = input("Name : ")
        after_name = questionary.select("Adding an After Name ? : ",
                                        ["False", "True"]).ask()
        after_name = bool(after_name)

        print(erase, end="")

        function_ = questionary.select("Select a function :", choices = function_list).ask()

        function_ = function_dict[function_]


        window = input("Window : ")

        print(erase, end="")

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

    if command == "📊 Calculate Stats":
        command = questionary.select("Number of Variables : ",
                                     choices=[
                                         "1 variable",
                                         "2 variables (heatmap)"
                                     ]).ask()

    if command == "📉 Plot":

        print(erase, end="")
        print("📉 Plot")

        after_command = input("Plot command : ")

        if after_command == "stat":
            after_command = input("number of var : ")

    if command == "🗑️ Delete Column":

        print(erase, end="")
        print("🗑️ Delete Column")

        cursor.execute("""PRAGMA table_info(candles)""")
        existing_parameters = [row[1] for row in cursor.fetchall()]

        parameters = questionary.select(f"Select parameter : ", choices=existing_parameters).ask()

        yes_no = questionary.select(f"Deleting {parameters} ? For real 🤨 ?", ["No", "Yes"]).ask()

        if yes_no == "Yes":
            cursor.execute(f"""
                ALTER TABLE candles
                DROP COLUMN {parameters}""")

        else:
            print(erase, end="")

    if command == "📘 History":
        print(erase, end="")
        print("📖 History")

    if command == "❌ Exit":
        questionary.print("Leaving MARKET LAB ", style="fg:red")
        break

        

