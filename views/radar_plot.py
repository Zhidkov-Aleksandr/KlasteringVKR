import matplotlib.pyplot as plt
import numpy as np
import os

def plot_radar_charts(cluster_means):
    """
    Строит и сохраняет радарные (лепестковые) диаграммы для каждого кластера.
    """
    # Создаем директорию, если она не существует
    os.makedirs("output/districts/diagrams", exist_ok=True)

    labels = cluster_means.columns.tolist()
    num_vars = len(labels)

    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    for cluster_id, row in cluster_means.iterrows():
        values = row.tolist()
        values += values[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.fill(angles, values, color='b', alpha=0.25)
        ax.plot(angles, values, color='b', linewidth=2)

        ax.set_yticklabels([])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=8)

        plt.title(f"Профиль кластера {cluster_id}", size=14, y=1.1)

        plt.savefig(f"output/districts/diagrams/cluster_{cluster_id}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
