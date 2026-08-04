import json
import sqlite3
from websocket import WebSocketApp

# ====================================================
# PARAMETRES
# ====================================================

DB_NAME = "market.db"

SYMBOL = "btcusdt"
INTERVAL = "1m"

URL = f"wss://stream.binance.com:9443/ws/{SYMBOL}@kline_{INTERVAL}"

# ====================================================
# SQLITE
# ====================================================


# ====================================================
# CALLBACKS
# ====================================================

def on_open(ws):
    print("Connexion au WebSocket établie.")


def on_close(ws, close_status_code, close_msg):
    print("Connexion fermée.")
    print(close_status_code)
    print(close_msg)


def on_error(ws, error):
    print(error)


def on_message(ws, message):

    data = json.loads(message)

    if data["e"] != "kline":
        return

    candle = data["k"]

    print(
        f"Prix : {candle['c']} | "
        f"Volume : {candle['v']} | "
        f"Close : {candle['x']}"
    )

    # Sauvegarde uniquement lorsque la bougie est terminée
    if not candle["x"]:
        return


    print("Nouvelle bougie enregistrée.\n")


# ====================================================
# LANCEMENT
# ====================================================

ws = WebSocketApp(
    URL,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    #on_close=on_close
)

ws.run_forever()