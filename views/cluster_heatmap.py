import matplotlib.pyplot as plt
import seaborn as sns
import os


def plot_cluster_heatmap(cluster_means):
    """
    Строит и сохраняет тепловую карту средних значений факторов по кластерам.
    """
    # Создаем директорию, если она не существует
    os.makedirs("output/districts/plots", exist_ok=True)

    plt.figure(figsize=(12, 8))
    sns.heatmap(cluster_means, annot=True, cmap="viridis", fmt=".2f")
    plt.title("Тепловая карта средних значений факторов по кластерам")
    plt.xlabel("Факторы")
    plt.ylabel("Кластеры")
    plt.tight_layout()
    plt.savefig("output/districts/plots/cluster_heatmap.png", dpi=300)
    plt.close()
