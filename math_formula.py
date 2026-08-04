from math import *
import numpy as np
from scipy.signal import find_peaks


def vwema(data):
    sum  = 0.
    sumv = 0.
    sump = 0.
    p    = 1.5

    vol = data[0]
    price = data[1]

    for i in range(vol.size):
        sumv += vol[i] 

    for i in range(len(vol)):
        sump += vol[i]**p

    sump = sump/sumv

    for i in range(len(vol)) : 
        w = vol[i]**p / sumv #calcul de la taille du vol par rapport a sumv
        sum += price[i]*w    # plus la taille du vol est grande plus le poid dans la moyenne est important 

    result = sum/sump
    d = price[-1] - result

    return d 

def correlation(x, y):
    moy_x = sum(x)/len(x)
    moy_y = sum(y)/len(y)

    sig_x = 0.
    for i in range(len(x)) :
        sig_x += (x[i] - moy_x)**2

    sig_x /= len(x)
    sig_x = sqrt(sig_x)

    sig_y = 0.
    for i in range(len(y)) :
        sig_y += (y[i] - moy_y)**2

    sig_y /= len(y)
    sig_y = sqrt(sig_y)

    conv = 0.
    
    for i in range(len(x)):
        conv += (x[i] - moy_x) * (y[i] - moy_y)

    conv /= len(x)

    r = conv / (sig_x*sig_y)

    return r

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return column in {row[1] for row in cursor.fetchall()}

def peaks_data(cursor, prominence_para):

    rows = cursor.execute("""
        SELECT open_time, vwema_savgol
        FROM candles 
        WHERE vwema_savgol IS NOT NULL
        ORDER BY open_time"""
    ).fetchall()

    open_times = [row[0] for row in rows]
    values = np.array([row[1] for row in rows], dtype=float)

    peaks_table, peaks_properties = find_peaks(values, prominence=prominence_para, 
                             height=(None, None), 
                             distance=(None, None), 
                             width=(None, None),
                             wlen=(None, None), 
                             rel_height=(None, None),
                             plateau_size=(None, None)
                            )

    lows_table, lows_properties = find_peaks(values, prominence=prominence_para, 
                             height=(None, None), 
                             distance=(None, None), 
                             plateau_size=(None, None)
                            )

    # Création de la liste des statuts
    statut = [0] * len(open_times)

    peak_height   = [0.0] * len(values)

    prominence    = [0.0] * len(values)
    left_base     = [0] * len(values)
    right_base    = [0] * len(values)

    width         = [0.0] * len(values)
    width_height  = [0.0] * len(values)
    left_ip       = [0.0] * len(values)
    right_ip      = [0.0] * len(values)

    plateau_size  = [0] * len(values)
    left_edge     = [0] * len(values)
    right_edge    = [0] * len(values)

    # Marquage des maxima

    for i, index in enumerate(peaks_table):

        statut[index] = 100

        peak_height[index]  = peaks_properties["peak_heights"][i]

        prominence[index]   = peaks_properties["prominences"][i]
        left_base[index]    = peaks_properties["left_bases"][i]
        right_base[index]   = peaks_properties["right_bases"][i]

        width[index]        = peaks_properties["widths"][i]
        width_height[index] = peaks_properties["width_heights"][i]
        left_ip[index]      = peaks_properties["left_ips"][i]
        right_ip[index]     = peaks_properties["right_ips"][i]

        plateau_size[index] = peaks_properties["plateau_sizes"][i]
        left_edge[index]    = peaks_properties["left_edges"][i]
        right_edge[index]   = peaks_properties["right_edges"][i]

    # Marquage des minima

    for i, index in enumerate(lows_table):

        statut[index] = -100

        peak_height[index]  = - lows_properties["peak_heights"][i]
        prominence[index]   = lows_properties["prominences"][i]
        left_base[index]    = lows_properties["left_bases"][i]
        right_base[index]   = lows_properties["right_bases"][i]

        width[index]        = lows_properties["widths"][i]
        width_height[index] = lows_properties["width_heights"][i]
        left_ip[index]      = lows_properties["left_ips"][i]
        right_ip[index]     = lows_properties["right_ips"][i]

        plateau_size[index] = lows_properties["plateau_sizes"][i]
        left_edge[index]    = lows_properties["left_edges"][i]
        right_edge[index]   = lows_properties["right_edges"][i]

    # Vérification de cohérence
    assert len(statut) == len(open_times), \
        "Le nombre de statuts ne correspond pas au nombre de bougies."
    

    # Préparation des données

    columns = {
        "statut": "INTEGER",
        "peak_height": "REAL",
        "prominence": "REAL",
        "left_base": "INTEGER",
        "right_base": "INTEGER",
        "width": "REAL",
        "width_height": "REAL",
        "left_ip": "REAL",
        "right_ip": "REAL",
        "plateau_size": "INTEGER",
        "left_edge": "INTEGER",
        "right_edge": "INTEGER",
    }

    cursor.execute("PRAGMA table_info(candles)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    for name, sql_type in columns.items():
        if name not in existing_columns:
            cursor.execute(f"""
            ALTER TABLE candles
            ADD COLUMN {name} {sql_type}
            """)

    data = list(zip(
    statut,
    peak_height,
    prominence,
    left_base,
    right_base,
    width,
    width_height,
    left_ip,
    right_ip,
    plateau_size,
    left_edge,
    right_edge,
    open_times
    ))

    cursor.executemany("""
    UPDATE candles
    SET
        statut = ?,
        peak_height = ?,
        prominence = ?,
        left_base = ?,
        right_base = ?,
        width = ?,
        width_height = ?,
        left_ip = ?,
        right_ip = ?,
        plateau_size = ?,
        left_edge = ?,
        right_edge = ?
    WHERE open_time = ?
    """, data)

    cursor.connection.commit()

def sma(data):
    return sum(data[0])/len(data[0])

def ema(data):
    open = data[0]
    period = len(open)

    if type(data[-1]) != str :
        ema_st = sum(open)
        return ema_st
    else :
        previous_ema = data[-1]
        alpha = 2/(period+1)
        ema = previous_ema + alpha * (open - previous_ema)
        return ema

def wma(data):
    open = data[0]
    n = len(open)
    weights = np.arange(1, n + 1)
    return np.sum(open * weights) / np.sum(weights)

def vwma(data):
    open = data[0]
    volume = data[1]
    return sum(open*volume)/sum(volume)

def amplitude(data):

    if data[0][0] != None and data[1][0] != None :
        ampl = data[0][0] - data[1][0]
        return abs(ampl)

    else:
        return None

def atr(data):

    high = data[0]
    low = data[1]
    open = data[2]

    period = len(high)

    tr_list = []

    if  type(data[-1]) != str: 
        for i in range(period):
            tr = max(
                high[i] - low[i],
                abs(high[i] - open[i]),
                abs(low[i] - open[i])
            )
            tr_list.append(tr)
            
        previous_atr = sum(tr_list)/period
        return previous_atr

    else:
        previous_atr = float(data[-1])
            
        tr = max(
                    high[-1] - low[-1],
                    abs(high[-1] - open[-1]),
                    abs(low[-1]  - open[-1])
                )
        atr = ((previous_atr * (period - 1)) + tr) / period
        return atr

def relative(data):
    if data[1][0] == None or data[0][0] == None:
        return None
    else : 
        return data[0][0]/data[1][0]

def relative_gap(data):
    if data[1][0] is None or data[0][0] is None:
        return None
    else : 
        return (data[0][0] - data[1][0])/data[1][0]
        
def return_(data):
    start = data[0][0]
    end = data[1][-1]
    return (end-start)/start

def log_return(data):
    start = data[0][0]
    end = data[1][-1]
    r = log(end/start)
    return r 

def slope(data):
    return data[0][-1] - data[0][0] / len(data[0])

def linear_slope(data):
    points = data[0]
    period = len(data[0])

    x = np.arrange(period)
    slope = np.polyfit(x, points, 1)[0]

    return slope

def close_position(data):
    close = data[0][0]
    high = data[1][0]
    low = data[2][0]

    position = (close-low)/(high-low)

    return position

def std_dev(data):
    return np.std(data[0])

def zscore(data):

    values = data[0][0]
    moy    = data[1][0]
    sigma  = data[2][0]

    if moy is None or values is None or sigma is None:
        return None

    var = values - moy
    z = var/sigma

    return z

def log_(data):
    return log(data)

def bol_band_up(data):
    sma = data[0][0]
    dev = data[1][0]

    if dev is not None :
        return sma + 2*dev

    else:
        return None

def bol_band_down(data):
    sma = data[0][0]
    dev = data[1][0]

    if dev is not None :
        return sma - 2*dev

    else:
        return None

def avg_gain(data):

    close = data[0]
    previous_data = data[-1]
    period = len(close) -1

    moy_gain = 0

    for i in range(len(close)-1):
        delta = close[i+1] - close[i]
        gain = max(delta, 0)

        moy_gain += gain

    moy_gain = (moy_gain)/period

    if type(previous_data) != str :
        return moy_gain

    else:
        return (previous_data*(period-1)+(moy_gain*period))/period

def avg_loss(data):

    close = data[0]
    previous_data = data[-1]
    period = len(close) -1

    moy_loss = 0

    for i in range(len(close)-1):
        delta = close[i+1] - close[i]
        loss = max(-delta, 0)

        moy_loss += loss

    moy_loss = (moy_loss)/period

    if type(previous_data) != str:
        return moy_loss

    else:
        return (previous_data*(period-1)+(moy_loss*period))/period

def rsi(data):
    avg_gain = data[0][0]
    avg_loss = data[1][0]

    if avg_gain is None or avg_loss is None:
        return None

    if avg_loss == 0:
        rsi = 100
        return rsi

    rs = avg_gain/avg_loss
    rsi = 100 - (100/(1+rs))

    return rsi

def stochastic(data):

    close = data[0][-1]
    high  = data[1]
    low   = data[2]

    high = max(high)
    low  = min(low)

    k = 100 * (close-low)/(high-low)

    return k 

def tp(data):
    close = data[0][0]
    high = data[1][0]
    low = data[2][0]

    tp = (close + low + high) / 3

    return tp

def cci(data):
    tp_ = data[0]
    sma_tp = sum(tp_)/len(tp_)
    period = len(tp_)

    md = 0

    for i in range(period):
        md += abs(tp_[i] - sma_tp)

    md = md/period

    cci = (tp_[-1] - sma_tp) / (0.015 * md)

    return cci

def roc(data):
    close = data[0]
    roc = close[-1]-close[0]*100/ close[0]

    return roc

def william(data):
    close = data[0][0]
    high = data[1][0]
    low = data[2][0]

    wil = (high - close)*-100 / (high-low)
    
    return wil



[
    # ==========================
    # PRIX
    # ==========================

    "weighted_close",

    # ==========================
    # RENDEMENTS
    # ==========================

    # ==========================
    # VOLUME
    # ==========================

    "volume_percentile",

    # ==========================
    # MOYENNES MOBILES
    # ==========================

    "vwema",

    # ==========================
    # DISTANCES AUX MOYENNES
    # ==========================

    "relative_vwema",
    "relative_vwma",

    # ==========================
    # PENTES
    # ==========================

    "slope_sma_20",

    "slope_ema_20",

    "slope_vwema",

    "acceleration_sma",
    "acceleration_ema",
    "acceleration_vwema",

    # ==========================
    # VOLATILITE
    # ==========================

    "relative_atr",
    "rolling_std",
    "variance",
    "coefficient_variation",

    "average_range",

    # ==========================
    # BOLLINGER
    # ==========================

    "relative_upper_band",
    "relative_lower_band",

    # ==========================
    # MOMENTUM
    # ==========================

    "roc",
    "momentum",

    "williams_r",
   
    "macd",
    "macd_signal",
    "macd_histogram",

    # ==========================
    # STRUCTURE DE MARCHE
    # ==========================

    "bullish_count",
    "bearish_count",

    "bullish_streak",
    "bearish_streak",

    "distance_last_peak",
    "distance_last_low",

    "variation_last_peak",
    "variation_last_low",

    "bars_since_peak",
    "bars_since_low",

    # ==========================
    # DONNEES DES PICS
    # ==========================

    "statut",
    "peak_height",
    "prominence",
    "left_base",
    "right_base",
    "width",
    "width_height",
    "left_ip",
    "right_ip",
    "plateau_size",
    "left_edge",
    "right_edge",

    # ==========================
    # DONNEES BINANCE
    # ==========================

    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume",

    "buy_ratio",
    "quote_base_ratio",
    "average_trade_size",

    # ==========================
    # TEMPS
    # ==========================

    "hour",
    "minute",
    "day_of_week",
    "day_of_month",
    "month",

    "asian_session",
    "europe_session",
    "us_session",

    # ==========================
    # STATISTIQUES
    # ==========================

    "quantile",
    "decile",
    "percentile",
    "zscore",
    "distance_median",
    "rolling_skewness",
    "rolling_kurtosis",

    # ==========================
    # VARIABLES COMBINEES
    # ==========================

    "volume_x_atr",
    "volume_x_relative_sma",
    "atr_x_relative_sma",
    "slope_x_atr",
    "relative_sma_x_rsi",
    "relative_vwema_x_atr",
    "relative_volume_x_atr",
    "number_of_trades_x_volume",
    "buy_ratio_x_atr"
]