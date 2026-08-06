import questionary
import data_extraction as de
import sqlite3
import applications as app
from   questionary import *
from rich.console import Console
import graph_plot as gp
import event as ev



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


def turn_page(logo, symbol, interval, source, logo_color, active_color):
    console = Console()
    console.clear()
    print("")
    questionary.print(logo, style=logo_color)
    print("")
    questionary.print(f"Working on {symbol} {interval} From {source}", style=active_color)
    print("")

def skip(pointer, config):
    res = questionary.select("Go back to Menu ?", choices=["Yes", "Continue"], pointer=pointer, style=config ).ask()
    if res == "Yes":
        print(""*80, end="\r")
        return res
    else:
        return res

def yes_no(question, pointer, config):
    rep = questionary.select(question, ["No", "Yes"], pointer=pointer, style=config).ask()
    return rep

def data_base(pointer, logo, config, err_color):

    while True :
        symbol = input("Symbol : ")

        if symbol == "":
            print(""*80, end="\r")
            print("")
            questionary.print("❌ You must enter a symbol (ex: BTC)", style=err_color)
            continue
        else:
            break
            
    source = questionary.select("Source : ", choices=["Binance", "HyperLiquid"], pointer=pointer, style=config).ask()

    while True :
        if source == "Binance":
            interval = questionary.autocomplete("Timeframe : ", choices=BINANCE_TIMEFRAMES).ask()
        else:
            interval = questionary.autocomplete("Timeframe : ", choices=HYPERLIQUID_TIMEFRAMES).ask()

        if interval in BINANCE_TIMEFRAMES or interval in HYPERLIQUID_TIMEFRAMES:
            break

        else:
            print(""*80, end="\r")
            print("")
            questionary.print("❌ You must enter a Timeframe present in the Timeframe list", style=err_color)
        
    print(""*80, end="\r")
    print(""*80, end="\r")
    print(""*80, end="\r")

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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS status(
        open_time INTERGER PRIMARY KEY
        )
""")


    conn.commit()
    
    return conn, cursor, source, symbol, interval

def download_data(cursor, symbol, interval, source, timestamp, conn, history):

    print(""*80, end="\r")
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
   
def calculate_indic(function_dict, function_list, cursor, conn, history, symbol, interval, pointer, config, err_color):

    print(""*80, end="\r")
    print("📈 Calculate Indicators")
    print("")

    while True :
        name = input("Name : ")
        if name == "":
            print(""*80, end="\r")
            print("")
            questionary.print("You Must Enter a Name", style="fg:red")

        else: 
            break

    after_name = questionary.select("Adding an After Name ? : ",
                                        ["No", "Yes"], pointer=pointer, style=config).ask()

    while True : 
        function_ = questionary.autocomplete("Select a function :", choices=function_list).ask()

        if function_ == "":
            print(""*80, end="\r")
            print("")
            questionary.print("❌ You Must Select a function", style=err_color)

        elif function_ in function_list:
            function_ = function_dict[function_]
            break
        else: 
            print(""*80, end="\r")
            print("")
            questionary.print("❌ This function does not exists. Create and add it in the function dict.", style=err_color)
    

    while True :
        while True:
            window = input("Window : ")

            try:
                window = int(window)
                break

            except ValueError:
                print(""*80, end="\r")
                print("")
                questionary.print("❌ You must enter an integer greater than 0", style=err_color)

        if window <= 0:
            print(""*80, end="\r")
            print("")
            questionary.print("❌ You must enter an integer greater than 0", style=err_color)

        else:
            break


    parameters = []

    cursor.execute("""PRAGMA table_info(candles)""")
    existing_parameters = [row[1] for row in cursor.fetchall()]


    if type(function_[-1]) is list:
        print("")
        questionary.print(f"Recomended parameters : {function_[-1]}", style="fg:blue")

    for i in range(function_[1]):

        parameters.append(questionary.autocomplete(f"Select parameter {i+1} : ", choices=existing_parameters).ask())

    app.general_application(cursor, name, after_name, function_[0], window, parameters)
    conn.commit()
    history.append(f"{name} {window} {parameters} Calculated on {symbol} {interval}")


def calculate_event(event_dict, pointer, cursor):

    print(""*80, end="\r")
    print("🎉 Calculate Events")
    print("")

    event_list = list(event_dict.keys())
    questionary.print(f"{len(event_list)}, {type(event_list[0])}")

    choice = questionary.select("Select an event :", choices=event_list, pointer=pointer).ask()

    event = event_dict[choice]
    event_function = event[0]
    questionary.print(f"{type(event_function)}")

    nb_para = event[1]

    cursor.execute("""PRAGMA table_info(candles)""")
    existing_parameters = [row[1] for row in cursor.fetchall()]
    data = []

    for i in range(nb_para):
        data.append(questionary.autocomplete(f"Select Parameter {i+1} : ", choices=existing_parameters).ask())

    event_function(cursor, data)
    questionary.print("Event calculated")



def plot_indic(cursor, err_color, pointer):

    print(""*80, end="\r")
    print("Plot")
    print(" ")

    values = []
    cursor.execute("""PRAGMA table_info(candles)""")
    existing_values = [row[1] for row in cursor.fetchall()]
    #existing_values.remove("open_time")

    while True:
        choice = questionary.autocomplete("What Indicator do you want to plot?", 
                                          choices=existing_values,
                                          ).ask()
        values.append(choice)
        if not choice in existing_values:
            questionary.print("You must enter an Indicator present in the Indicator list", 
                              style=err_color)
        else:
            rep = questionary.select("Do you wanna plot another Indicator ?", 
                                     ["Yes", "No"],
                                     pointer=pointer).ask()
            if rep == "No":
                questionary.print(f"Indicators to plot : {values}", style="lightblue")
                break

   
    rep = questionary.select("Do you wanna plot a Status ?", choices=["Yes", "No"], pointer=pointer).ask()
    if rep == "Yes":
        cursor.execute("""PRAGMA table_info(status)""")
        existing_status = [r[1] for r in cursor.fetchall()]

        existing_status.remove("open_time")

        choice = questionary.autocomplete("What Status do you wanna plot ?", choices=existing_status).ask()
        status = choice

    else:
        status = None

    
    questionary.print("Ploting ...", style="fg:lightblue")

    gp.plot(cursor, values, status)


def delete_col(cursor, history, symbol, interval, source, pointer, config):

    print(""*80, end="\r")
    print("🗑️  Delete Column")
    print("")

    cursor.execute("""PRAGMA table_info(candles)""")
    existing_parameters = [row[1] for row in cursor.fetchall()]

    parameters = questionary.autocomplete(f"Select parameter : ", choices=existing_parameters).ask()

    if parameters == "Exit":
        print(""*80, end="\r")
        print(""*80, end="\r")

    else:
        rep = yes_no(f"Deleting {parameters} ? For real 🤨 ?", pointer, config)

        if rep == "Yes":
            cursor.execute(f"""
                ALTER TABLE candles
                DROP COLUMN {parameters}""")
            history.append(f"{parameters} Deleted In {symbol} {interval} From {source}")
         
def action_history(history):

    print(""*80, end="\r")
    print("📖 History")
    print("")

    if len(history) == 0:
        print("The Action History is empty")

        
    else:
        for i in range(len(history)):
            print(history[i])

def take_look(history, pointer, function_dict, cursor, config):
    print(""*80, end="\r")
    print("👀 Take a Look")
    print("")

    cursor.execute("""PRAGMA table_info(candles)""")
    indicator_dict = [row[1] for row in cursor.fetchall()]
    

    look = questionary.select("What do you wanna look ?", ["Indicators Dict", "Function Dict"], pointer=pointer, style=config).ask()
    
    if look == "Indicators Dict":
        copy = questionary.select("Indicators Dict", choices=indicator_dict, pointer=pointer, style=config).ask()
        print(copy)
        nb = cursor.execute(f"""
                                SELECT COUNT(DISTINCT {copy})
                                FROM candles
                                WHERE {copy} IS NOT NULL""").fetchone()[0]

        rows = cursor.execute(f"""
                                SELECT {copy}
                                FROM candles
                                ORDER BY open_time
            """).fetchall()

        last_values = [r[0] for r in rows][-8 : -1]

        questionary.print(f"Calculated over {nb} candles", style="fg:blue")
        questionary.print("Last Values : ", style="fg:blue")

        for i in range(len(last_values)):
            questionary.print(f"{last_values[i]}", style="fg:red")


    if look == "Function Dict":
        copy = questionary.select("Function Dict", choices=function_dict, pointer=pointer).ask()
        print(copy)

    res = questionary.select("What do you wanna do ?", 
                             choices=["Go back to '👀 Take a Look'", f"Copy '{copy}' and go back to '👀 Take a Look'"], 
                             pointer=pointer).ask()
    if res == f"Copy '{copy}' and go back to '👀 Take a Look'":
        history.append(f"{copy} Copied")
        return copy

    else:
        return None

def settings(color):
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
    
    print(""*80, end="\r")
    print("⚙️ Settings")
    print("")

    set = questionary.select("What do you wanna set ?", choices=["Colors", "Pointer"])

    if set == "Color":
        set = questionary.select("Which color do you wanna Set ?", choices=["Color of the Logo", 
                                                                            "Color of Questions", 
                                                                            "Color of Answers", 
                                                                            "Color of Errors", 
                                                                            "Color of Active Symbol"]).ask()


