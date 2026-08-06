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

style = questionary.Style([("question", questions_color), ("answer", questions_color)])


function_dict = {
    "sma" : (mf.sma, 1, ["close", "high", "low", "open", "volume"]),
    "ema" : (mf.ema, 1, ["open", "close", "low", "high"]),
    "atr" : (mf.atr, 3, ["open", "high", "low"]),
    "rsi" : (mf.rsi, 2),
    "vwma" : (mf.vwma, 2, "open", "volume"),
    "amplitude" : (mf.amplitude, 2),
    "relative" : (mf.amplitude, 2)
}
function_list = list(function_dict.keys())

values_list = []

print("")
questionary.print(logo, style=logo_color)
print("")


conn, cursor, source, symbol, interval = data_base(pointer, logo, config=style, err_color=err_color)

history = []

while True :

    command = questionary.select("Actions : ", 
                                choices = [
                                "📁 Change or Create a DataBase",
                                "💾 Download Data",
                                "📈 Calculate Indicators",
                                "📊 Calculate Stats",
                                "📉 Plot",
                                "🗑️  Delete Column", 
                                "📘 History",
                                "⚙️  Settings",
                                "👀 Take a Look",
                                "🚪 Exit"], pointer="▶︎").ask()

    print(""*80, end="\r")

    if command == "📁 Change or Create a DataBase":

        conn.commit()
        conn.close()

        data_base(pointer, logo, err_color=err_color, config=style)

        skip(pointer, config=style)
        turn_page(logo, symbol, interval, source, active_color=active_file, logo_color=logo_color)
        

    if command == "💾 Download Data":
        download_data(cursor, symbol, interval, source, timestamp, conn, history)
        res = skip(pointer, config=style)
        turn_page(logo, symbol, interval, source, logo_color, active_color=active_file)



    if command == "📈 Calculate Indicators":
        while True:
            calculate_indic(function_dict=function_dict, 
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
            turn_page(logo, symbol, interval, source, logo_color=logo_color, active_color=active_file)
            if res == "Yes":
                break
        
    if command == "📊 Calculate Stats":
        command = questionary.select("Number of Variables : ",
                                     choices=[
                                         "1 variable",
                                         "2 variables (heatmap)"
                                     ]).ask()

    if command == "📉 Plot":

        while True : 
            print(""*80, end="\r")
            print("📉 Plot")
            print(" ")

            plot_indic(cursor, err_color=err_color, pointer=pointer)
            res = skip(pointer, config=style)
            turn_page(logo, symbol, interval, source, logo_color, active_color=active_file)
            if res == "Yes":
                break

        
    if command == "🗑️  Delete Column":
        while True:
            delete_col(cursor, history, symbol, interval, source, pointer, config=style)
            conn.commit()
            res = skip(pointer, config=style)
            turn_page(logo, symbol, interval, source, logo_color=logo_color, active_color=active_file)
            if res == "Yes":
                break
        
    if command == "📘 History":
        while True:
            action_history(history)
            res = skip(pointer, config=style)
            turn_page(logo, symbol, interval, source, logo_color=logo_color, active_color=active_file)
            if res == "Yes":
                break
        
    if command == "👀 Take a Look":
        while True:
            res = take_look(history, pointer, function_dict, cursor, config=style)
            if res != None:
                copy = res
            turn_page(logo, symbol, interval, source, logo_color=logo_color, active_color=active_file)
            skip(pointer, config=style)
            break

    if command == "🚪 Exit":
        rep = yes_no("Do you really wanna leave MARKET LAB ?", pointer, config=style)

        if rep == "Yes":
            questionary.print("Leaving MARKET LAB", style="fg:red")
            break

        else:
            print(""*80, end="\r")


