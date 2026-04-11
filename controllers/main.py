import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

from models.architecture import Pipeline
from models.data_service import DistrictDataLoader
from models.clustering_service import KMeansClusteringStrategy
from models.analysis_service import ClusterAnalyzer
from views.visualization_service import DistrictVisualizer
from services.regions_elbow import plot_regions_elbow
from services.regions_clustering import cluster_regions_by_district
from services.analysis_cluster_factors import analyze_cluster_district_factors
from services.merge_region_clusters import merge_region_clusters
from services.cluster_subject_plots import plot_cluster_subjects
from services.district_subject_cluster_plots import plot_district_subject_clusters
from services.clustering_all_regions import run_global_clustering


def main():
    # Создаем сервисы
    data_loader = DistrictDataLoader("Данные по федеральным округам.xlsx")
    clustering_strategy = KMeansClusteringStrategy()
    analyzer = ClusterAnalyzer()
    visualizer = DistrictVisualizer()

    # Создаем pipeline для округов
    pipeline = Pipeline(data_loader, clustering_strategy, analyzer, visualizer)

    year = 2024

    # Метод локтя для субъектов
    plot_regions_elbow(year)

    # Кластеризация субъектов по округам
    cluster_regions_by_district(year)

    # Запускаем pipeline для округов
    pipeline.run(year)

    # Анализ факторов субъектов РФ
    print("\nОбъединение кластеров субъектов...")
    merge_region_clusters()
    print("\nАнализ факторов различий между кластерами субъектов РФ...\n")
    analyze_cluster_district_factors()
    print("\nАнализ кластеров субъектов завершён.")

    # Построение диаграмм кластеров субъектов
    print("\nПостроение диаграмм кластеров субъектов...\n")
    plot_cluster_subjects()
    plot_district_subject_clusters()

    # Построение диаграмм кластеров по всем субъектам
    print("\nПостроение диаграмм кластеров по всем субъектам...\n")
    run_global_clustering()


if __name__ == "__main__":
    main()