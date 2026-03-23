import pandas as pd
from pathlib import Path

# папка где лежат файлы кластеров
INPUT_PATH = Path("results/regions_clusters")

# папка куда сохраняем объединённый файл
OUTPUT_PATH = Path("data")
OUTPUT_PATH.mkdir(exist_ok=True)


def merge_region_clusters():

    files = list(INPUT_PATH.glob("*_clusters.xlsx"))

    if not files:
        print("Файлы кластеров не найдены в", INPUT_PATH)
        return

    dfs = []

    for file in files:
        print("Найден файл:", file)
        df = pd.read_excel(file)
        dfs.append(df)

    result = pd.concat(dfs, ignore_index=True)

    result.to_excel(OUTPUT_PATH / "all_regions_clusters.xlsx", index=False)

    print("Файл data/all_regions_clusters.xlsx создан")