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
    # Ограничиваем K количеством данных: n_clusters не может быть >= n_samples.
    # Так как у нас всего 8 округов, K должно быть от 1 до 8 (не включая 8, если len(data)=8, то max_k = 8, range(1, 8) -> 1..7)
    max_k = min(8, len(data))
    
    # Защита от случая, когда len(data) меньше 2
    if max_k <= 1:
        max_k = 2

    K = range(1, max_k)

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
