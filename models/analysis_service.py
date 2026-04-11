from models.architecture import Analyzer
from utils.cluster_analysis import analyze_cluster_factors


class ClusterAnalyzer(Analyzer):
    def analyze(self, data, clusters):
        cluster_means, factors = analyze_cluster_factors(data, clusters)
        return {'cluster_means': cluster_means, 'factors': factors}