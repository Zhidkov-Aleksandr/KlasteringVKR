from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd


def run_kmeans(data, k=3):
    """
    Кластеризация федеральных округов методом K-means
    """

    # названия округов
    districts = data.index

    # масштабирование
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(data)

    # модель K-means
    model = KMeans(n_clusters=k, random_state=42)

    clusters = model.fit_predict(X_scaled)

    result = pd.DataFrame({
        "district": districts,
        "cluster": clusters
    })

    return result, model.cluster_centers_