import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

DB_NAME = "digitalization.db"
CLUSTERS_FILE = "output/regions/tables/all_regions_clusters.xlsx"

PLOTS_PATH = Path("output/regions/plots")
TABLES_PATH = Path("output/regions/tables")


def analyze_cluster_district_factors():

    PLOTS_PATH.mkdir(parents=True, exist_ok=True)
    TABLES_PATH.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_NAME)

    query = """
    SELECT
        r.name as region,
        i.name as indicator,
        v.value
    FROM values_data v
    JOIN regions r ON v.territory_id = r.id
    JOIN indicators i ON v.indicator_id = i.id
    WHERE v.territory_type = 'region'
    """

    df = pd.read_sql(query, conn)

    conn.close()

    # превращаем в матрицу регион × показатели
    matrix = df.pivot(index="region", columns="indicator", values="value")

    matrix.reset_index(inplace=True)

    # загружаем кластеры
    clusters = pd.read_excel(CLUSTERS_FILE)

    clusters.columns = ["region", "cluster", "cluster_name"]

    # объединяем
    data = pd.merge(matrix, clusters, on="region")

    features = matrix.columns[1:]

    # средние значения факторов по кластерам
    cluster_means = data.groupby("cluster")[features].mean()

    cluster_means.to_excel(TABLES_PATH / "cluster_feature_means.xlsx")

    # ranking факторов
    factor_diff = cluster_means.max() - cluster_means.min()
    factor_ranking = factor_diff.sort_values(ascending=False)

    plt.figure(figsize=(10,6))
    factor_ranking.plot(kind="bar")

    plt.title("Ранжирование факторов различий между кластерами субъектов РФ")

    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()

    plt.savefig(PLOTS_PATH / "factor_ranking.png", dpi=300)

    plt.close()

    # heatmap
    plt.figure(figsize=(10,6))

    sns.heatmap(
        cluster_means,
        annot=True,
        cmap="YlOrRd",
        fmt=".1f"
    )

    plt.title("Тепловая карта факторов по кластерам субъектов РФ")

    plt.tight_layout()

    plt.savefig(PLOTS_PATH / "factor_heatmap.png", dpi=300)

    plt.close()

    print("Анализ факторов завершен")
