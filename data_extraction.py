import time

import requests

def extraction_binance(cursor, symbol, interval, start_timestamp, end_timestamp):

    url = "https://api.binance.com/api/v3/klines"

    start_timestamp = int(start_timestamp)

    count = 0
    while True :

        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": 1000,
            "startTime": start_timestamp,
            "endTime": end_timestamp
        }
        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            count += len(data)

        except (requests.RequestException, ValueError) as error:
            raise RuntimeError(f"Unable to download Binance data: {error}") from error

        if isinstance(data, dict):
            raise RuntimeError(f"Binance API error: {data.get('msg', data)}")

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
                f"INSERT OR IGNORE INTO candles ({features}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                values
                )

            cursor.execute(
                "INSERT OR IGNORE INTO status (open_time) VALUES (?)", (open_time,))

        print(f"Candles collected : {count}", end="\r")
        
        last = data[-1]

        last_timestamp = last[0]
        start_timestamp = last_timestamp + 1

def extraction_hyperliquid(cursor, symbol, interval, timestamp):
    """Download Hyperliquid candles, whose API returns dictionaries."""
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": symbol,
            "interval": interval,
            "startTime": timestamp,
            "endTime": int(time.time() * 1000),
        },
    }
    try:
        response = requests.post("https://api.hyperliquid.xyz/info", json=payload, timeout=20)
        response.raise_for_status()
        candles = response.json()
    except (requests.RequestException, ValueError) as error:
        raise RuntimeError(f"Unable to download Hyperliquid data: {error}") from error

    if not isinstance(candles, list):
        raise RuntimeError(f"Hyperliquid API error: {candles}")

    features = (
        "open_time, open, high, low, close, volume, close_time, quote_asset_vol, "
        "number_of_trades, taker_buy_base_asset_volume, taker_buy_quote_asset_volume"
    )
    for candle in candles:
        values = (
            candle["t"], float(candle["o"]), float(candle["h"]), float(candle["l"]),
            float(candle["c"]), float(candle["v"]), candle["T"], None,
            candle.get("n"), None, None,
        )
        cursor.execute(
            f"INSERT OR IGNORE INTO candles ({features}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            values,
        )
        cursor.execute("INSERT OR IGNORE INTO status (open_time) VALUES (?)", (candle["t"],))

    print(f"Candles collected: {len(candles)}")
    
