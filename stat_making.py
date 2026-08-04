import numpy as np
import matplotlib.pyplot as plt


def stat_onevar(cursor, status, data, inter):

    total_computed = 0

    print("\r" + " " * 80, end="\r")

    stat_table = []

    # Récupération de toutes les valeurs
    rows = cursor.execute(f"""
        SELECT {data}
        FROM candles
        WHERE {data} IS NOT NULL
    """).fetchall()

    values = np.array([row[0] for row in rows], dtype=float)

    # Calcul des bornes des quantiles
    bornes = np.quantile(values, np.linspace(0, 1, inter + 1))

    borne_list = []

    for i in range(inter):

        borne_min = bornes[i]
        borne_max = bornes[i + 1]

        borne_list.append((float(borne_min), float(borne_max)))

        # Nombre de bougies
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM candles
            WHERE {data} >= ?
            AND {data} < ?
        """, (borne_min, borne_max))

        nb_candles = cursor.fetchone()[0]

        # Nombre de pics
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM candles
            WHERE {status} > 0
            AND {data} >= ?
            AND {data} < ?
        """, (borne_min, borne_max))

        nb_peaks = cursor.fetchone()[0]

        # Nombre de creux
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM candles
            WHERE {status} < 0
            AND {data} >= ?
            AND {data} < ?
        """, (borne_min, borne_max))

        nb_lows = cursor.fetchone()[0]

        stat_table.append([
            i,
            nb_peaks * 100 / nb_candles if nb_candles else 0,
            nb_lows * 100 / nb_candles if nb_candles else 0,
            nb_candles
        ])

        total_computed += 1
        print(
            f"Computed Stat : {total_computed*100 / inter} %",
            end="\r"
        )

    # Affichage
    x = [ligne[0] for ligne in stat_table]
    y_peaks = [ligne[1] for ligne in stat_table]
    y_low = [ligne[2] for ligne in stat_table]

    print(borne_list)

    plt.plot(x, y_low, marker="o")
    plt.plot(x, y_peaks, color="red", marker="o")

    plt.xlabel(f"Quantile {data}")
    plt.ylabel("Probabilité de pic (%)")
    plt.grid(True)
    plt.show()

    return stat_table


def stat_twovar(cursor, data_1, data_2, inter):


    print("\r" + " " * 80, end="\r")

    rows = cursor.execute(f"""
            SELECT {data_1}, {data_2}
            FROM candles
            WHERE {data_1} IS NOT NULL
            ANd {data_2} IS NOT NULL
    """).fetchall()

    values_1 = np.array([row[0] for row in rows], dtype=float)
    values_2 = np.array([row[1] for row in rows], dtype=float)

    bornes_1 = np.quantile(values_1, np.linspace(0, 1, inter + 1))
    bornes_2 = np.quantile(values_2, np.linspace(0, 1, inter + 1))

    stat_table = []

    total_computed = 0

    for i in range(inter):

        stat_table.append([])

        borne_min_2 = bornes_1[i]
        borne_max_2 = bornes_2[i + 1]

        for n in range(inter):

            borne_min_1 = bornes_1[n]
            borne_max_1 = bornes_1[n + 1]

            cursor.execute(f"""
                SELECT COUNT (*)
                FROM candles 
                WHERE statut = 100
                AND {data_1} >= ?
                AND {data_1} < ?
                AND {data_2} >= ?
                AND {data_2 } < ?
            """, (borne_min_1, borne_max_1, borne_min_2, borne_max_2 ))


            nb_peaks = cursor.fetchall()[0][0]

            cursor.execute(f"""
                SELECT COUNT (*)
                FROM candles 
                WHERE statut = -100
                AND {data_1} >= ?
                AND {data_1} < ?
                AND {data_2} >= ?
                AND {data_2 } < ?
            """, (borne_min_1, borne_max_1, borne_min_2, borne_max_2 ))

            nb_lows = cursor.fetchall()[0][0]

            cursor.execute(f"""
                SELECT COUNT (*)
                FROM candles 
                WHERE {data_1} >= ?
                AND {data_1} < ?
                AND {data_2} >= ?
                AND {data_2 } < ?
            """, (borne_min_1, borne_max_1, borne_min_2, borne_max_2 ))

            nb_candles = cursor.fetchall()[0][0]

            stat_table[i].append([nb_peaks * 100 / nb_candles if nb_candles else 0])

            total_computed += 1

            print(
            f"Computed Stat : {round((total_computed*100/inter**2), 1)} %   ",
            end="\r"
        )

    heatmap = np.array(stat_table)

    plt.imshow(
        heatmap,
        origin="lower",
        cmap="viridis",
        aspect="auto"
    )

    plt.colorbar(label="Probabilité de pic")

    plt.xlabel(f"{data_1}")
    plt.ylabel(f"{data_2}")

    plt.show()

  