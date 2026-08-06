import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import math_formula as mf



def plot(cursor, values, status):

    values_list = []
    nb = len(values)
    

    for i in range(nb):
        cursor.execute(f"""
        SELECT {values[i]}
        FROM candles
        ORDER BY open_time
        """)

        rows = cursor.fetchall()
        values_list.append([row[0] for row in rows])

   
    cursor.execute(f"""
    SELECT open_time
    FROM candles
    ORDER BY open_time
    """)

    rows = cursor.fetchall()
    open_times = [row[0] for row in rows]


    if status != None :
        nb_status = len(status)
        for n in range(nb_status):
            for i in range(len(open_times)):
                if values_list[0][i] is None :
                    continue
                if status[n] > 0:
                    plt.scatter(x=i, y= values_list[0][i]+ values_list[0][i]*0.1, marker="^", c="red", s=50, alpha=0.5)
                if status[n] < 0:
                    plt.scatter(x=i, y= values_list[0][i]- values_list[0][i]*0.1, marker="^", c="blue", s=50, alpha=0.5)

    for i in range(nb):
        plt.plot(np.array(values_list[i]), label=values[i])

    plt.legend()
    plt.grid(True)
    plt.show()