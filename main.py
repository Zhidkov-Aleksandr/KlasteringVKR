from database import create_database
from excel_loader import load_excel
from district_clustering import get_district_matrix
from elbow_method import plot_elbow
from district_plots import plot_districts
from radar_plot import plot_cluster_radar
from cluster_analysis import analyze_cluster_factors
from district_clustering import cluster_districts
from cleanup_plots import cleanup_images
from cluster_heatmap import plot_cluster_heatmap
from factor_ranking_plot import plot_factor_ranking
from regions_elbow import plot_regions_elbow
from regions_clustering import cluster_regions_by_district
from analysis_cluster_factors import analyze_cluster_district_factors
from merge_region_clusters import merge_region_clusters
from district_subject_cluster_plots import plot_district_subject_clusters
from cluster_subject_plots import plot_cluster_subjects
from clustering_all_regions import run_global_clustering
from district_scatter import plot_district_scatter
import pandas as pd


# =========================
# 1. Создаем базу данных
# =========================
create_database()


# =========================
# 2. Удаляем старые изображения
# =========================
cleanup_images()


# =========================
# 3. Загружаем Excel
# =========================
load_excel("Данные по федеральным округам.xlsx", 2024)

print("Загрузка завершена.")


# =========================
# 4. Метод локтя для субъектов
# =========================
plot_regions_elbow(2024)


# =========================
# 5. Кластеризация субъектов по округам
# =========================
cluster_regions_by_district(2024)


# =========================
# 6. Получаем матрицу округов
# =========================
data = get_district_matrix(2024)

print("\nМатрица для кластеризации:\n")

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

print(data)


# =========================
# 7. Метод локтя для округов
# =========================
plot_elbow(data)


# =========================
# 8. Кластеризация округов
# =========================
clusters, centers = cluster_districts(data)


# нумерация кластеров с 1
clusters = clusters + 1

print("\nКластеры:\n")

results = pd.DataFrame({
    "district": data.index,
    "cluster": clusters
})


labels = {
    1: "Передовые округа",
    2: "Округа с потенциалом развития",
    3: "Округа-аутсайдеры"
}

results["cluster_name"] = results["cluster"].map(labels)

print(results)

print("\nЦентры кластеров:\n")
print(centers)


# =========================
# 9. Анализ факторов округов
# =========================
cluster_means, factors = analyze_cluster_factors(data, clusters)

plot_cluster_heatmap(cluster_means)
plot_factor_ranking(factors)


# =========================
# 10. Диаграммы округов
# =========================
plot_districts(data)


# =========================
# 11. Radar диаграммы кластеров
# =========================
plot_cluster_radar(cluster_means, results)

# =========================
# 11.5 Точечная диаграмма (Scatter Plot) для округов
# =========================
plot_district_scatter(data, clusters, centers)


# =========================
# 12. Анализ факторов субъектов РФ
# =========================

print("\nОбъединение кластеров субъектов...")

merge_region_clusters()
print("\nАнализ факторов различий между кластерами субъектов РФ...\n")

analyze_cluster_district_factors()


print("\nАнализ кластеров субъектов завершён.")

# =========================
# 13. Построение диаграмм кластеров субъектов по федеральным округам
# =========================
print("\nПостроение диаграмм кластеров субъектов...\n")

plot_cluster_subjects()
print("\nПостроение диаграмм кластеров субъектов по федеральным округам...\n")

plot_district_subject_clusters()

# =========================
# 14. Построение диаграмм кластеров по всем субъектам
# =========================
print("\nПостроение диаграмм кластеров по всем субъектам...\n")

run_global_clustering()

