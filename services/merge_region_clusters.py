import pandas as pd
from pathlib import Path

# папка где лежат файлы кластеров
INPUT_PATH = Path("output/regions/tables")

# папка куда сохраняем объединённый файл
OUTPUT_PATH = Path("output/regions/tables")


def merge_region_clusters():

    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    files = [f for f in INPUT_PATH.glob("*_clusters.xlsx") if "all_regions" not in f.name]

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

    print("Файл output/regions/tables/all_regions_clusters.xlsx создан")
