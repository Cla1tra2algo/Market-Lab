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


    if not open_times:
        raise ValueError("There is no data to plot.")

    if status is not None:
        rows = cursor.execute(f'''SELECT "{status}" FROM status ORDER BY open_time''').fetchall()
        status_list = [row[0] for row in rows]

        for i, current_status in enumerate(status_list[:len(open_times)]):
            value = values_list[0][i]
            if current_status is None or value is None:
                continue
            if current_status > 0:
                plt.scatter(x=i, y=value * 1.1, marker="^", c="red", s=50, alpha=0.5)
            elif current_status < 0:
                plt.scatter(x=i, y=value * 0.9, marker="v", c="blue", s=50, alpha=0.5)

    for i in range(nb):
        plt.plot(np.array(values_list[i]), label=values[i])

    plt.legend()
    plt.grid(True)
    plt.show()
