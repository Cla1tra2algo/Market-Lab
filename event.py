import numpy as np
from scipy.signal import *
import math_formula as mf
from math_formula import *
from numpy.lib.stride_tricks import sliding_window_view
from questionary import *

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return column in {row[1] for row in cursor.fetchall()}

def _isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def peaks_detection(cursor, parameters, name):

    if column_exists(cursor, "status", name) is False:
        cursor.execute(f"ALTER TABLE status ADD COLUMN {name}")
    else:
        cursor.execute(f"ALTER TABLE status DROP COLUMN {name}")
        cursor.execute(f"ALTER TABLE status ADD COLUMN {name}")

    prominence_para = float(parameters[0])

    data = parameters[1]

    rows = cursor.execute(f"""
        SELECT open_time, {data}
        FROM candles 
        WHERE {data} IS NOT NULL
        ORDER BY open_time"""
    ).fetchall()

    open_times = [row[0] for row in rows]
    values = np.array([row[1] for row in rows], dtype=float)


    peaks_table = find_peaks(values, prominence=prominence_para)[0]
    lows_table = find_peaks(-values, prominence=prominence_para)[0]


    # Création de la liste des statuts
    status = [0] * len(open_times)

    # Marquage des maxima

    for  index in range(len(peaks_table)):
        status[peaks_table[index]] = 1

    # Marquage des minima

    for index in range(len(lows_table)):

        status[lows_table[index]] = -1

    # Vérification de cohérence
    assert len(status) == len(open_times), \
        "The number of status does not corresponds to the number of candles."
    
    # Préparation des données

    data = list(zip(status,open_times))

    print(f"Applying peaks detection with prominence: {prominence_para} on {data}... ")

    cursor.executemany(f"""
    UPDATE status
    SET {name} = ?
    WHERE open_time = ?
    """, data)
    cursor.connection.commit()

def cross(data, window_opentimes, open_times):

    values1_window = list(data[0])
    values2_window = list(data[1])

    corresponding_index_over = [] # récupération de l'index de l'open_time dans la liste des open times
    corresponding_index_under = [] # récupération de l'index de l'open_time dans la liste des open times

    for i in range(len(open_times)):

        if i == 0:
            continue

        if values1_window[i-1] is not None and values2_window[i-1] is not None and values1_window[i] is not None and values2_window[i] is not None and values1_window[i-1] < values2_window[i-1] and values2_window[i] < values1_window[i]:
            corresponding_opentime = window_opentimes[i] # récupération de l'open_time qui correspond a la valeur max
            corresponding_index_over.append(list(open_times).index(corresponding_opentime)) # récupération de l'index de l'open_time dans la liste des open times

        elif values1_window[i-1] is not None and values2_window[i-1] is not None and values1_window[i] is not None and values2_window[i] is not None and values1_window[i-1] > values2_window[i-1] and values2_window[i] > values1_window[i]:
            corresponding_opentime = window_opentimes[i] # récupération de l'open_time qui correspond a la valeur min
            corresponding_index_under.append(list(open_times).index(corresponding_opentime)) # récupération de l'index de l'open_time dans la liste des open times


    return (corresponding_index_over, 1), (corresponding_index_under, -1)

def over_under(data, window_opentimes, open_times):

    values1_window = list(data[0])
    values2_window = list(data[1])

    corresponding_index_over = [] # récupération de l'index de l'open_time dans la liste des open times
    corresponding_index_under = [] # récupération de l'index de l'open_time dans la liste des open times

    for i in range(len(open_times)):

        if values1_window[i] is not None and values2_window[i] is not None and values1_window[i] > values2_window[i]:
            corresponding_opentime = window_opentimes[i]                             # récupération de l'open_time qui correspond a la valeur max
            corresponding_index_over.append(list(open_times).index(corresponding_opentime)) # récupération de l'index de l'open_time dans la liste des open times

        elif values1_window[i] is not None and values2_window[i] is not None and values1_window[i] < values2_window[i]:
            corresponding_opentime = window_opentimes[i]                             # récupération de l'open_time qui correspond a la valeur min
            corresponding_index_under.append(list(open_times).index(corresponding_opentime)) # récupération de l'index de l'open_time dans la liste des open times


    return (corresponding_index_over, 1), (corresponding_index_under, -1)

def highest_lowest(data, window_opentimes, open_times):

    values_window = list(data[0])

    id = list(values_window).index(max(values_window))                           # récupération de l'index de la plus grande valeur

    corresponding_opentime = window_opentimes[id]                                # récupération de l'open_time qui correspond a la valeur max
    
    corresponding_index_highest = list(open_times).index(corresponding_opentime) # récupération de l'index de l'open_time dans la liste des open times
    

    id = list(values_window).index(min(values_window)) # récupération de l'index de la plus grande valeur
    corresponding_opentime = window_opentimes[id]      # récupération de l'open_time qui correspond a la valeur max
        
    corresponding_index_lowest = list(open_times).index(corresponding_opentime) # récupération de l'index de l'open_time dans la liste des open times

    return ([corresponding_index_highest], 1), ([corresponding_index_lowest], -1)


base_event_dict = {
    "cross" : (cross, 2, ["sma"], "general_app"),
    "highest_lowest" : (highest_lowest, 1, ["close"], "general_app"),
    "over_under" : (over_under, 2, ["close", "sma"], "general_app"),
    "peaks_detection" : (peaks_detection, 
                         2, 
                         [("Select a prominence: ", lambda value, parameter_list: True if _isfloat(value) else print("❌ The prominence must be a float.")),
                          ("Select a parameter: " , lambda value, parameter_list: True if value in parameter_list else print(f"❌ The parameter must be one of the following: {parameter_list}"))],
                         "custom")
}



