import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import os
import shutil


def plot_regions_elbow(year=2024):

    # создаём папку
    os.makedirs("output/regions/diagrams", exist_ok=True)

    conn = sqlite3.connect("digitalization.db")

    # получаем список округов
    districts = pd.read_sql("""
        SELECT id, name
        FROM federal_districts
    """, conn)

    for _, district in districts.iterrows():

        district_id = district["id"]
        district_name = district["name"]

        # получаем данные субъектов округа
        df = pd.read_sql(f"""
            SELECT r.name as region,
                   i.name as indicator,
                   v.value
            FROM values_data v
            JOIN regions r ON v.territory_id = r.id
            JOIN indicators i ON v.indicator_id = i.id
            WHERE v.territory_type = 'region'
            AND r.federal_district_id = {district_id}
            AND v.year = {year}
        """, conn)

        if df.empty:
            continue

        matrix = df.pivot(index="region", columns="indicator", values="value")
        matrix = matrix.fillna(matrix.mean())

        # заполняем пропущенные значения средними
        scaler = StandardScaler()
        X = scaler.fit_transform(matrix)

        distortions = []
        max_k = min(10, len(matrix))
        K = range(1, max_k)

        for k in K:
            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(X)
            distortions.append(kmeans.inertia_)

        plt.figure(figsize=(6,4))

        plt.plot(K, distortions, marker='o')

        plt.xlabel("Количество кластеров (k)")
        plt.ylabel("Внутрикластерная ошибка")

        plt.title(f"Метод локтя\n{district_name}")

        plt.xticks(K)

        plt.tight_layout()

        filename = district_name.replace(" ", "_").replace("ё","е")

        plt.savefig(f"output/regions/diagrams/elbow_{filename}.png", dpi=300)

        plt.close()

    conn.close()
