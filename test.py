import stat_making as sm
import sqlite3
import matplotlib.pyplot as plt
import math_formula as mf
import applications as app
import event as ev


firt_timestamp = 1502942400000

conn = sqlite3.connect("data_BTCUSDT_12h")
cursor = conn.cursor()

ev.over_under(cursor, data = ["sma_close_50", "sma_close_100"])

conn.close()
