import sqlite3 
import math_formula as mf
import json as js

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from scipy.signal import savgol_filter

def general_application(cursor, name, function, window, parameters, last_timestamp):

    window = int(window)
    cursor.execute("PRAGMA table_info(candles)")

    if not mf.column_exists(cursor, "candles", name):

        cursor.execute(f"""
            ALTER TABLE candles 
            ADD COLUMN {name} REAL
    """)

        cursor.connection.commit()

    else:
        cursor.execute(f"""
            ALTER TABLE candles
            DROP COLUMN {name}""")

        cursor.connection.commit()

        cursor.execute(f"""
            ALTER TABLE candles 
            ADD COLUMN {name} REAL
    """)
        cursor.connection.commit()


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indicators_metadata(
        column_name TEXT PRIMARY KEY,
        function_name TEXT,
        parameters TEXT
        )
""")

    cursor.connection.commit()
    
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

    if not parameters:
        raise ValueError("Select at least one parameter.")
    if total < window:
        raise ValueError(
            f"Not enough candles for a window of {window}. Available candles: {total}."
        )

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


    json_para = js.dumps(parameters)

    cursor.execute(f"""
        INSERT INTO indicators_metadata (column_name, function_name, parameters)
        VALUES (?, ?, ?)
""", (name, function.__name__, json_para))


def ganeral_event_application(cursor, name,function, window, data):

    nb_open_times = cursor.execute("SELECT COUNT(*) FROM candles").fetchone()[0]


    if not mf.column_exists(cursor, "candles", name):

        cursor.execute(f"""
            ALTER TABLE candles 
            ADD COLUMN {name} REAL
    """)

    else:
        cursor.execute(f"""
            ALTER TABLE status
            DROP COLUMN {name}""")

    
    if window < 1 or len(rows := cursor.execute(f"""
                SELECT {data[0]}, open_time
                FROM candles
                ORDER BY open_time
                """).fetchall()) < window:
        raise ValueError("The window size must not exceed the number of candles.")

    rows = []

    for i in range(len(data)):

        data_list = cursor.execute(f"""
                SELECT {data[i]}
                FROM candles
                ORDER BY open_time
        """).fetchall()

        rows.append([r[0] for r in data_list])

    nb_category_of_values = len(rows)

    open_times = cursor.execute("SELECT open_time FROM candles ORDER BY open_time").fetchall()

    open_times = [r[0] for r in open_times]

    windows_list = []

    for i in range(len(rows)):
        windows_list.append(np.array(sliding_window_view(rows[i], window)))

    window_opentimes = np.array(sliding_window_view(open_times, window))

    status = [0] * nb_open_times

    for i in range(len(windows_list[0])):
        values_list = []
        for n in range(nb_category_of_values):
            
            values_list.append(windows_list[n][i])

        rep = function(list(values_list), list(window_opentimes[i]), open_times)
 
        for n in range(len(rep)):
            for j in range(len(rep[n][0])):
                status[rep[n][0][j]] = rep[n][1]

    cursor.execute(f"""ALTER TABLE status 
                   ADD COLUMN {name}""")
    cursor.connection.commit()

    results = list(zip(status, open_times))

    cursor.executemany(f"UPDATE status SET {name} = ? WHERE open_time = ?", results)
    cursor.connection.commit()


