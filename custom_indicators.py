"""Personal Market Lab indicators and events.

Only load code that you wrote or trust: this file is executed by Market Lab.
"""


def median_price(data):
    """Return the midpoint of the latest high and low values."""
    high = data[0]
    low = data[1]
    return (high[-1] + low[-1]) / 2


def close_above_open(cursor, columns):
    """Create a status equal to 1 when close is above open, otherwise 0."""
    close_column, open_column = columns
    rows = cursor.execute(
        f"SELECT open_time, \"{close_column}\", \"{open_column}\" FROM candles ORDER BY open_time"
    ).fetchall()

    status_columns = {row[1] for row in cursor.execute("PRAGMA table_info(status)")}
    if "close_above_open" not in status_columns:
        cursor.execute("ALTER TABLE status ADD COLUMN close_above_open")
    cursor.executemany(
        "UPDATE status SET close_above_open = ? WHERE open_time = ?",
        [(int(close > open_), open_time) if close is not None and open_ is not None else (0, open_time)
         for open_time, close, open_ in rows],
    )
    cursor.connection.commit()


indicator_dict = {
    "median_price": (median_price, 2, ["high", "low"]),
}

event_dict = {
    "close_above_open": (close_above_open, 2, ["close", "open"]),
}
