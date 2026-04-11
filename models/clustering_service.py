from models.architecture import ClusteringStrategy
from utils.district_clustering import cluster_districts


class KMeansClusteringStrategy(ClusteringStrategy):
    def cluster(self, data, k=3):
        clusters, centers = cluster_districts(data, k)
        return clusters, centers