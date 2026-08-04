import sqlite3
import matplotlib.pyplot as plt

import math_formula as mf

conn = sqlite3.connect("data_BTCUSDT_12h")
cursor = conn.cursor()



cursor.execute("""
SELECT sma_close_50, sma_close_100, close, status_under_over, open_time
FROM candles
ORDER BY open_time
""")

rows = cursor.fetchall()


data_1 = [row[0] for row in rows]
data_2 = [row[1] for row in rows]
data_3 = [row[2] for row in rows] 
data_4 = [row[3] for row in rows]
open_times = [row[4] for row in rows]


for i in range(len(open_times)):
    if data_1[i] is None or data_2[i] is None:
        continue
    if data_4[i] > 0:
        plt.scatter(x=i, y=data_1[i]+data_1[i]*0.1, marker="^", c="red", s=50, alpha=0.5)
    if data_4[i] < 0:
        plt.scatter(x=i, y=data_1[i]-data_1[i]*0.1, marker="^", c="blue", s=50, alpha=0.5)

plt.plot(data_1, label="SMA Close 50", color = "red")
plt.plot(data_2, label="SMA Close 100", color = "blue")
plt.plot(data_3, label="BTCUSDT", color = "black")



plt.legend()
plt.grid(True)



plt.show()