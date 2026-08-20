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
from collections.abc import Mapping

from importlib.util import module_from_spec, spec_from_file_location
from inspect import signature

from database_validation import *

from datetime import *

DISPLAY_WIDTH = 100


def clear_display_line():
    print(f"\r{' ' * DISPLAY_WIDTH}", end="\r")


def display_blank_lines(count=1):
    for _ in range(count):
        print("")


def display_title(title, style="fg:blue"):
    clear_display_line()
    display_blank_lines(1)
    questionary.print(title, style=style)
    display_blank_lines(1)


def display_heading(title, style=None):
    heading_style = style or "fg:blue"
    display_title(title, heading_style)


def display_info(message, style="fg:lightblue"):
    questionary.print(message, style=style)


def display_success(message, style="fg:green"):
    questionary.print(message, style=style)


def display_warning(message, style="fg:yellow"):
    questionary.print(message, style=style)


def display_error(message, style="fg:red"):
    clear_display_line()
    questionary.print(f"❌ {message}", style=style)


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



class FunctionData():

    def __init__(self, f):
        self.func          = f[0]
        self.nb_parameters = f[1]
        self.recommended_parameters = f[2]
        self.func_type     = f[3]


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

tables_list = ("candles", "status", "indicators_metadata")

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

def create_custom_indicators_file(err_color, pointer, config):

    if CUSTOM_FILE.exists():
        questionary.print(f"Custom indicator file already exists: {CUSTOM_FILE}", style="fg:yellow")
        _open_in_editor(CUSTOM_FILE, err_color)
        return False

    CUSTOM_FILE.write_text(CUSTOM_TEMPLATE, encoding="utf-8")

    questionary.print(f"Custom indicator file created: {CUSTOM_FILE}",
                      style="fg:green")
    _open_in_editor(CUSTOM_FILE, err_color)

    questionary.select("Press Enter to continue", choices=["Ok"], pointer=pointer, style=config).ask()

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

def merge_registries(base_registry, custom_registry, registry_name):
    """Merge built-in and custom registries after validating their structure."""
    if not isinstance(base_registry, Mapping) or not isinstance(custom_registry, Mapping):
        raise ValueError(f"{registry_name} must be a dictionary.")
    return {**base_registry, **custom_registry}

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

        questionary.print(f"Loaded {custom_indicator_dict.keys()} (custom indicator(s)) and {custom_event_dict.keys()} (custom event(s)).")

        return custom_indicator_dict, custom_event_dict
    

    except Exception as error:
        questionary.print(f"❌ Unable to load custom indicators and events: {error}", style=err_color)

        return None

def checking_file(chemin, err_color):

    path = Path(chemin).expanduser()

    if not path.exists():
        print(""*80, end="\r")
        print(""*80, end="\r")
        return False

    if not path.is_file():
        print(""*80, end="\r")
        print(""*80, end="\r")
        return False

    if path.suffix.lower() != ".db":
        print(""*80, end="\r")
        print(""*80, end="\r")
        return False

    return True

def turn_page(logo, symbol, interval, logo_color, active_color):

    console = Console()
    console.clear()
    display_blank_lines(1)
    questionary.print(logo, style=logo_color)
    display_blank_lines(1)
    questionary.print(f"Working on {symbol} — {interval}", style=active_color)
    display_blank_lines(1)

def skip(pointer, config, action):
    res = questionary.select("Return to the main menu?", choices=["Back to the main menu", f"Stay in {action}"], pointer=pointer, style=config).ask()
    if res == "Back to the main menu":
        clear_display_line()
        return True
    else:
        return False

def yes_no(question, pointer, config):
    rep = questionary.select(question, ["No", "Yes"], pointer=pointer, style=config).ask()
    return rep

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

def compute_series(cursor, root_name, function_, window_series, data, last_timestamp, indications_color, index, err_color, config, pointer):

    model = FunctionData(function_)

    f = model.func
    o = model.func_type

    if o == "general_app":
        for i in range(window_series[0], window_series[1], window_series[2]):
            name = root_name
            window = i
            name += f"_{window}"

            name = name_verification(cursor=cursor, 
                                     config=config, 
                                     pointer=pointer, 
                                     name=name, 
                                     err_color=err_color,
                                     table="candles")

            if not name:
                continue

            app.general_application(cursor, name, f, window, data, last_timestamp)
            cursor.connection.commit()
            questionary.print(f"Computed {name} with window size {window}.", style=indications_color)

    if o == "custom":
        for i in range(window_series[0], window_series[1], window_series[2]):
            name = root_name
            window = i
            name += f"_{window}"
            data[index] = window

            name = name_verification(cursor, config, pointer, name, err_color=err_color, table="candles")

            if not name:
                continue

            f(cursor, data, name)
            cursor.connection.commit()
            questionary.print(f"Computed {name} with window size {window}.", style=indications_color)

def name_definition(config, err_color, name):
    root_name = name
    while True:
        name = questionary.text("Define another name: ", default=name, style=config).ask()

        if not _identifier_is_valid(name):
            questionary.print("❌ Use a name starting with a letter or underscore; use only letters, numbers, and underscores.", style=err_color)

        elif root_name == name:
            questionary.print(f"❌ You must define a different name (actual name : {name})", style=err_color)

        else:
            break
    return name

def name_verification(cursor, config, pointer, name, err_color, table):

        if column_exists(cursor, table, name):
            res = questionary.select(f"❌ {name} already exixts. Do you want to replace the actual {name} or define another name for {name}?",
                                    choices=[f"Define another name for {name}", 
                                                f"Replace the actual {name}", 
                                                f"Do not calculate {name}"], pointer=pointer).ask()

            if res == f"Define another name for {name}":
                    
                name = name_definition(config=config, err_color=err_color, name=name)
    
                return name

            elif res == f"Replace the actual {name}":
                cursor.execute(f"""
                                ALTER TABLE candles
                                DROP COLUMN {name}
                        """)
                cursor.execute(f"""
                                DELETE FROM indicators_metadata
                                WHERE column_name = ?
                        """, (name,))
                cursor.connection.commit()
                
                return name

            else:
                return None

        else:
            return name

def parameters_custom_indic(indicator_, existing_parameters, config, indications_color):

    parameters = []

    model = FunctionData(indicator_)

    nb = model.nb_parameters           # nb of parameters 
    rp = model.recommended_parameters  # recommended paramters

    for i in range(nb):
        while True:
            parameter = questionary.text(f"{rp[i][0]}", style=config).ask()

            if rp[i][1](parameter, parameter_list=existing_parameters) is True:
                parameters.append(parameter)
                break

    questionary.print(f"Selected parameters: {parameters}", style=indications_color)

    return parameters

def display_parameters(parameters, color):
    for i in range(len(parameters)):
        val = parameters[i]
        val = str(val)
        if (i+1)%3 != 0:
            if len(str(val)) > 25:
                x = len(str(val)) - 25
                val = str(val)[:-x-3] + "..."
                questionary.print(f"{val}" + " " * 5, end="", style=color)

            else:
                questionary.print(f"{val}" + " " * (30-(len(val))), end="", style=color)

        else:
            questionary.print(f"{val}" + " " * 15, style=color)

    print("")

def data_base(pointer, logo, config, err_color):

    rep = questionary.select("Would you like to create or open a database?", choices=["Create a database", "Open a database"], pointer=pointer, style=config).ask()

    if rep == "Open a database":

        file = questionary.path("Database file (.db):", validate=lambda chemin: checking_file(chemin, err_color)).ask()
        if not is_marketlad_database(file):
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

        selected_database = MarketLabDataBase(name=file, symbol=symbol, timeframe=interval)
        selected_database.database_commit()

        return selected_database

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

        name = "marketlab_database" + "_" + str(symbol) + "_" + str(interval)

        new_database = MarketLabDataBase(name=name, symbol=symbol, timeframe=interval)
        new_database.database_commit()
        
        return new_database

def download_data(active_database, history, config, err_color, pointer):

    print(""*80, end="\r")
    print("💾 Download Data")


    res = questionary.select(f"Do you want to download all the history of {active_database.symbol} {active_database.timeframe} ?", 
                             choices=["Select a precise date", "Download all the history"], 
                             style=config, pointer=pointer).ask()

    if res == "Select a precise date":
        questionary.print("Define a start date (enter 'LAST' for select the last date): ")

        while True:
            start = questionary.form(year=questionary.text("Year: ", style=config),
                                    month=questionary.text("Month: ", style=config),
                                    day=questionary.text("Day: ", style=config)).ask()

            if start["year"].upper() == "LAST":
                start_timestamp = active_database.get_start_timestamp() 
                break

            else:
                try:
                    year = int(start["year"])
                    month = int(start["month"])
                    day = int(start["day"])

                except ValueError:
                    questionary.print("You must enter integers.")

            try:
                start_timestamp = datetime(year, month, day)
                start_timestamp = start_timestamp.timestamp() * 1000

            except ValueError as e:
                questionary.print(f"❌ The date you choose is invalid: {e}.", style=err_color)

            if start_timestamp > datetime.today().timestamp() * 1000:
                questionary.print("❌ You must choose a past date")
            else: 
                break

        questionary.print("Select an end date (enter 'TODAY' for select the today date): ", )

        while True:
            end = questionary.form(year=questionary.text("Year: ", style=config),
                                    month=questionary.text("Month: ", style=config),
                                    day=questionary.text("Day: ", style=config)).ask()

            if end["year"].upper() == "TODAY":
                end_timestamp = datetime.today() 
                end_timestamp = int(end_timestamp.timestamp() * 1000)
                break

            else:
                while True:
                    try:
                        year = int(end["year"])
                        month = int(end["month"])
                        day = int(end["day"])


                    except ValueError:
                        questionary.print("❌ You must enter integers.", style=err_color)
                        break

                    try:
                        end_timestamp = datetime(year, month, day)
                        end_timestamp = end_timestamp.timestamp() * 1000
                    except ValueError as e:
                        questionary.print(f"❌ The date you choose is invalid: {e}.", style=err_color)

                    if end_timestamp < start_timestamp():
                        questionary.print(f"❌ You must choose a date after the {datetime.fromtimestamp(start_timestamp)}", style=err_color)

                    elif end_timestamp < datetime.today().timestamp() * 1000:
                        questionary.print("❌ You must choose a past date.", style=err_color)
                    else: 
                        valid_date = True
                        break

                if valid_date:
                    break

    else:
        start_timestamp = datetime(2017, 8, 17)
        start_timestamp = start_timestamp.timestamp() * 1000

        end_timestamp = datetime.today()
        end_timestamp = end_timestamp.timestamp() * 1000

    de.extraction_binance(cursor=active_database.cursor, 
                          symbol=active_database.sybol,
                          interval=active_database.timeframe,
                          start_timestamp=start_timestamp, 
                          end_timestamp=end_timestamp)

    active_database.database_commit()
    
    print("Data downloaded.")
    
    history.append(f"{active_database.symbol} {active_database.timeframe} Downloaded ")
   
def calculate_indic(active_database, indicator_dict, indicator_list, history, pointer, config, err_color, indications_color):

    symbol = active_database.symbol
    timeframe = active_database.timeframe
    cursor = active_database.cursor
    conn = active_database.conn

    print(""*80, end="\r")
    print("📈 Calculate Indicators")
    print("")

    existing_parameters = [row[1] for row in active_database.cursor.execute("PRAGMA table_info(candles)").fetchall()]


# FUNCTION SELECTION  ------------------

    display_parameters(indicator_list, color=indications_color)

    while True : 
        indicator_name = questionary.autocomplete("Select an indicator:", choices=indicator_list, style=config).ask()

        if indicator_name == "":
            print(""*80, end="\r")
            print("")
            questionary.print("❌ Select an indicator.", style=err_color)

        elif indicator_name in indicator_list:
            indicator_ = indicator_dict[indicator_name]
            break
        else: 
            print(""*80, end="\r")
            print("")
            questionary.print("❌ This function does not exist. Select a function from the list", style=err_color)

    model = FunctionData(indicator_)

    function_type = model.func_type
    f = model.func
    recommended_para = model.recommended_parameters

# PARAMETERS SELECTION  -----------------

    parameters = []

    display_parameters(existing_parameters, color=indications_color)

    # GENERAL APP -------------------

    if function_type == "general_app":
        if type(indicator_[2]) is list:
            questionary.print(f"Recommended parameters: {indicator_[2]}", style=indications_color)

        for i in range(indicator_[1]):
            parameter = questionary.autocomplete(f"Select parameter {i + 1}:", choices=existing_parameters, style=config).ask()
            if parameter not in existing_parameters:
                questionary.print("❌ Select a parameter from the list.", style=err_color)
                return
            parameters.append(parameter)

    # CUSTOM -----------------

    else:
        parameters = parameters_custom_indic(indicator_=indicator_, 
                                                existing_parameters=existing_parameters, 
                                                config=config, 
                                                indications_color=indications_color)

# NAME DEFINITION --------------

    root_name = f.__name__
    for i in range(len(parameters)):
        root_name += "_"+str(parameters[i])

# -------------------------

    res_serie = questionary.select("Do you want to compute a series of indicators with different window sizes?", ["Single indicator", "Series of indicators"], pointer=pointer, style=config).ask()

#   SINGLE INDICATOR -------------------------------------------

    if res_serie == "Single indicator":

        # GENERAL APP

        if function_type == "general_app":
            while True :
                while True:
                    window = questionary.text("Window size:", style=config).ask()

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
                    continue

                else:
                    if window > 1:
                        name = root_name + "_" + str(window)

                name = name_verification(cursor=active_database.cursor,
                                         config=config,
                                         pointer=pointer,
                                         data=parameters,
                                         name=name,
                                         err_color=err_color,
                                         table="candles")

                if not name:
                    break

            if not name:
                return

            app.general_application(active_database.cursor, name, f, window, parameters, last_timestamp=1)
            display_parameters(existing_parameters, indications_color)

        # CUSTOM

        else: 

            name = name_verification(cursor=active_database.cursor,
                                     config=config,
                                     pointer=pointer,
                                     data=parameters,
                                     name=root_name,
                                     err_color=err_color,
                                     table="candles")

            if not name:
                return 

            f(active_database.cursor, parameters, name)
        
            

# SERIES OF INDICATOR --------------------

    if res_serie == "Series of indicators":

        window_series = (None, None, None)

        # GENERAL APP -----------------------

        if function_type == "general_app":
            while True :
                window_start = questionary.text("Start of the series:", style=config).ask()
                try:
                    window_start = int(window_start)
                    break
                except ValueError:
                    print(""*80, end="\r")
                    print("")
                    questionary.print("❌ You must enter an integer greater than 0", style=err_color)
            window_series = (window_start, None, None)

            while True :
                window_end = questionary.text("End of the series:", style=config).ask()
                try:
                    window_end = int(window_end)
                    if window_end > window_start:
                        break
                    else:
                        questionary.print(f"❌ You must enter a value greater than the start of the serie (currantly {window_start})")
                except ValueError:
                    print(""*80, end="\r")
                    print("")
                    questionary.print("❌ You must enter an integer greater than 0", style=err_color)

            window_series = (window_start, window_end, None)

            while True :
                window_step = questionary.text("Step of the series:", style=config).ask()
                try:
                    window_step = int(window_step)
                    break
                except ValueError:
                    print(""*80, end="\r")
                    print("")
                    questionary.print("❌ You must enter an integer greater than 0", style=err_color)

            window_series = (window_start, window_end, window_step)

        
            root_name = name
            for i in range(window_series[0], window_series[1], window_series[2]):
                name = root_name
                window = i
                name += f"_{window}"

                if column_exists(active_database.cursor, "candles", name):
                    res = questionary.select(f"❌ {name} already exixts. Do you want to replace the actual {name} or define another name for {name}?",
                        choices=[f"Define another name for {name}", f"Replace the actual {name}"],
                        style=err_color).ask()

        # CUSTOM ----------------------

        else:

            choices = [r[0] for r in recommended_para]

            serie_on_parameter  = questionary.select("On which parameter do you what to apply the serie ?", 
                               choices=choices, 
                               pointer=pointer, 
                               style=config).ask()

            index_serie_on_para = choices.index(serie_on_parameter)
    
            while True :
                window_start = questionary.text("Start of the series:", style=config).ask()
                try:
                    window_start = int(window_start)
                    break
                except ValueError:
                    print(""*80, end="\r")
                    print("")
                    questionary.print("❌ You must enter an integer greater than 0", style=err_color)
            window_series = (window_start, None, None)

            while True :
                window_end = questionary.text("End of the series:", style=config).ask()
                try:
                    window_end = int(window_end)
                    if window_end > window_start:
                        break
                    else:
                        questionary.print(f"❌ You must enter a value greater than the start of the serie (currantly {window_start})")
                except ValueError:
                    print(""*80, end="\r")
                    print("")
                    questionary.print("❌ You must enter an integer greater than 0", style=err_color)

            window_series = (window_start, window_end, None)

            while True :
                window_step = questionary.text("Step of the series:", style=config).ask()
                try:
                    window_step = int(window_step)
                    break
                except ValueError:
                    print(""*80, end="\r")
                    print("")
                    questionary.print("❌ You must enter an integer greater than 0", style=err_color)

            window_series = (window_start, window_end, window_step)

        print(f"{root_name}")

        compute_series(cursor, 
                        root_name=root_name, 
                        function_=indicator_, 
                        window_series=window_series, 
                        data=parameters, 
                        indications_color=indications_color, 
                        err_color=err_color,
                        pointer=pointer,
                        config=config,
                        index=index_serie_on_para, 
                        last_timestamp=1)

    conn.commit()
    history.append(f"Serie {root_name} {window_series} {parameters} Calculated on {symbol} {timeframe}")

def manage_custom_indicators_and_events(pointer, err_color, custom_indicator_dict, custom_event_dict, config):
    rep = questionary.select("Actions : ", ["Create custom_indicators.py", 
                                            "List available custom indicators and events",
                                            "Reload custom indicators",
                                            "Back to main menu"], pointer=pointer, style=config).ask()

    if rep == "Create custom_indicators.py":
        create_custom_indicators_file(err_color, pointer)
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

        res = questionary.select("", ["Ok"], pointer=pointer, style=config).ask()

        return custom_indicator_dict, custom_event_dict

    return None
 
def calculate_stats(active_database, pointer, config, indications_color):

    cursor = active_database.cursor

    print(""*80, end="\r")
    print("📊 Calculate Statistics")
    print("")

    cursor.execute("""PRAGMA table_info(candles)""")
    existing_parameters = [row[1] for row in cursor.fetchall()]
    existing_parameters.remove("open_time")

    cursor.execute("""PRAGMA table_info(status)""")
    existing_status = [row[1] for row in cursor.fetchall()]
    existing_status.remove("open_time")
    rep = questionary.select("Choose a chart type:", choices=["Classic chart", "Heat map"], pointer=pointer, style=config).ask()

    if not existing_status:
        questionary.print("❌ Create an event before calculating statistics.", style="fg:red")
        return
    try:
        x_axis = int(questionary.text("Number of quantile intervals: ", style=config).ask())
        if x_axis < 1:
            raise ValueError
    except ValueError:
        questionary.print("❌ Enter a positive integer.", style="fg:red")
        return

    while True:
        display_parameters(existing_parameters, color=indications_color)
        parameter = questionary.autocomplete("Select a parameter:", choices=existing_parameters, style=config).ask()
        if parameter not in existing_parameters:
            questionary.print("❌ Select a parameter from the list.", style="fg:red")      
        else:
            break

    while True:
        status = questionary.autocomplete("Select a status:", choices=existing_status, style=config).ask()
        if status not in existing_status:
            questionary.print("❌ Select a status from the list.", style="fg:red")
        else:   
            break


    if rep == "Classic chart":
        sm.stat_onevar(cursor, status, parameter, int(x_axis))

    else:
        display_parameters(existing_parameters, color=indications_color)
        second_parameter = questionary.autocomplete("Select a second parameter:", choices=existing_parameters, style=config).ask()
        if second_parameter not in existing_parameters:
            questionary.print("❌ Select a parameter from the list.", style="fg:red")
            return
        sm.stat_twovar(cursor, status, parameter, second_parameter, int(x_axis))
        
def calculate_event(event_dict, pointer, active_database, err_color, config, indications_color):

    cursor = active_database.cursor

    print(""*80, end="\r")
    print("🎉 Calculate Events")
    print("")


    cursor.execute("""PRAGMA table_info(candles)""")
    existing_parameters = [row[1] for row in cursor.fetchall()]

# EVENT SELECTION

    while True :
        display_parameters(event_list, indications_color)
        event_list = list(event_dict.keys())
        name = questionary.select("Select an event:", choices=event_list, pointer=pointer, style=config).ask()

        if name not in event_list:
            questionary.print("❌ Select an event from the list.", style=err_color)
        else:
            break  

    event = event_dict[name]
    event_function = event[0]



# CUSTOM EVENTS

    if event[3] == "custom":

        parameters = []
        for i in range(event[1]):
            while True:
                parameter = questionary.text(f"{event[2][i][0]}", style=config).ask()

                if event[2][i][1](parameter, parameter_list=existing_parameters) is True:
                    parameters.append(parameter)
                    break

        while True:
            res = questionary.select("Append selected parameters to the event name ?", ["No", "Append seleccted parameters to the event name"], pointer=pointer, style=config).ask()
            after_name = None

            if res == "Append seleccted parameters to the event name":
                after_name = ""
                for i in range(len(parameters)):
                    after_name += f"_{parameters[i]}"

            if after_name != None:
                name += after_name

            questionary.print(f"Event name: {name}")

            if column_exists(cursor, "status", name) is True:
                questionary.print("This event already exists.")
                res = questionary.select("Do you wanna choose another name for this event ? If you select 'No', the existing event will be replaced.", 
                                        choices=["Yes", "No"], 
                                        pointer=pointer, 
                                        style=config).ask()

                if res == "No":
                    break 

            else: 
                break

        event_function(cursor, parameters, name)
        cursor.connection.commit()

        questionary.print("Event calculated.")


# GENERAL APPLICATION
    
    elif event[3] == "general_app":

# WINDOW SELECTION
        while True :
            while True:
                window = questionary.text("Window size (type 'ALL' for all data):", style=config).ask()

                if str(window).upper() == "ALL":
                    window = "ALL"
                    break

                else:
                    try:
                        window = int(window)
                        break

                    except ValueError:
                        print(""*80, end="\r")
                        print("")
                        questionary.print("❌ You must enter an integer greater than 0", style=err_color)

            if type(window) is not str and window <= 0:
                print(""*80, end="\r")
                print("")
                questionary.print("❌ You must enter an integer greater than 0", style=err_color)

            else:
                break



        parameters = []

        cursor.execute("""PRAGMA table_info(candles)""")
        existing_parameters = [row[1] for row in cursor.fetchall()].remove("open_time")

    # PARAMETERS SELECTION

        display_parameters(existing_parameters, color=indications_color)

        if type(event[-1]) is list:
            print("")
            questionary.print(f"Recommended parameters: {event[-1]}", style=indications_color)

        for i in range(event[1]):

            while True:
                questionary.print(f"Existing parameters: {existing_parameters}")
                parameter = questionary.autocomplete(f"Select parameter {i + 1}:", choices=existing_parameters, style=config).ask()
                if parameter not in existing_parameters:
                    questionary.print("❌ Select a parameter from the list.", style=err_color)
                else:
                    break
            parameters.append(parameter)

        questionary.print(f"Selected parameters: {parameters}", style="fg:lightblue")
        
    # NAME
        while True:
    
            res = questionary.select("Append selected parameters to the event name ?", ["No", "Yes"], pointer=pointer, style=config).ask()

            after_name = None

            if res == "Yes":
                after_name = ""
                for i in range(len(parameters)):
                    after_name += f"_{parameters[i]}"

            
            if after_name != None:
                name += after_name


            if window == "ALL":
                nb_open_times = cursor.execute("SELECT COUNT(*) FROM candles").fetchone()[0]
                window = nb_open_times

            else:
                name += f"_{window}"



            questionary.print(f"Event name: {name}")

            if column_exists(cursor, "status", name) is True:
                questionary.print("This event already exists.")
                res = questionary.select("Do you wanna choose another name for this event ? If you select 'No', the existing event will be replaced.", 
                                        choices=["Yes", "No"], 
                                        pointer=pointer, 
                                        style=config).ask()

                if res == "No":
                    break 

            else: 
                break


        app.ganeral_event_application(cursor, name, event_function, window, parameters)
        questionary.print("Event calculated.")

def plot_indic(active_database, err_color, pointer, config, indications_color):

    cursor = active_database.cursor

    print(""*80, end="\r")
    print("✏️  Plot")
    print(" ")

    values = []
    cursor.execute("""PRAGMA table_info(candles)""")
    existing_values = [row[1] for row in cursor.fetchall()]
    existing_values.remove("open_time")

    display_parameters(existing_values, color=indications_color)

    while True:
        choice = questionary.autocomplete("Select an indicator to plot:", 
                                          choices=existing_values, style=config
                                          ).ask()
        if not choice in existing_values:
            questionary.print("❌ Select an indicator from the list.", 
                              style=err_color)
        else:
            values.append(choice)
            rep = questionary.select("Plot another indicator?", 
                                     ["Yes", "No"],
                                     pointer=pointer, style=config).ask()
            if rep == "No":
                questionary.print(f"Indicators to plot: {values}", style="fg:lightblue")
                break

   
    rep = questionary.select("Plot a status?", choices=["Yes", "No"], pointer=pointer, style=config).ask()

    if rep == "Yes":
        cursor.execute("""PRAGMA table_info(status)""")
        existing_status = [r[1] for r in cursor.fetchall()]

        existing_status.remove("open_time")

        display_parameters(existing_status, color=indications_color)

        if not existing_status:
            questionary.print("No status is available yet.", style=err_color)
            status = None
        else:
            while True:
                status = questionary.autocomplete("Select a status: ", choices=existing_status, style=config).ask()


                if status not in existing_status:
                    questionary.print("❌ Select a status from the list.", style=err_color)

                else:
                    break

    else:
        status = None

    
    questionary.print("Plotting… (close the graph window to continue)", style="fg:lightblue")

    gp.plot(cursor, values, status)

def delete_col(active_database, history, pointer, config, err_color, indications_color):

    cursor = active_database.cursor
    symbol = active_database.symbol
    timeframe = active_database.timeframe
    

    print(""*80, end="\r")
    print("🗑️  Delete a Column")
    print("")


    target = questionary.select("What would you like to delete?", ["An indicator", "A status"], pointer=pointer, style=config).ask()


    if target == "An indicator":

        cursor.execute("""PRAGMA table_info(candles)""")
        existing_parameters = [row[1] for row in cursor.fetchall()]
        existing_parameters.remove("open_time")


        if not existing_parameters:
            questionary.print("No indicator can be deleted.", style="fg:yellow")
            return

        display_parameters(existing_parameters, indications_color)
        parameters = questionary.autocomplete("Select an indicator:", choices=existing_parameters, style=config).ask()
        if parameters in existing_parameters:
            rep = yes_no(f'Permanently delete "{parameters}"?', pointer, config)

            if rep == "Yes":
                cursor.execute(f"""
                    ALTER TABLE candles
                    DROP COLUMN {_quote_identifier(parameters)}""")
                history.append(f"{parameters} deleted in {symbol} {timeframe}.")


    if target == "A status":

        cursor.execute("""PRAGMA table_info(status)""")
        existing_parameters = [row[1] for row in cursor.fetchall()]
        existing_parameters.remove("open_time")
            
        if not existing_parameters:
            questionary.print("No status can be deleted.", style="fg:yellow")
            return

        while True:

            display_parameters(existing_parameters, indications_color)

            parameters = questionary.autocomplete("Select a status:", choices=existing_parameters, style=config).ask()

            if parameters not in existing_parameters:
                questionary.print("❌ Select a status from the list.", style=err_color)
            else:
                break

        if parameters in existing_parameters:
            rep = yes_no(f'Permanently delete "{parameters}"?', pointer, config)

            if rep == "Yes":
                cursor.execute(f"""
                    ALTER TABLE status
                    DROP COLUMN {_quote_identifier(parameters)}""")
                history.append(f"{parameters} deleted in {symbol} {timeframe}.")
         
def action_history(history, heading_color="fg:cyan"):

    display_heading("📖 History", style=heading_color)

    if len(history) == 0:
        print("The action history is empty.")

    else:
        for i in range(len(history)):
            print(history[i])

def take_look(history, pointer, indicator_dict, active_database, config, indications_color):
    print(""*80, end="\r")
    print("👀 Inspect Data")
    print("")

    cursor = active_database.cursor

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

        last_values = [r[0] for r in rows][-12:]

        start_time = cursor.execute(f"""
                                SELECT open_time
                                FROM candles
                                WHERE {copy} IS NOT NULL
                                ORDER BY open_time ASC 
                                LIMIT 1""").fetchone()[0]

                                
        end_time = cursor.execute(f"""
                                SELECT open_time
                                FROM candles
                                WHERE {copy} IS NOT NULL
                                ORDER BY open_time DESC
                                LIMIT 1""").fetchone()[0]

        start_timestamp = start_time/1000
        end_timestamp = end_time/1000

        start_date = datetime.fromtimestamp(start_timestamp)
        end_date = datetime.fromtimestamp(end_timestamp)

        questionary.print(f"Calculated over {nb} candles", style="fg:blue")
        questionary.print(f"From the {start_date} "\
                          f"to the {end_date}.")
        questionary.print("Last values:", style="fg:blue")

        display_parameters(last_values, indications_color)


    if look == "Available functions":
        copy = questionary.select("Available indicators:", choices=indicator_dict, pointer=pointer, style=config).ask()


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

def settings(pointer, logo_color, questions_color, answers_color, err_color, active_color, config, indications_color, heading_color):
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

    setting = questionary.select("What would you like to change?", choices=["Colors", "Pointer"], pointer=pointer, style=config).ask()

    if setting == "Pointer":
        pointer = questionary.select("Choose a pointer:", choices=["▶︎", "❯", "➜", "→"], pointer=pointer, style=config).ask()
    else:
        labels = {
            "Logo": "logo_color",
            "Questions": "questions_color",
            "Answers": "answers_color",
            "Errors": "err_color",
            "Active database": "active_color",
            "Indications": "indications_color",
            "Heading": "heading_color"
        }
        label = questionary.select("Choose an element:", choices=list(labels), pointer=pointer, style=config).ask()
        color = questionary.select("Choose a color:", choices=color_list, pointer=pointer, style=config).ask()
        color = f"fg:{color}"
        if labels[label] == "logo_color":
            logo_color = color
        elif labels[label] == "questions_color":
            questions_color = color
        elif labels[label] == "answers_color":
            answers_color = color
        elif labels[label] == "err_color":
            err_color = color
        elif labels[label] == "active_color":
            active_color = color
        elif labels[label] == "indications_color":
            indications_color = color
        else:
            heading_color = color

    return pointer, logo_color, questions_color, answers_color, err_color, active_color, indications_color, heading_color
