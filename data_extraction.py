from datetime import datetime
import requests 
from time import *

def extraction_binance(cursor, symbol, interval, timestamp):

    url = "https://api.binance.com/api/v3/klines"

    count = 0
    while True :
        count += 1
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": 1000,
            "startTime": timestamp
        }
        response = requests.get(url, params=params)

        data = response.json()

        if len(data) == 0 :  # Regarde si des donnés renvoyées ou si elles l'ont toute déjà été
            break          

        for candle in data :

            open_time = candle[0]
            open = float(candle[1])
            high = float(candle[2])
            low = float(candle[3])
            close = float(candle[4])
            volume = float(candle[5])
            close_time = float(candle[6])
            quote_asset_vol = float(candle[7])
            number_of_trades = float(candle[8])
            taker_buy_base_asset_volume = float(candle[9])
            taker_buy_quote_asset_volume = float(candle[10])

            features = "open_time, open, high, low, close, volume, close_time, quote_asset_vol, number_of_trades, taker_buy_base_asset_volume, taker_buy_quote_asset_volume"
            values = [open_time, 
                      open, 
                      high, 
                      low, 
                      close, 
                      volume, 
                      close_time, 
                      quote_asset_vol, 
                      number_of_trades, 
                      taker_buy_base_asset_volume, 
                      taker_buy_quote_asset_volume
                      ]


            cursor.execute(
                f"INSERT INTO candles ({features}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                values
                )

        print(f"Candles collected : {count*1000}", end="\r")
        
        last = data[-1]

        last_timestamp = last[0]
        timestamp = last_timestamp + 1

def extraction_hyperliquid(cursor, symbol, interval, timestamp):

    url = "https://api.hyperliquid.xyz/info"

    end = int(time.time()) * 1000

    payload = {
        "type" : "candleSnapshot", 
        "req" : {
            "coin": symbol,
            "interval" : interval,
            "startTime" : timestamp,
            "endTime" : end}
        }

    response = requests.post(url, json=payload)
    candles  = response.json()

    print(f"{len(candles)} collected ")

    last_candle = candles[-1]

    print(last_candle)

    open_times   = [r["t"] for r in candles]
    list_open    = [float(r["o"]) for r in candles]
    list_close   = [float(r["c"]) for r in candles]
    list_high    = [float(r["h"]) for r in candles]
    list_low     = [float(r["l"]) for r in candles]
    list_volume  = [float(r["v"]) for r in candles]
    list_nbtrade = [r["n"] for r in candles]

    print(list_nbtrade)