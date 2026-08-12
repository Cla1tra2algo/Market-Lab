import questionary
import data_extraction as de
import sqlite3
import applications as app
from   questionary import *
from rich.console import Console
import graph_plot as gp
import event as ev
import stat_making as sm
from pathlib import Path
import os
import re
import shlex
import subprocess

from importlib.util import module_from_spec, spec_from_file_location
from inspect import signature


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



CUSTOM_FILE = Path(__file__).resolve().parent / "custom_indicators.py"

CUSTOM_TEMPLATE = '''"""Personal Market Lab indicators and events.

Only load code that you wrote or trust: this file is executed by Market Lab.
"""


def median_price(data):
    """Return the midpoint of the latest high and low values."""
    high = data[0]
    low = data[1]
    return (high[-1] + low[-1]) / 2


def close_above_open(cursor, columns):
    """Create a status equal to 1 when close is above open, otherwise 0."""
    close_column, open_column = columns
    rows = cursor.execute(
        f"SELECT open_time, \\"{close_column}\\", \\"{open_column}\\" FROM candles ORDER BY open_time"
    ).fetchall()

    status_columns = {row[1] for row in cursor.execute("PRAGMA table_info(status)")}
    if "close_above_open" not in status_columns:
        cursor.execute("ALTER TABLE status ADD COLUMN close_above_open")
    cursor.executemany(
        "UPDATE status SET close_above_open = ? WHERE open_time = ?",
        [(int(close > open_), open_time) if close is not None and open_ is not None else (0, open_time)
         for open_time, close, open_ in rows],
    )
    cursor.connection.commit()


indicator_dict = {
    "median_price": (median_price, 2, ["high", "low"]),
}

event_dict = {
    "close_above_open": (close_above_open, 2, ["close", "open"]),
}
'''

def _open_in_editor(path, err_color):
    editor = os.environ.get("EDITOR")
    if not editor:
        questionary.print(f"Open this file in your code editor: {path}", style="fg:blue")
        return

    try:
        subprocess.Popen(shlex.split(editor) + [str(path)])
    except (OSError, ValueError) as error:
        questionary.print(f"❌ Unable to open the editor: {error}", style=err_color)
        questionary.print(f"Open this file manually: {path}", style="fg:blue")


def create_custom_indicators_file(err_color):

    if CUSTOM_FILE.exists():
        questionary.print(f"Custom indicator file already exists: {CUSTOM_FILE}", style="fg:yellow")
        _open_in_editor(CUSTOM_FILE, err_color)
        return False

    CUSTOM_FILE.write_text(CUSTOM_TEMPLATE, encoding="utf-8")

    questionary.print(f"Custom indicator file created: {CUSTOM_FILE}",
                      style="fg:green")
    _open_in_editor(CUSTOM_FILE, err_color)
    return True


def _validate_custom_registry(registry, registry_name, expected_function_parameters):
    if not isinstance(registry, dict):
        raise ValueError(f"{registry_name} must be a dictionary.")

    for name, definition in registry.items():
        if not _identifier_is_valid(name):
            raise ValueError(f"Invalid {registry_name} name: {name!r}.")
        if not isinstance(definition, tuple) or len(definition) != 3:
            raise ValueError(f"{name!r} must be a tuple: (function, parameter_count, recommendations).")
        function, parameter_count, recommendations = definition
        if not callable(function) or not isinstance(parameter_count, int) or parameter_count < 1:
            raise ValueError(f"Invalid definition for {name!r}.")
        if not isinstance(recommendations, list) or not all(isinstance(item, str) for item in recommendations):
            raise ValueError(f"Recommendations for {name!r} must be a list of strings.")
        if len(recommendations) != parameter_count:
            raise ValueError(f"{name!r} expects {parameter_count} recommendations.")
        try:
            signature(function).bind(*([None] * expected_function_parameters))
        except TypeError as error:
            raise ValueError(
                f"{name!r} must accept {expected_function_parameters} argument(s)."
            ) from error

def load_custom_indicators_and_events(err_color):
    if not CUSTOM_FILE.exists():
        questionary.print("No custom_indicators.py file found.",
                          style="fg:yellow")
        return None

    try:
        spec = spec_from_file_location("custom_indicators", CUSTOM_FILE)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        custom_indicator_dict = getattr(module, "indicator_dict", {})
        custom_event_dict = getattr(module, "event_dict", {})
        _validate_custom_registry(custom_indicator_dict, "indicator_dict", 1)
        _validate_custom_registry(custom_event_dict, "event_dict", 2)
        return custom_indicator_dict, custom_event_dict
    

    except Exception as error:
        questionary.print(f"❌ Unable to load custom indicators and events: {error}", style=err_color)

        return None



def checking_file(chemin, err_color):

    path = Path(chemin).expanduser()

    if not path.exists():
        print(""*80, end="\r")
        print(""*80, end="\r")
        questionary.print("❌ This file does not exist.", style=err_color)
        return False

    if not path.is_file():
        print(""*80, end="\r")
        print(""*80, end="\r")
        questionary.print("❌ This path does not lead to a file.", style=err_color)
        return False

    if path.suffix.lower() != ".db":
        print(""*80, end="\r")
        print(""*80, end="\r")
        questionary.print("❌ The file must have a .db extension.", style=err_color)
        return False

    return True

def turn_page(logo, symbol, interval, logo_color, active_color):

    console = Console()
    console.clear()
    print("")
    questionary.print(logo, style=logo_color)
    print("")
    questionary.print(f"Working on {symbol} — {interval}", style=active_color)
    print("")

def skip(pointer, config):
    res = questionary.select("Return to the main menu?", choices=["Yes", "Continue"], pointer=pointer, style=config ).ask()
    if res == "Yes":
        print(""*80, end="\r")
        return res
    else:
        return res

def yes_no(question, pointer, config):
    rep = questionary.select(question, ["No", "Yes"], pointer=pointer, style=config).ask()
    return rep

def _database_schema_is_valid(path):
    try:
        with sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True) as connection:
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            return {"candles", "status"}.issubset(tables)
    except sqlite3.Error:
        return False

def _identifier_is_valid(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value) is not None

def _quote_identifier(value):
    if not _identifier_is_valid(value):
        raise ValueError("Invalid database identifier.")
    return f'"{value}"'

def _database_details(path):
    stem = Path(path).stem
    parts = stem.split("_")
    if len(parts) < 3 or parts[0] != "data" or parts[2] not in BINANCE_TIMEFRAMES:
        raise ValueError("The database name must follow data_SYMBOL_TIMEFRAME.db.")
    return parts[1], parts[2]

def data_base(pointer, logo, config, err_color):

    rep = questionary.select("Would you like to create or open a database?", choices=["Create a database", "Open a database"], pointer=pointer, style=config).ask()

    if rep == "Open a database":

        file = questionary.path("Database file (.db):", validate=lambda chemin: checking_file(chemin, err_color)).ask()
        if not _database_schema_is_valid(file):
            questionary.print("❌ This is not a Market Lab database.", style=err_color)
            return data_base(pointer, logo, config, err_color)

        conn = sqlite3.connect(file)
        cursor = conn.cursor()
        try:
            symbol, interval = _database_details(file)
        except ValueError as error:
            conn.close()
            questionary.print(f"❌ {error}", style=err_color)
            return data_base(pointer, logo, config, err_color)

        return conn, cursor, symbol, interval
        

    if rep == "Create a database":

        while True :
            symbol = input("Symbol (e.g. BTC or BTCUSDT): ").strip().upper()

            if symbol == "":
                print(""*80, end="\r")
                print("")
                questionary.print("❌ Enter a symbol, for example BTC.", style=err_color)
                continue
            else:
                break
                
        
        while True :
            
            interval = questionary.autocomplete("Timeframe:", choices=BINANCE_TIMEFRAMES, style=config).ask()
            
            if interval in BINANCE_TIMEFRAMES :
                break

            else:
                print(""*80, end="\r")
                print("")
                questionary.print("❌ Select a timeframe from the list.", style=err_color)
            
        print(""*80, end="\r")
        print(""*80, end="\r")
        print(""*80, end="\r")

        if not re.fullmatch(r"[A-Z0-9]+", symbol):
            questionary.print("❌ The symbol may contain only letters and numbers.", style=err_color)
            return data_base(pointer, logo, config, err_color)
        if not symbol.endswith("USDT"):
            symbol += "USDT"

        conn = sqlite3.connect(f"data_{symbol}_{interval}.db")
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
            open_time INTEGER PRIMARY KEY
            )
    """)


        conn.commit()
        
        return conn, cursor, symbol, interval

def download_data(cursor, symbol, interval, timestamp, conn, history):

    print(""*80, end="\r")
    print("💾 Download Data")
    
    
    de.extraction_binance(cursor, symbol, interval, timestamp)
    conn.commit()
    
    print("Data downloaded.")
    
    history.append(f"{symbol} {interval} Downloaded ")
   
def calculate_indic(indicator_dict, indicator_list, cursor, conn, history, symbol, interval, pointer, config, err_color):

    print(""*80, end="\r")
    print("📈 Calculate Indicators")
    print("")

    while True :
        name = input("Indicator name: ").strip()
        if not _identifier_is_valid(name):
            print(""*80, end="\r")
            print("")
            questionary.print("❌ Use a name starting with a letter or underscore; use only letters, numbers, and underscores.", style=err_color)

        else: 
            break

    after_name = questionary.select("Append selected parameters to the indicator name?",
                                        ["No", "Yes"], pointer=pointer, style=config).ask()

    while True : 
        indicator_ = questionary.autocomplete("Select an indicator:", choices=indicator_list, style=config).ask()

        if indicator_ == "":
            print(""*80, end="\r")
            print("")
            questionary.print("❌ Select a function.", style=err_color)

        elif indicator_ in indicator_list:
            indicator_ = indicator_dict[indicator_]
            break
        else: 
            print(""*80, end="\r")
            print("")
            questionary.print("❌ This function does not exist.", style=err_color)
    

    while True :
        while True:
            window = input("Window size: ")

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


    if type(indicator_[-1]) is list:
        print("")
        questionary.print(f"Recommended parameters: {indicator_[-1]}", style="fg:blue")

    for i in range(indicator_[1]):

        parameter = questionary.autocomplete(f"Select parameter {i + 1}:", choices=existing_parameters, style=config).ask()
        if parameter not in existing_parameters:
            questionary.print("❌ Select a parameter from the list.", style=err_color)
            return
        parameters.append(parameter)

    app.general_application(cursor, name, after_name, indicator_[0], window, parameters)
    conn.commit()
    history.append(f"{name} {window} {parameters} Calculated on {symbol} {interval}")

def manage_custom_indicators_and_events(pointer, err_color, custom_indicator_dict, custom_event_dict):
    rep = questionary.select("Actions : ", ["Create custom_indicators.py", 
                                            "List available custom indicators and events",
                                            "Reload custom indicators",
                                            "Back to main menu"], pointer=pointer).ask()

    if rep == "Create custom_indicators.py":
        create_custom_indicators_file(err_color)
        return None

    if rep == "List available custom indicators and events":
        indicators_list = list(custom_indicator_dict.keys())
        event_list = list(custom_event_dict.keys())

        questionary.print(f"Indicators dictionary: {indicators_list}", style="fg:lightblue")
        questionary.print(f"Events dictionary: {event_list}", style="fg:lightblue")

    if rep == "Reload custom indicators":
        registries = load_custom_indicators_and_events(err_color)
        if registries is None:
            return None
        custom_indicator_dict, custom_event_dict = registries
        questionary.print(f"{len(custom_indicator_dict)} custom indicator(s) loaded; {len(custom_event_dict)} custom event(s) loaded.", style="fg:green")
        return custom_indicator_dict, custom_event_dict

    return None

    

def calculate_stats(cursor, pointer):

    print(""*80, end="\r")
    print("📊 Calculate Statistics")
    print("")

    cursor.execute("""PRAGMA table_info(candles)""")
    existing_parameters = [row[1] for row in cursor.fetchall()]
    existing_parameters.remove("open_time")

    cursor.execute("""PRAGMA table_info(status)""")
    existing_status = [row[1] for row in cursor.fetchall()]
    existing_status.remove("open_time")
    rep = questionary.select("Choose a chart type:", choices=["Classic chart", "Heat map"], pointer=pointer).ask()

    if not existing_status:
        questionary.print("❌ Create an event before calculating statistics.", style="fg:red")
        return
    try:
        x_axis = int(input("Number of quantile intervals: "))
        if x_axis < 1:
            raise ValueError
    except ValueError:
        questionary.print("❌ Enter a positive integer.", style="fg:red")
        return
    parameter = questionary.autocomplete("Select a parameter:", choices=existing_parameters).ask()
    status    = questionary.autocomplete("Select a status:", choices=existing_status).ask()
    if parameter not in existing_parameters or status not in existing_status:
        questionary.print("❌ Select values from the lists.", style="fg:red")
        return

    if rep == "Classic chart":
        sm.stat_onevar(cursor, status, parameter, int(x_axis))

    else:
        second_parameter = questionary.autocomplete("Select a second parameter:", choices=existing_parameters).ask()
        if second_parameter not in existing_parameters:
            questionary.print("❌ Select a parameter from the list.", style="fg:red")
            return
        sm.stat_twovar(cursor, status, parameter, second_parameter, int(x_axis))
        
def calculate_event(event_dict, pointer, cursor):

    print(""*80, end="\r")
    print("🎉 Calculate Events")
    print("")

    event_list = list(event_dict.keys())
    choice = questionary.select("Select an event:", choices=event_list, pointer=pointer).ask()

    event = event_dict[choice]
    event_function = event[0]

    nb_para = event[1]

    cursor.execute("""PRAGMA table_info(candles)""")
    existing_parameters = [row[1] for row in cursor.fetchall()]
    data = []

    questionary.print(f"Recommended Parameters : {event[-1]}", style="fg:lightblue")

    for i in range(nb_para):
        if choice == "highest_lowest" and i == 1:
            try:
                value = int(input("Window size: "))
                if value < 1:
                    raise ValueError
            except ValueError:
                questionary.print("❌ Enter a positive integer.", style="fg:red")
                return
        else:
            value = questionary.autocomplete(f"Select parameter {i + 1}:", choices=existing_parameters).ask()
            if value not in existing_parameters:
                questionary.print("❌ Select a parameter from the list.", style="fg:red")
                return
        data.append(value)

    event_function(cursor, data)
    questionary.print("Event calculated.")

def plot_indic(cursor, err_color, pointer):

    print(""*80, end="\r")
    print("✏️  Plot")
    print(" ")

    values = []
    cursor.execute("""PRAGMA table_info(candles)""")
    existing_values = [row[1] for row in cursor.fetchall()]
    existing_values.remove("open_time")

    while True:
        choice = questionary.autocomplete("Select an indicator to plot:", 
                                          choices=existing_values,
                                          ).ask()
        if not choice in existing_values:
            questionary.print("❌ Select an indicator from the list.", 
                              style=err_color)
        else:
            values.append(choice)
            rep = questionary.select("Plot another indicator?", 
                                     ["Yes", "No"],
                                     pointer=pointer).ask()
            if rep == "No":
                questionary.print(f"Indicators to plot: {values}", style="fg:lightblue")
                break

   
    rep = questionary.select("Plot a status?", choices=["Yes", "No"], pointer=pointer).ask()
    if rep == "Yes":
        cursor.execute("""PRAGMA table_info(status)""")
        existing_status = [r[1] for r in cursor.fetchall()]

        existing_status.remove("open_time")

        if not existing_status:
            questionary.print("No status is available yet.", style=err_color)
            status = None
        else:
            choice = questionary.autocomplete("Select a status:", choices=existing_status).ask()
            if choice not in existing_status:
                questionary.print("❌ Select a status from the list.", style=err_color)
                return
            status = choice

    else:
        status = None

    
    questionary.print("Plotting…", style="fg:lightblue")

    gp.plot(cursor, values, status)

def delete_col(cursor, history, symbol, interval, pointer, config):

    print(""*80, end="\r")
    print("🗑️  Delete a Column")
    print("")


    target = questionary.select("What would you like to delete?", ["An indicator", "A status"], pointer=pointer).ask()


    if target == "An indicator":

        cursor.execute("""PRAGMA table_info(candles)""")
        existing_parameters = [row[1] for row in cursor.fetchall()]
        existing_parameters.remove("open_time")

        if not existing_parameters:
            questionary.print("No indicator can be deleted.", style="fg:yellow")
            return
        parameters = questionary.autocomplete("Select an indicator:", choices=existing_parameters).ask()

        if parameters in existing_parameters:
            rep = yes_no(f'Permanently delete "{parameters}"?', pointer, config)

            if rep == "Yes":
                cursor.execute(f"""
                    ALTER TABLE candles
                    DROP COLUMN {_quote_identifier(parameters)}""")
                history.append(f"{parameters} deleted in {symbol} {interval}.")


    if target == "A status":

        cursor.execute("""PRAGMA table_info(status)""")
        existing_parameters = [row[1] for row in cursor.fetchall()]
        existing_parameters.remove("open_time")
            
        if not existing_parameters:
            questionary.print("No status can be deleted.", style="fg:yellow")
            return
        parameters = questionary.autocomplete("Select a status:", choices=existing_parameters).ask()

        if parameters in existing_parameters:
            rep = yes_no(f'Permanently delete "{parameters}"?', pointer, config)

            if rep == "Yes":
                cursor.execute(f"""
                    ALTER TABLE status
                    DROP COLUMN {_quote_identifier(parameters)}""")
                history.append(f"{parameters} deleted in {symbol} {interval}.")
         
def action_history(history):

    print(""*80, end="\r")
    print("📖 History")
    print("")

    if len(history) == 0:
        print("The action history is empty.")

        
    else:
        for i in range(len(history)):
            print(history[i])

def take_look(history, pointer, indicator_dict, cursor, config):
    print(""*80, end="\r")
    print("👀 Inspect Data")
    print("")

    cursor.execute("""PRAGMA table_info(candles)""")
    indicator_dict = [row[1] for row in cursor.fetchall()]
    

    look = questionary.select("What would you like to inspect?", ["Indicators", "Status", "Available functions"], pointer=pointer, style=config).ask()
    
    if look == "Indicators":
        copy = questionary.select("Indicators:", choices=indicator_dict, pointer=pointer, style=config).ask()
        nb = cursor.execute(f"""
                                SELECT COUNT(DISTINCT {copy})
                                FROM candles
                                WHERE {copy} IS NOT NULL""").fetchone()[0]

        rows = cursor.execute(f"""
                                SELECT {copy}
                                FROM candles
                                ORDER BY open_time
            """).fetchall()

        last_values = [r[0] for r in rows][-8:]

        questionary.print(f"Calculated over {nb} candles", style="fg:blue")
        questionary.print("Last values:", style="fg:blue")

        for i in range(len(last_values)):
            questionary.print(f"{last_values[i]}", style="fg:red")


    if look == "Available functions":
        copy = questionary.select("Available indicators:", choices=indicator_dict, pointer=pointer).ask()


    if look == "Status":

        cursor.execute("PRAGMA table_info(status)")
        status_dict = indicator_dict = [row[1] for row in cursor.fetchall()]

        status_dict.remove("open_time")

        copy = questionary.select("Status:", choices=status_dict, pointer=pointer, style=config).ask()
        nb = cursor.execute(f"""
                            SELECT COUNT(DISTINCT {copy})
                            FROM status
                            WHERE {copy} IS NOT NULL""").fetchone()[0]
        
        rows = cursor.execute(f"""
                            SELECT {copy}
                            FROM status
                            ORDER BY open_time
                    """).fetchall()
        
        last_values = [r[0] for r in rows][-8:]
        
        questionary.print(f"Calculated over {nb} candles", style="fg:blue")
        questionary.print("Last values:", style="fg:blue")
        


    history.append(f"Inspected {copy}.")
    return None

def settings(pointer, logo_color, questions_color, answers_color, err_color, active_color):
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

    setting = questionary.select("What would you like to change?", choices=["Colors", "Pointer"]).ask()

    if setting == "Pointer":
        pointer = questionary.select("Choose a pointer:", choices=["▶︎", "❯", "➜", "→"]).ask()
    else:
        labels = {
            "Logo": "logo_color",
            "Questions": "questions_color",
            "Answers": "answers_color",
            "Errors": "err_color",
            "Active database": "active_color",
        }
        label = questionary.select("Choose an element:", choices=list(labels)).ask()
        color = questionary.select("Choose a color:", choices=color_list).ask()
        color = f"fg:{color}"
        if labels[label] == "logo_color":
            logo_color = color
        elif labels[label] == "questions_color":
            questions_color = color
        elif labels[label] == "answers_color":
            answers_color = color
        elif labels[label] == "err_color":
            err_color = color
        else:
            active_color = color

    return pointer, logo_color, questions_color, answers_color, err_color, active_color
