import pandas as pd


def analyze_cluster_factors(data, clusters):

    df = data.copy()
    df["cluster"] = clusters

    # средние значения по кластерам
    cluster_means = df.groupby("cluster").mean()

    print("\nСредние значения факторов по кластерам:\n")
    print(cluster_means)

    # вычисляем разброс факторов
    factor_variation = cluster_means.max() - cluster_means.min()

    factor_variation = factor_variation.sort_values(ascending=False)

    print("\nФакторы с наибольшими различиями между кластерами:\n")
    print(factor_variation)

    return cluster_means, factor_variation