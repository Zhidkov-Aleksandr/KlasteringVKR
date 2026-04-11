from abc import ABC, abstractmethod
import pandas as pd


class DataLoader(ABC):
    @abstractmethod
    def load_data(self, year: int) -> pd.DataFrame:
        pass


class ClusteringStrategy(ABC):
    @abstractmethod
    def cluster(self, data: pd.DataFrame, k: int = 3) -> tuple:
        pass


class Analyzer(ABC):
    @abstractmethod
    def analyze(self, data: pd.DataFrame, clusters) -> dict:
        pass


class Visualizer(ABC):
    @abstractmethod
    def visualize(self, data: pd.DataFrame, clusters, **kwargs):
        pass


class Pipeline:
    def __init__(self, data_loader: DataLoader, clustering_strategy: ClusteringStrategy,
                 analyzer: Analyzer, visualizer: Visualizer):
        self.data_loader = data_loader
        self.clustering_strategy = clustering_strategy
        self.analyzer = analyzer
        self.visualizer = visualizer

    def run(self, year: int):
        # Загрузка данных
        data = self.data_loader.load_data(year)

        # Кластеризация
        clusters, centers = self.clustering_strategy.cluster(data)

        # Анализ
        analysis_results = self.analyzer.analyze(data, clusters)

        # Визуализация
        self.visualizer.visualize(data, clusters, centers=centers, **analysis_results)