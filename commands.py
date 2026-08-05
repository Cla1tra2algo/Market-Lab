import questionary
import data_extraction as de
import sqlite3
import applications as app


HYPERLIQUID_TIMEFRAMES = [
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
    "1M",
]

BINANCE_TIMEFRAMES = [
    "1s",
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
    "1M",
]


logo = """ 
    ╔╦╗╔═╗╦═╗╦╔═╔═╗╔╦╦═══════════╗
    ║║║╠═╣╠╦╝╠╩╗║╣  ║   ╦  ╔═╗╔╗         
    ╩ ╩╩ ╩╩╚═╩ ╩╚═╝ ╩   ║  ╠═╣╠╩╗   
  ╚═════════════════════╩═╝╩ ╩╚═╝    """


def turn_page(logo, symbol, interval, source):
    print("\033[0;1H", end="")
    print("\033[J", end="")
    print("")
    questionary.print(logo, style="fg:pink")
    print("")
    questionary.print(f"Working on {symbol} {interval} From {source}", style="fg:yellow")
    print("")

def skip(erase, pointer):
    res = questionary.select("Go back to Menu ?", choices=["Yes", "Continue"], pointer=pointer).ask()
    if res == "Yes":
        print(erase, end="")
        return res
    else:
        return res

def yes_no(question, pointer):
    rep = questionary.select(question, ["No", "Yes"], pointer=pointer).ask()
    return rep

def data_base(erase, pointer, logo):

    while True :
        symbol = input("Symbol : ")

        if symbol == "":
            print(erase, end="")
            print("")
            questionary.print("❌ You must enter a symbol (ex: BTC)", style="fg:red")
            continue
        else:
            break
            
    source = questionary.select("Source : ", choices=["Binance", "HyperLiquid"], pointer=pointer).ask()

    while True :
        if source == "Binance":
            interval = questionary.autocomplete("Timeframe : ", choices=BINANCE_TIMEFRAMES).ask()
        else:
            interval = questionary.autocomplete("Timeframe : ", choices=HYPERLIQUID_TIMEFRAMES).ask()

        if interval in BINANCE_TIMEFRAMES or interval in HYPERLIQUID_TIMEFRAMES:
            break

        else:
            print(erase, end="")
            print("")
            questionary.print("You must enter a Timeframe present in the Timeframe list", style="fg:red")
        
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
    skip(erase, pointer)
    turn_page(logo, symbol, interval, source)

    return conn, cursor, source, symbol, interval

def download_data(cursor, symbol, interval, source, timestamp, erase, conn, history):

    print(erase)
    
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

        
def calculate_indic(erase, function_dict, function_list, cursor, history, symbol, interval, pointer):

    print(erase, end="")
    print("📈 Calculate Indicators")
    print("")

    while True :
        name = input("Name : ")
        if name == "":
            print(erase, end="")
            print("")
            questionary.print("You Must Enter a Name", style="fg:red")

        else: 
            break

    after_name = questionary.select("Adding an After Name ? : ",
                                        ["No", "Yes"], pointer=pointer).ask()

    while True : 
        function_ = questionary.autocomplete("Select a function :", choices=function_list).ask()

        if function_ == "":
            print(erase, end="")
            print("")
            questionary.print("You Must Select a function", style="fg:red")

        elif function_ in function_list:
            function_ = function_dict[function_]
            break
        else: 
            print(erase, end="")
            print("")
            questionary.print("This function does not exists. Create and add it in the function dict.", style="fg:red")
    

    while True :
        while True:
            window = input("Window : ")

            try:
                window = int(window)
                break

            except ValueError:
                print(erase, end="")
                print("")
                questionary.print("You must enter an integer greater than 0", style="fg:red")

        if window <= 0:
            print(erase, end="")
            print("")
            questionary.print("You must enter an integer greater than 0", style="fg:red")

        else:
            break


    parameters = []

    cursor.execute("""PRAGMA table_info(candles)""")
    existing_parameters = [row[1] for row in cursor.fetchall()]

    for i in range(function_[1]):
        parameters.append(questionary.autocomplete(f"Select parameter {i+1} : ", choices=existing_parameters).ask())

    app.general_application(cursor, name, after_name, function_[0], window, parameters)

    history.append(f"{name} {window} {parameters} Calculated on {symbol} {interval}")


def delete_col(erase, cursor, history, symbol, interval, source, pointer):

    print(erase, end="")
    print("🗑️  Delete Column")
    print("")

    cursor.execute("""PRAGMA table_info(candles)""")
    existing_parameters = [row[1] for row in cursor.fetchall()]

    parameters = questionary.autocomplete(f"Select parameter : ", choices=existing_parameters).ask()

    if parameters == "Exit":
        print(erase, end="")
        print(erase, end="")

    else:
        rep = yes_no(f"Deleting {parameters} ? For real 🤨 ?", pointer)

        if rep == "Yes":
            cursor.execute(f"""
                ALTER TABLE candles
                DROP COLUMN {parameters}""")
            history.append(f"{parameters} Deleted In {symbol} {interval} From {source}")

            
def action_history(erase, history, pointer):

    print(erase, end="")
    print("📖 History")
    print("")

    if len(history) == 0:
        print("The Action History is empty")
        
    else:
        for i in range(len(history)):
            print(history[i])
    
def take_look(erase, history, pointer, function_dict, indicator_dict, cursor):
    print(erase, end="")
    print("👀 Take a Look")
    print("")

    look = questionary.select("What do you wanna look ?", ["Indicators Dict", "Function Dict"], pointer=pointer).ask()
    
    if look == "Indicators Dict":
        copy = questionary.select("Indicators Dict", choices=indicator_dict, pointer=pointer).ask()
        print(copy)
        nb = cursor.execute(f"""
                                SELECT COUNT(DISTINCT {copy})
                                FROM candles
                                WHERE {copy} IS NOT NULL""").fetchone()[0]

    questionary.print(f"Calculated over {nb} candles", style="fg:lightblue")

    if look == "Function Dict":
        copy = questionary.select("Function Dict", choices=function_dict, pointer=pointer).ask()
        print(copy)

    res = questionary.select("What do you wanna do ?", choices=["Go back to '👀 Take a Look'", f"Copy '{copy}' and go back to '👀 Take a Look'"]).ask()
    if res == f"Copy '{copy}' and go back to '👀 Take a Look'":
        history.append(f"{copy} Copied")
        return copy

    else:
        return None

def settings(erase, color):
    color_list = [
            "black",
            "red",
            "green",
            "yellow",
            "blue",
            "magenta",
            "cyan",
            "white",
            "brightblack",
            "brightred",
            "brightgreen",
            "brightyellow",
            "brightblue",
            "brightmagenta",
            "brightcyan",
            "brightwhite"
            ]
    
    print(erase, end="")
    print("⚙️ Settings")
    print("")

    set = questionary.select("What do you wanna set ?", choices=["Colors", "Pointer"])

    if set == "Color":
        set = questionary.select("Which color do you wanna Set ?", choices=["Color of the Logo", 
                                                                            "Color of Questions", 
                                                                            "Color of Answers", 
                                                                            "Color of Errors", 
                                                                            "Color of Active Symbol"]).ask()
        