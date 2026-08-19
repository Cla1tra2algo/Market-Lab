import math_formula as mf
import event as ev
import stat_making as sm
import applications as app
import sqlite3
import data_extraction as de
from datetime import *
import questionary 
from commands import *
from questionary import *
from rich.console import Console

start = datetime(2017, 8, 17)             # limites temporelles de l'exctraction des donnés 
timestamp = int(start.timestamp() * 1000)
pointer = "▶︎"
logo = """ 
    ╔═╦╦╗╔═╗╦═╗╦╔═╔═╗╔╦╦═══════════╗ 
    ║ ║║║╠═╣╠╦╝╠╩╗║╣  ║  ╦  ╔═╗╔╗  ║   
    ║ ╩ ╩╩ ╩╩╚═╩ ╩╚═╝ ╩  ║  ╠═╣╠╩╗ ║ 
    ╚════════════════════╩═╝╩ ╩╚═╩═╝ 
"""

copy = None

logo_color = "fg:pink"
questions_color = "fg:blue"
answers_color = "fg:orange"
err_color = "fg:red"
active_file = "fg:yellow"
indications_color = "fg:green"

style = questionary.Style([("question", questions_color), ("answer", answers_color)])


base_indicator_dict = mf.indicator_dict
custom_indicator_dict = {}
indicator_dict = dict(base_indicator_dict)



base_event_dict = ev.base_event_dict
custom_event_dict = {}
event_dict = dict(base_event_dict)


INDICATOR_LIST = list(indicator_dict.keys())

values_list = []
questionary.print(logo, style=logo_color)
print("")


conn, cursor, symbol, interval = data_base(pointer, logo, config=style, err_color=err_color)
conn.commit()

history = []


def run_safely(action, *args, **kwargs):
    try:
        return action(*args, **kwargs)
    except (RuntimeError, ValueError, sqlite3.Error) as error:
        questionary.print(f"❌ {error}", style=err_color)
        return None


while True :

    command = questionary.select("Actions : ", 
                                choices = [
                                "💾 Download Data",
                                "📈 Calculate Indicators",
                                "📊 Calculate Statistics",
                                "🎉 Calculate Events",
                                "✏️  Plot",
                                "📘 History",
                                "⚙️  Settings",
                                "👀 Take a Look",
                                "🚪 Exit"], pointer=pointer, style=style).ask()

    print(""*80, end="\r")


    if command == "💾 Download Data":
        while True:
            run_safely(download_data, cursor, symbol, interval, conn, history, err_color=err_color, config=style, pointer=pointer)
            res = skip(pointer, config=style, action="💾 Download Data")
            turn_page(logo, symbol, interval, logo_color, active_color=active_file)
            if res is True:
                break

    if command == "📈 Calculate Indicators":
        while True:
            run_safely(calculate_indic, indicator_dict=indicator_dict, 
                            indicator_list=INDICATOR_LIST, 
                            cursor=cursor, 
                            history=history, 
                            symbol=symbol, 
                            interval=interval, 
                            pointer=pointer, 
                            err_color=err_color, 
                            config=style, 
                            conn=conn,
                            indications_color=indications_color)
            

            res = skip(pointer, config=style, action="📈 Calculate Indicators")
            turn_page(logo, symbol, interval, logo_color=logo_color, active_color=active_file)
            if res is True:
                break
        
    if command == "📊 Calculate Statistics":

        run_safely(calculate_stats, cursor, pointer, config=style, indications_color=indications_color)

    if command == "🎉 Calculate Events":


        while True :

            run_safely(calculate_event, event_dict, pointer, cursor, err_color, style, indications_color=indications_color)

            res = skip(pointer, config=style, action="🎉 Calculate Events")
            turn_page(logo, symbol, interval, logo_color, active_color=active_file)

            if res:
                break
        
    if command == "✏️  Plot":

        while True : 


            run_safely(plot_indic, cursor, err_color=err_color, pointer=pointer, config=style, indications_color=indications_color)
            res = skip(pointer, config=style, action="✏️  Plot")
            turn_page(logo, symbol, interval, logo_color, active_color=active_file)
            if res is True:
                break
        
    if command == "📘 History":
        while True:
            action_history(history)
            res = skip(pointer, config=style, action="📘 History")
            turn_page(logo, symbol, interval, logo_color=logo_color, active_color=active_file)
            if res is True:
                break

    if command == "⚙️  Settings":

        while True:

            res = questionary.select("Actions: ", ["🧩 Manage Custom Indicators and Events", "🗑️  Delete a Column", "🎨 Theme", "📁 Open or Create a Database"], pointer=pointer, style=style).ask()

            if res == "🎨 Theme":
                while True:
                    pointer, logo_color, questions_color, answers_color, err_color, active_file, indications_color = settings(
                        pointer,
                        logo_color,
                        questions_color,
                        answers_color,
                        err_color,
                        active_file,
                        config=style,
                        indications_color=indications_color
                    )
                    style = questionary.Style([
                        ("question", questions_color),
                        ("answer", answers_color),
                    ])
                    res = skip(pointer, style, "🎨 Theme")
                    turn_page(logo, symbol, interval, logo_color, active_color=active_file)

                    if res:
                        break

            if res == "🧩 Manage Custom Indicators and Events":

                while True:
                    custom_registries = run_safely(
                    manage_custom_indicators_and_events,
                    pointer,
                    err_color,
                    custom_indicator_dict,
                    custom_event_dict,
                    config=style
                    )
                    if custom_registries is not None:
                        custom_indicator_dict, custom_event_dict = custom_registries
                        merged_indicators = run_safely(
                            merge_registries,
                            base_indicator_dict,
                            custom_indicator_dict,
                            "indicator_dict",
                        )
                        merged_events = run_safely(
                            merge_registries,
                            base_event_dict,
                            custom_event_dict,
                            "event_dict",
                        )
                        if merged_indicators is not None and merged_events is not None:
                            indicator_dict = merged_indicators
                            event_dict = merged_events
                            INDICATOR_LIST = list(indicator_dict.keys())

                        res = skip(pointer, config=style, action="🧩 Manage Custom Indicators and Events")
                        turn_page(logo, symbol, interval, logo_color, active_color=active_file)

                        if res:
                            break

            if res == "🗑️  Delete a Column":

                while True:
                    run_safely(delete_col, cursor, history, symbol, interval, pointer, config=style, err_color=err_color, indications_color=indications_color)
                    conn.commit()
                    res = skip(pointer, config=style, action="🗑️  Delete a Column")
                    turn_page(logo, symbol, interval, logo_color=logo_color, active_color=active_file)
                    if res is True:
                        break

            if res == "📁 Open or Create a Database":

                while True:
                    conn.commit()
                    conn.close()

                    conn, cursor, symbol, interval = data_base(
                        pointer, logo, err_color=err_color, config=style
                    )

                    res = skip(pointer, config=style, action="📁 Open or Create a Database")
                    turn_page(logo, symbol, interval, active_color=active_file, logo_color=logo_color)

                    if res:
                        break


            echap = skip(pointer, config=style, action="⚙️  Settings")
            turn_page(logo, symbol, interval, logo_color, active_color=active_file)
            if echap is True:
                break

    if command == "👀 Take a Look":
        while True:
            res = take_look(history, pointer, indicator_dict, cursor, config=style, indications_color=indications_color)
            if res != None:
                copy = res

            echap = skip(pointer, config=style, action="👀 Take a Look")
            turn_page(logo, symbol, interval, logo_color=logo_color, active_color=active_file)
            if echap is True:
                break

    if command == "🚪 Exit":
        rep = yes_no("Do you really want to exit Market Lab?", pointer, config=style)

        if rep == "Yes":
            conn.commit()
            conn.close()
            questionary.print("Leaving MARKET LAB", style="fg:red")
            break

        else:
            print(""*80, end="\r")
