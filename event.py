import numpy as np
from scipy.signal import *
import math_formula as mf
from math_formula import *
from numpy.lib.stride_tricks import sliding_window_view


def peaks_detection(cursor, prominence_para):

    rows = cursor.execute("""
        SELECT open_time, vwema_savgol
        FROM candles 
        WHERE vwema_savgol IS NOT NULL
        ORDER BY open_time"""
    ).fetchall()

    open_times = [row[0] for row in rows]
    values = np.array([row[1] for row in rows], dtype=float)

    peaks_table = find_peaks(values, prominence=prominence_para)[0]

    lows_table = find_peaks( -values, prominence=prominence_para)[0]

    # Création de la liste des statuts
    statut = [0] * len(open_times)


    # Marquage des maxima

    for  index in range(len(peaks_table)):
        statut[peaks_table[index]] = 100


    # Marquage des minima

    for index in range(len(lows_table)):

        statut[lows_table[index]] = -100

    # Vérification de cohérence
    assert len(statut) == len(open_times), \
        "Le nombre de statuts ne correspond pas au nombre de bougies."
    
    # Préparation des données

    data = list(zip(statut,open_times))

    cursor.executemany("""
    UPDATE candles
    SET statut = ?
    WHERE open_time = ?
    """, data)
    cursor.connection.commit()

def cross(cursor, data):
    cursor.execute(f"SELECT \"{data[0]}\", \"{data[1]}\", open_time FROM candles ORDER BY open_time")

    rows = cursor.fetchall()

    data_1 = [d[0] for d in rows]
    data_2 = [d[1] for d in rows]
    open_times = [d[2] for d in rows]    

    status = [0] * len(open_times)

    for i in range(len(data_1)):

        if i == 0:
            continue

        if data_1[i] is not None and data_1[i-1] is not None and data_2[i] is not None and data_2[i-1] is not None:
            prev_diff = data_1[i-1]-data_2[i-1]
            diff = data_1[i]-data_2[i]

            if prev_diff < 0 < diff:
                status[i] = 1

            elif prev_diff > 0 > diff :
                status[i] = -1

        else :
            status[i] = 0


    results = list(zip(status, open_times))

    name = f"cross_{data[0]}_{data[1]}"

    if not mf.column_exists(cursor, "status", name):
        cursor.execute(f"""
            ALTER TABLE status
            ADD COLUMN \"{name}\"
    """)

    cursor.connection.commit()

    cursor.executemany(f"""
        UPDATE status
        SET \"{name}\" = ?
        WHERE open_time = ?
    """, results)

    cursor.connection.commit()

def over_under(cursor, data):

    cursor.execute(f"""
    SELECT {data[0]}, {data[1]}, open_time
    FROM candles
    ORDER BY open_time
""")

    rows = cursor.fetchall()

    data_1 = [r[0] for r in rows]
    data_2 = [r[1] for r in rows]
    open_times = [r[2] for r in rows]

    nb = len(open_times)

    status = [0] * nb

    for i in range(nb):
        if data_1[i] is None or data_2[i] is None:
            continue
        if data_1[i]-data_2[i] > 0:
            status[i] = 1

        elif data_1[i]-data_2[i] < 0:
            status[i] = -1

    results = list(zip(status, open_times))

    if mf.column_exists(cursor,"status", "status_under_over") is False:
        cursor.execute("""
            ALTER TABLE status
            ADD COLUMN status_under_over
        """)

    cursor.executemany("""
        UPDATE status
        SET status_under_over = ?
        WHERE open_time = ?
    """, results)

    cursor.connection.commit()

def highest_lowest(cursor, data):

    window = int(data[1])

    if window < 1 or len(rows := cursor.execute(f"""
                SELECT {data[0]}, open_time
                FROM candles
                ORDER BY open_time
                """).fetchall()) < window:
        raise ValueError("The window size must not exceed the number of candles.")

    values_list = [r[0] for r in rows]
    open_times = [r[1] for r in rows]

    nb = len(open_times)

    windows_list = np.array(sliding_window_view(values_list, window))
    
    window_opentimes = np.array(sliding_window_view(open_times, window))

    status = [0] * nb

    for i in range(len(windows_list)):
        
       
        id = list(windows_list[i]).index(max(windows_list[i]))
        corresponding_opentime = window_opentimes[i][id]
        
        corresponding_index = list(open_times).index(corresponding_opentime)

        status[int(corresponding_index)] = 1


        id = list(windows_list[i]).index(min(windows_list[i]))

        corresponding_opentime = window_opentimes[i][id]
        
        corresponding_index = list(open_times).index(corresponding_opentime)


        status[int(corresponding_index)] = -1
        
    results = list(zip(status, open_times))

    if mf.column_exists(cursor, "status", "highest_lowest") is False:
        cursor.execute("""
            ALTER TABLE status
            ADD COLUMN highest_lowest""")

        cursor.connection.commit()

    cursor.executemany("UPDATE status SET highest_lowest = ? WHERE open_time = ?", results)
    cursor.connection.commit()

