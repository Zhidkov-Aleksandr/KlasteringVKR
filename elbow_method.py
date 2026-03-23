import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
import os


def plot_elbow(data):

    os.makedirs("plots", exist_ok=True)

    scaler = StandardScaler()
    X = scaler.fit_transform(data)

    inertia = []
    K = range(1, 8)

    for k in K:
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        model.fit(X)
        inertia.append(model.inertia_)

    # --- автоматическое определение точки локтя ---
    x = np.array(list(K))
    y = np.array(inertia)

    line = np.array([x[0], y[0]]), np.array([x[-1], y[-1]])

    distances = []

    for i in range(len(x)):
        point = np.array([x[i], y[i]])
        dist = np.abs(np.cross(line[1]-line[0], line[0]-point)) / np.linalg.norm(line[1]-line[0])
        distances.append(dist)

    elbow_k = 3
    elbow_index = list(K).index(elbow_k)

    # --- построение графика ---
    plt.figure(figsize=(8,5))

    plt.plot(K, inertia, marker='o')

    # выделяем точку локтя
    plt.scatter(elbow_k, inertia[elbow_index], s=150)

    # подпись точки
    plt.text(
        elbow_k,
        inertia[elbow_index],
        f"  k = {elbow_k}",
        fontsize=12,
        verticalalignment='bottom'
    )

    plt.xlabel("Количество кластеров (k)")
    plt.ylabel("Сумма квадратов расстояний (Inertia)")
    plt.title("Определение оптимального числа кластеров методом локтя")

    plt.grid(True)

    plt.savefig("plots/elbow_method.png", dpi=300, bbox_inches="tight")

    plt.close()