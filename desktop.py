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

style = questionary.Style([("question", questions_color), ("answer", answers_color)])


function_dict = mf.function_dict

event_dict = {
    "cross" : (ev.cross, 2, ["sma"]),
    "highest_lowest" : (ev.highest_lowest, 2, ["close", "window"])
}


function_list = list(function_dict.keys())

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
                                "📁 Open or Create a Database",
                                "💾 Download Data",
                                "📈 Calculate Indicators",
                                "🧩 Manage Custom Indicators",
                                "📊 Calculate Statistics",
                                "🎉 Calculate Events",
                                "✏️  Plot",
                                "🗑️  Delete a Column", 
                                "📘 History",
                                "⚙️  Settings",
                                "👀 Take a Look",
                                "🚪 Exit"], pointer=pointer, style=style).ask()

    print(""*80, end="\r")

    if command == "📁 Open or Create a Database":

        conn.commit()
        conn.close()

        conn, cursor, symbol, interval = data_base(
            pointer, logo, err_color=err_color, config=style
        )

        skip(pointer, config=style)
        turn_page(logo, symbol, interval, active_color=active_file, logo_color=logo_color)
        

    if command == "💾 Download Data":
        run_safely(download_data, cursor, symbol, interval, timestamp, conn, history)
        res = skip(pointer, config=style)
        turn_page(logo, symbol, interval, logo_color, active_color=active_file)



    if command == "📈 Calculate Indicators":
        while True:
            run_safely(calculate_indic, function_dict=function_dict, 
                            function_list=function_list, 
                            cursor=cursor, 
                            history=history, 
                            symbol=symbol, 
                            interval=interval, 
                            pointer=pointer, 
                            err_color=err_color, 
                            config=style, 
                            conn=conn)
            
            res = skip(pointer, config=style)
            turn_page(logo, symbol, interval, logo_color=logo_color, active_color=active_file)
            if res == "Yes":
                break
        
    if command == "📊 Calculate Statistics":

        run_safely(calculate_stats, cursor, pointer)


    if command == "🎉 Calculate Events":

        while True :
            print(""*80, end="\r")
            print("🎉 Calculate Events")
            print(" ")

            run_safely(calculate_event, event_dict, pointer, cursor)

            res = skip(pointer, config=style)
            turn_page(logo, symbol, interval, logo_color, active_color=active_file)

            if res == "Yes":
                break

        
    if command == "✏️  Plot":

        while True : 
            print(""*80, end="\r")
            print("✏️  Plot")
            print(" ")

            run_safely(plot_indic, cursor, err_color=err_color, pointer=pointer)
            res = skip(pointer, config=style)
            turn_page(logo, symbol, interval, logo_color, active_color=active_file)
            if res == "Yes":
                break


        
    if command == "🗑️  Delete a Column":
        while True:
            run_safely(delete_col, cursor, history, symbol, interval, pointer, config=style)
            conn.commit()
            res = skip(pointer, config=style)
            turn_page(logo, symbol, interval, logo_color=logo_color, active_color=active_file)
            if res == "Yes":
                break
        
    if command == "📘 History":
        while True:
            action_history(history)
            res = skip(pointer, config=style)
            turn_page(logo, symbol, interval, logo_color=logo_color, active_color=active_file)
            if res == "Yes":
                break

    if command == "⚙️  Settings":
        pointer, logo_color, questions_color, answers_color, err_color, active_file = settings(
            pointer,
            logo_color,
            questions_color,
            answers_color,
            err_color,
            active_file,
        )
        style = questionary.Style([
            ("question", questions_color),
            ("answer", answers_color),
        ])
        turn_page(logo, symbol, interval, logo_color, active_color=active_file)
        
    if command == "👀 Take a Look":
        while True:
            res = take_look(history, pointer, function_dict, cursor, config=style)
            if res != None:
                copy = res
            turn_page(logo, symbol, interval, logo_color=logo_color, active_color=active_file)
            skip(pointer, config=style)
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
