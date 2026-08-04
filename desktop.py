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
print(" ")
questionary.print("I--I MARKET LAB I--I", style="fg:pink")
print("")


conn, cursor, source, symbol, interval = data_base(erase)

print("")
questionary.print(f"Working on {symbol} {interval} From {source}", style="fg:yellow")
print("")

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
                                "❌ Exit"]).ask()

    print(erase)

    if command == "📁 Change or Create a DataBase":

        data_base()

        print("")
        questionary.prin(f"Working on {symbol} {interval} From {source}", style="fg:yellow")

        cursor.commit()
        conn.close()

    if command == "💾 Download Data":
        download_data(cursor, symbol, interval, source, timestamp, erase, conn, history)

    if command == "📈 Calculate Indicators":
        calculate_indic(erase, function_dict, function_list, cursor, history, symbol, interval)
    
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
        delete_col(erase, cursor)
        

    if command == "📘 History":
        print(erase, end="")
        print("📖 History")
        if len(history) == 0:
            print("The Action History is empty")
            skip()
        else:
            print(history)
            skip()

    if command == "❌ Exit":
        rep = yes_no("Do you really wanna leave MARKET LAB ?")

        if rep == "Yes":
            questionary.print("Leaving MARKET LAB", style="fg:red")
            break

        else:
            print(erase, end="")

 
