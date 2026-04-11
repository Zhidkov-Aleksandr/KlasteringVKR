import sqlite3
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import os


def cluster_regions_by_district(year=2024):

    os.makedirs("output/regions/tables", exist_ok=True)

    conn = sqlite3.connect("digitalization.db")

    districts = pd.read_sql("""
        SELECT id, name
        FROM federal_districts
    """, conn)

    for _, district in districts.iterrows():

        district_id = district["id"]
        district_name = district["name"]

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
        # заменяем пропуски на минимальные значения по каждому показателю
        matrix = matrix.apply(lambda col: col.fillna(col.min()))

        scaler = StandardScaler()
        X = scaler.fit_transform(matrix)

        kmeans = KMeans(n_clusters=3, random_state=42)
        kmeans.fit(X)

        print("\nЦентры кластеров:")
        print(pd.DataFrame(kmeans.cluster_centers_, columns=matrix.columns))

        centers = pd.DataFrame(kmeans.cluster_centers_)

        # считаем общий уровень цифровизации
        centers["score"] = centers.mean(axis=1)

        # сортируем
        order = centers["score"].sort_values().index

        cluster_map = {
            order[0]: 3,  # аутсайдеры
            order[1]: 2,  # потенциал
            order[2]: 1  # лидеры
        }

        clusters = pd.Series(kmeans.labels_).map(cluster_map).values

        results = pd.DataFrame({
            "region": matrix.index,
            "cluster": clusters
        })

        labels = {
            1: "Передовые субъекты",
            2: "Субъекты с потенциалом развития",
            3: "Субъекты-аутсайдеры"
        }

        results["cluster_name"] = results["cluster"].map(labels)

        filename = district_name.replace(" ", "_")

        results.to_excel(
            f"output/regions/tables/{filename}_clusters.xlsx",
            index=False
        )

        print(f"\nКластеры субъектов — {district_name}")
        print(results)

    conn.close()
