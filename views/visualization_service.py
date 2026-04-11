from models.architecture import Visualizer
from views.elbow_method import plot_elbow_method
from views.district_plots import plot_district_cluster_charts
from views.radar_plot import plot_radar_charts
from views.cluster_heatmap import plot_cluster_heatmap
from views.factor_ranking_plot import plot_factor_ranking
from views.district_scatter import plot_district_scatter
import pandas as pd


class DistrictVisualizer(Visualizer):
    def visualize(self, data, clusters, centers=None, cluster_means=None, factors=None, **kwargs):
        # Метод локтя
        plot_elbow_method(data)

        # Диаграммы округов
        plot_district_cluster_charts(data, clusters)

        # Radar диаграммы кластеров
        if cluster_means is not None:
            results = pd.DataFrame({
                "district": data.index,
                "cluster": clusters + 1  # нумерация с 1
            })
            labels = {
                1: "Передовые округа",
                2: "Округа с потенциалом развития",
                3: "Округа-аутсайдеры"
            }
            results["cluster_name"] = results["cluster"].map(labels)
            plot_radar_charts(cluster_means)

        # Heatmap и ranking
        if cluster_means is not None:
            plot_cluster_heatmap(cluster_means)
        if factors is not None:
            plot_factor_ranking(factors)

        # Scatter plot
        if centers is not None:
            plot_district_scatter(data, clusters)
