import sqlite3 
import math_formula as mf

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from scipy.signal import savgol_filter


def filter_application(cursor, data):

    print("\r" + " " * 80, end="\r")

    print("Filter Application")

    cursor.execute(f"""
        SELECT open_time, {data}
        FROM candles
        WHERE {data} IS NOT NULL
        ORDER BY open_time
    """)

    rows = cursor.fetchall()

    if not rows:
        raise ValueError("Aucune donnée VWEMA disponible.")

    open_times = [row[0] for row in rows]
    vwema_values = np.array(
        [row[1] for row in rows],
        dtype=float
    )

    window_length = 51
    polyorder = 3

    if len(vwema_values) < window_length:
        raise ValueError(
            f"Série trop courte pour savgol_filter : "
            f"{len(vwema_values)} < {window_length}"
        )

    filtered = savgol_filter(
        vwema_values,
        window_length=window_length,
        polyorder=polyorder
    )

    cursor.executemany("""
        UPDATE candles
        SET vwema_savgol = ?
        WHERE open_time = ?
    """,
    list(zip(filtered.tolist(), open_times)))

    cursor.connection.commit()

    print("\r" + " " * 80, end="\r")
    print("Filter Applied", end="\r")


def general_application(cursor, name, after_name, function, window, parameters):

    window = int(window)
    cursor.execute("PRAGMA table_info(candles)")

    columns = [c[1] for c in cursor.fetchall()]


    if after_name is True :
        after_name = ""

        for i in range(len(parameters)):
            after_name += f"_{parameters[i]}"

    else:
        after_name = ""

    if window > 1:
        name = name + after_name + "_" + str(window)

    else:
       name = name + after_name  

    if not mf.column_exists(cursor, "candles", name):

        cursor.execute(f"""
            ALTER TABLE candles 
            ADD COLUMN {name} REAL
    """)

    rows = np.array([])
    mat = []

    for i in range(len(parameters)):

        data = None

        cursor.execute(f"""
            SELECT {parameters[i]}
            FROM candles
            ORDER BY open_time
        """)

        data = cursor.fetchall()

        data = np.array([r[0] for r in data])
        mat.append(data)

    rows = np.array(mat)

    cursor.execute(f"""
    SELECT open_time
    FROM candles
    ORDER BY open_time
    """)

    open_times = cursor.fetchall()
    open_times = [o[0] for o in open_times]

    total = len(open_times)

    results = []

    windows_array = []

    for r in range(len(parameters)): # Calcul des fenetres pour tous les parametres
        windows_list = np.array(sliding_window_view(rows[r], window)) # contient toutes les fenetres
        windows_array.append(windows_list) 

    windows_array = np.array(windows_array)


    for i in range(len(windows_array[0])):  #boucle pour faire passer toutes les fenetres

        data_s = []

        for n in range(len(windows_array)): #boucle pour prendre toutes les fenetres[i] de tous les params
            data_s.append(windows_array[n][i])

        data_s = np.array(data_s)

        func_return = str(function(data_s))

        if func_return != "None":
            results.append((float(func_return), open_times[window+i - 1]))


        if type(data_s[-1]) != str :
            data_s = np.append(data_s, func_return)
        else:
            data_s[-1] = func_return
        
        print(
            f"computed {name} : {100*(i+1)/(total-window+1):.1f} %                                   ",
            end="\r"
        )

    cursor.executemany(f"""
    UPDATE candles
    SET {name} = ?
    WHERE open_time = ?
    """, results)



def general_application_inbetter(cursor, name, function, window, **kwargs):

    after_name = ""
    parameters = list(kwargs.values())



    if name != ("ema" or "atr" or "rsi" or "sma"):

        for i in range(len(kwargs)):
            after_name += f"_{parameters[i]}"
        if window > 1:
            name = name + after_name + "_" + str(window)

        else:
            name = name + {after_name}

    else : 
        if parameters[0] != "close":
            name = name + "_" + parameters[0]
        if window > 1 :
            name += "_" + str(window)
        

    if not mf.column_exists(cursor, "candles", name):

        cursor.execute(f"""
            ALTER TABLE candles 
            ADD COLUMN {name} REAL
    """)

    rows = np.array([])
    mat = []

    for i in range(len(parameters)):

        data = None

        cursor.execute(f"""
            SELECT {parameters[i]}
            FROM candles
            ORDER BY open_time
        """)

        data = cursor.fetchall()

        data = np.array([r[0] for r in data])
        mat.append(data)

    rows = np.array(mat)

    cursor.execute(f"""
    SELECT open_time
    FROM candles
    ORDER BY open_time
    """)

    open_times = cursor.fetchall()
    open_times = [o[0] for o in open_times]

    total = len(open_times)

    results = []

    windows_array = []

    for r in range(len(parameters)): # Calcul des fenetres pour tous les parametres
        windows_list = np.array(sliding_window_view(rows[r], window)) # contient toutes les fenetres
        windows_array.append(windows_list) 

    windows_array = np.array(windows_array)


    for i in range(len(windows_array[0])):  #boucle pour faire passer toutes les fenetres

        data_s = []

        for n in range(len(windows_array)): #boucle pour prendre toutes les fenetres[i] de tous les params
            data_s.append(windows_array[n][i])

        data_s = np.array(data_s)

        func_return = str(function(data_s))

        if func_return != "None":
            results.append((float(func_return), open_times[window+i - 1]))


        if type(data_s[-1]) != str :
            data_s = np.append(data_s, func_return)
        else:
            data_s[-1] = func_return
        
        print(
            f"computed {name} : {100*(i+1)/(total-window+1):.1f} %                                   ",
            end="\r"
        )

    cursor.executemany(f"""
    UPDATE candles
    SET {name} = ?
    WHERE open_time = ?
    """, results)
