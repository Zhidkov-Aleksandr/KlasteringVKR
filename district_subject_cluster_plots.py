import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

DB_NAME = "digitalization.db"
CLUSTERS_FILE = "data/all_regions_clusters.xlsx"

OUTPUT_PATH = Path("plots/districts-subject")
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)


def plot_district_subject_clusters():

    conn = sqlite3.connect(DB_NAME)

    query = """
    SELECT
        r.name as region,
        r.federal_district_id,
        i.name as indicator,
        v.value
    FROM values_data v
    JOIN regions r ON v.territory_id = r.id
    JOIN indicators i ON v.indicator_id = i.id
    WHERE v.territory_type = 'region'
    """

    df = pd.read_sql(query, conn)
    conn.close()

    # делаем матрицу регион × показатели
    matrix = df.pivot(index="region", columns="indicator", values="value")
    matrix.reset_index(inplace=True)

    # загружаем кластеры
    clusters = pd.read_excel(CLUSTERS_FILE)
    clusters.columns = ["region", "cluster", "cluster_name"]

    # объединяем
    data = pd.merge(matrix, clusters, on="region")

    # добавляем округ
    districts = df[["region", "federal_district_id"]].drop_duplicates()
    data = pd.merge(data, districts, on="region")

    indicators = matrix.columns[1:]

    district_map = {
        1: "Центральный федеральный округ",
        2: "Северо-Западный федеральный округ",
        3: "Южный федеральный округ",
        4: "Северо-Кавказский федеральный округ",
        5: "Приволжский федеральный округ",
        6: "Уральский федеральный округ",
        7: "Сибирский федеральный округ",
        8: "Дальневосточный федеральный округ"
    }

    cluster_map = {
        1: "Передовые субъекты",
        2: "Субъекты с потенциалом развития",
        3: "Субъекты-аутсайдеры"
    }

    for district_id in sorted(data["federal_district_id"].unique()):

        district_data = data[data["federal_district_id"] == district_id]

        for cluster_id in sorted(district_data["cluster"].unique()):

            cluster_data = district_data[district_data["cluster"] == cluster_id]

            if cluster_data.empty:
                continue

            mean_values = cluster_data[indicators].mean()

            labels = indicators.tolist()
            values = mean_values.values.tolist()

            angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
            values += values[:1]
            angles += angles[:1]

            fig, ax = plt.subplots(figsize=(7,7), subplot_kw=dict(polar=True))

            ax.plot(angles, values)
            ax.fill(angles, values, alpha=0.25)

            ax.set_thetagrids(np.degrees(angles[:-1]), labels)

            title = f"{district_map[district_id]}\nКластер {cluster_id}: {cluster_map[cluster_id]}"
            ax.set_title(title, y=1.1)

            filename = f"{district_map[district_id]}_cluster_{cluster_id}.png"
            filename = filename.replace(" ", "_")

            plt.tight_layout()

            plt.savefig(OUTPUT_PATH / filename, dpi=300)

            plt.close()

    print("Диаграммы кластеров субъектов по округам построены")