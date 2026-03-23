import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DB_NAME = "digitalization.db"
CLUSTERS_FILE = "data/all_regions_clusters.xlsx"

OUTPUT_PATH = Path("plots/districts-subject")
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)


def plot_cluster_subjects():

    conn = sqlite3.connect(DB_NAME)

    query = """
    SELECT
        r.name as region,
        fd.name as district,
        i.name as indicator,
        v.value
    FROM values_data v
    JOIN regions r ON v.territory_id = r.id
    JOIN federal_districts fd ON r.federal_district_id = fd.id
    JOIN indicators i ON v.indicator_id = i.id
    WHERE v.territory_type = 'region'
    """

    df = pd.read_sql(query, conn)
    conn.close()

    # pivot таблица
    matrix = df.pivot_table(
        index=["region", "district"],
        columns="indicator",
        values="value"
    ).reset_index()

    clusters = pd.read_excel(CLUSTERS_FILE)
    clusters.columns = ["region", "cluster", "cluster_name"]

    data = pd.merge(matrix, clusters, on="region")

    indicators = [c for c in data.columns if c not in ["region", "district", "cluster", "cluster_name"]]

    districts = data["district"].unique()

    for district in districts:

        district_data = data[data["district"] == district]

        for cluster in sorted(district_data["cluster"].unique()):

            cluster_data = district_data[district_data["cluster"] == cluster]

            if cluster_data.empty:
                continue

            means = cluster_data[indicators].mean()

            plt.figure(figsize=(10,6))

            means.plot(kind="bar")

            plt.title(f"{district}\nКластер {cluster}")

            plt.ylabel("Среднее значение показателя")

            plt.xticks(rotation=45, ha="right")

            plt.tight_layout()

            filename = f"{district}_cluster_{cluster}.png"

            plt.savefig(OUTPUT_PATH / filename, dpi=300)

            plt.close()

    print("Диаграммы кластеров субъектов построены")