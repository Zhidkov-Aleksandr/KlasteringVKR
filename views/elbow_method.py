import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import os


def plot_elbow_method(data):
    """
    Строит и сохраняет график метода локтя.
    """
    # Создаем директорию, если она не существует
    os.makedirs("output/districts/diagrams", exist_ok=True)

    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)

    distortions = []
    K = range(1, 10)
    for k in K:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(data_scaled)
        distortions.append(kmeans.inertia_)

    plt.figure(figsize=(10, 6))
    plt.plot(K, distortions, "bx-")
    plt.xlabel("k (количество кластеров)")
    plt.ylabel("Искажение")
    plt.title("Метод локтя для определения оптимального количества кластеров")
    plt.savefig("output/districts/diagrams/elbow_method.png", dpi=300, bbox_inches="tight")
    plt.close()
