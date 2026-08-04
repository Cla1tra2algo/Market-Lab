import math_formula as mf
import event as ev
import stat_making as sm
import applications as app
import sqlite3

function_dict = {
    "sma" : mf.sma,
    "ema" : mf.ema,
    "atr" : mf.atr,
    "rsi" : mf.rsi,
    "vwma" : mf.vwma,
    "amplitude" : mf.amplitude

}

values_list = []


symbol = input("Symbol : ")
interval = input("Interval :")

symbol = symbol.upper() + "USDT"

conn = sqlite3.connect(f"data_{symbol}_{interval}")

cursor = conn.cursor()

command = input("Command : ")




if command == "cursor" :

    new_database = ("Enter in :")

    cursor.commit()
    conn.close()

    conn = sqlite3.connect(new_database)
    cursor = conn.cursor


if command == "indicator" :

    name = input("Name : ")

    after_name = input("Adding an After Name ? : ")

    try :
        after_name = bool(after_name)

    except ValueError:
        print("You must enter a bool value (True or False)")


    function_ = input("Function : ")

    if (function_ is function_dict) == False  :
        print(f"{function_} does not exist in the function dictionary. Code and add it in the function dictionnary to use it.")
        function_ = input("Function : ")

    else: 
        function = function_dict[function]


    window = input("Window :")

    try:
        window = int(window)

    except ValueError:
        print("You must enter an inter greater than 0")


    paramters = []
    while True :

        new_paramters = input("Parameters : ")

        if new_paramters in values_list :
            paramters += new_paramters
            continue

        else :
            print("This parameter does not exist. Compute it to use it. Command 'parameters' to see all parameters.")
        if new_paramters is None :
            break

    app.general_application(cursor, "name", after_name, function, window, paramters)


if command == "plot":

    after_command = input("Plot command : ")

    if after_command == "stat":
        after_command = input("number of var : ")


    
