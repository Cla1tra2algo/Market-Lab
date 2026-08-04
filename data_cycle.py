from datetime import datetime
import data_extraction as extraction
import requests
import sqlite3
import applications as app
import math_formula as mf
import stat_making as sm
import event 


# Connection a l'API binance et récupération des données

start = datetime(2017, 8, 17)             # limites temporelles de l'exctraction des donnés 
timestamp = int(start.timestamp() * 1000)

symbol = input("Symbol : ") + "USDT"
symbol = symbol.upper()
interval = input("Interval : ")

firt_timestamp = 1502942400000
gap_timestamp = 3600 * 1000
window = 100
power = 1.5
prominence = 500

url = "https://api.binance.com/api/v3/klines"

# Création de la base de donnés : 

conn = sqlite3.connect(f"data_{symbol}_{interval}")
cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS candles(

    open_time INTEGER PRIMARY KEY,

    open REAL NOT NULL,

    high REAL NOT NULL,
    low REAL NOT NULL,

    close REAL NOT NULL,

    volume REAL NOT NULL, 

    close_time REAL NOT NULL,
    
    vwema,
    vwema_savgol,

    quote_asset_vol REAL NOT NULL, 

    number_of_trades REAL NOT NULL,

    taker_buy_base_asset_volume REAL NOT NULL,
    taker_buy_quote_asset_volume REAL NOT NULL,

    statut REAL

)
""")

cursor.execute("""
SELECT COUNT(*)
FROM candles
WHERE open_time IS NOT NULL
""")

nb = cursor.fetchone()[0]

if nb != 0 :

    last_timestamp = cursor.execute("""
            SELECT MAX(open_time)
            FROM candles
            """).fetchone()[0] + 1

else:
    last_timestamp = firt_timestamp

print("Extraction")
extraction.extraction(url, cursor, symbol, interval, last_timestamp)

app.general_application(cursor, "vwema", mf.vwema, window, ["volume", "close"], last_timestamp)


print("VWEMA computed")

app.filter_application(cursor, "vwema_volume_close_100")

print("Peaks Detection")
event.peaks_detection(cursor, prominence)
conn.commit()

print("\r" + " " * 80, end="\r")
print("Peaks Detection : Done !", end="\r")

print("")

sma_data =  ["sma", mf.sma, ["close"],  [f"sma_close_", "close", "std_dev_close_"]]
ema_data =  ["ema", mf.ema, ["close"],  [f"ema_close_", "close", "std_dev_close_"]]
vsma_data = ["sma", mf.sma, ["volume"], [f"sma_volume_", "volume", "std_dev_volume_"]]
wma_data =  ["wma", mf.wma, ["close"],  [f"wma_close_", "close", "std_dev_close_"]]
vwma_data =  ["vwma", mf.vwma, ["close", "volume"],  [f"vwma_close_", "close", "std_dev_close_"]]


data_to_compute = [wma_data, sma_data, ema_data, vsma_data]


for i in range(len(data_to_compute)):

    for n in range(25, 201, 25):

        print(f"----{n}----                       ", end="\r")

        app.general_application(cursor, data_to_compute[i][0], data_to_compute[i][1], n, [data_to_compute[i][2][0]], last_timestamp)
        app.general_application(cursor, "relative", mf.relative, 1, [data_to_compute[i][3][1], data_to_compute[i][3][0]+str(n)], last_timestamp)
        app.general_application(cursor, "relative_gap", mf.relative_gap, 1, [data_to_compute[i][3][1], data_to_compute[i][3][0]+str(n)], last_timestamp)
        app.general_application(cursor, "ampl", mf.amplitude, 1, [data_to_compute[i][3][0]+str(n), data_to_compute[i][3][1]], last_timestamp)
        app.general_application(cursor, "std_dev", mf.std_dev, n, data_to_compute[i][2], last_timestamp)
        conn.commit()
        app.general_application(cursor, "zscore", mf.zscore, 1, [data_to_compute[i][3][0]+str(n), data_to_compute[i][3][1], data_to_compute[i][3][2]+str(n)], last_timestamp)
        conn.commit()

    print(f"{data_to_compute[i][3][0]} Computed ! " + " "*80)

    
app.general_application(cursor, "close_position", mf.close_position, 1, ["close", "high", "low"], last_timestamp)
app.general_application(cursor, "atr", mf.atr, 14, ["high", "low", "open"], last_timestamp)

returns = [["open", "close"], ["high", "low"]]

for i in range(4, 4*24 + 1, 4):
    app.general_application(cursor, "return", mf.return_, i, ["open", "open"], last_timestamp)
    app.general_application(cursor, "log_return", mf.log_return, i, ["open", "open"], last_timestamp)

for i in range(len(returns)):
    app.general_application(cursor, "return", mf.return_, 1, returns[i], last_timestamp)
    app.general_application(cursor, "log_return", mf.log_return, 1, returns[i], last_timestamp)


for i in range(25, 201, 25):
    app.general_application(cursor, "bol_band_up", mf.bol_band_up, i, [f"sma_close_{i}", f"std_dev_close_{i}"], last_timestamp)
    app.general_application(cursor, "bol_band_down", mf.bol_band_down, i, [f"sma_close_{i}", f"std_dev_close_{i}" ], last_timestamp)
    app.general_application(cursor, "ampl", mf.amplitude, 1, [f"sma_close_{i}", f"bol_band_up_sma_close_{i}_{i}", last_timestamp])

conn.commit()

cursor.execute("""PRAGMA table_info(candles)""")

columns = [c[1] for c in cursor.fetchall()]

print(f"{len(columns)} Columns Computed !")

conn.close()

