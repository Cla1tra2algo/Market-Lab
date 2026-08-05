import math_formula as mf
import event as ev
import stat_making as sm
import applications as app
import sqlite3
import data_extraction as de
from datetime import *
import questionary 
from commands import *

start = datetime(2017, 8, 17)             # limites temporelles de l'exctraction des donnés 
timestamp = int(start.timestamp() * 1000)
erase = "\033[F\033[K"
pointer = "▶︎"
logo = """ 
    ╔╦╗╔═╗╦═╗╦╔═╔═╗╔╦╦══════════╗
    ║║║╠═╣╠╦╝╠╩╗║╣  ║  ╦  ╔═╗╔╗       
    ╩ ╩╩ ╩╩╚═╩ ╩╚═╝ ╩  ║  ╠═╣╠╩╗   
  ╚════════════════════╩═╝╩ ╩╚═╝    """

copy = None


logo_color = "fg:pink"
questions_color = "fg:blue"
answers_color = "fg:orange"
err_color = "fg:red"
activ_file = "fg:yellow"


function_dict = {
    "sma" : (mf.sma, 1),
    "ema" : (mf.ema, 1),
    "atr" : (mf.atr, 1),
    "rsi" : (mf.rsi, 2),
    "vwma" : (mf.vwma, 2),
    "amplitude" : (mf.amplitude, 2)
}
function_list = list(function_dict.keys())

values_list = []

print(" ")
questionary.print(logo, style=logo_color)
print("")


conn, cursor, source, symbol, interval = data_base(erase, pointer, logo)

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

    print(erase)

    if command == "📁 Change or Create a DataBase":

        conn.commit()
        conn.close()

        data_base(erase, pointer, logo)

        print("")
        questionary.print(f"Working on {symbol} {interval} From {source}", style="fg:yellow")


    if command == "💾 Download Data":
        download_data(cursor, symbol, interval, source, timestamp, erase, conn, history)
        res = skip(erase, pointer)
        turn_page(logo, symbol, interval, source)


    if command == "📈 Calculate Indicators":
        while True:
            calculate_indic(erase, function_dict, function_list, cursor, history, symbol, interval, pointer=pointer)
            res = skip(erase, pointer)
            turn_page(logo, symbol, interval, source)
            if res == "Yes":
                break
        
    if command == "📊 Calculate Stats":
        command = questionary.select("Number of Variables : ",
                                     choices=[
                                         "1 variable",
                                         "2 variables (heatmap)"
                                     ]).ask()

    if command == "📉 Plot":

        print(erase, end="")
        print("📉 Plot")

        after_command = input("Plot command : ")

        if after_command == "stat":
            after_command = input("number of var : ")

    if command == "🗑️  Delete Column":
        while True:
            delete_col(erase, cursor, history, symbol, interval, source, pointer)
            conn.commit()
            res = skip(erase, pointer)
            turn_page(logo, symbol, interval, source)
            if res == "Yes":
                break
        
    if command == "📘 History":
        while True:
            action_history(erase, history, pointer)
            res = skip(erase, pointer)
            turn_page(logo, symbol, interval, source)
            if res == "Yes":
                break
        
    if command == "👀 Take a Look":
        while True:
            res = take_look()
            if res != None:
                copy = res
            turn_page(logo, symbol, interval, source)
            break



    if command == "🚪 Exit":
        rep = yes_no("Do you really wanna leave MARKET LAB ?", pointer)

        if rep == "Yes":
            questionary.print("Leaving MARKET LAB", style="fg:red")
            break

        else:
            print(erase, end="")


