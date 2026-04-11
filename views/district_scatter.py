import matplotlib.pyplot as plt
import os

def plot_district_scatter(data, cluster_labels):
    """
    Строит и сохраняет точечную диаграмму для кластеризации федеральных округов.
    """
    # Создаем директорию, если она не существует
    os.makedirs('output/districts/plots', exist_ok=True)

    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(data.iloc[:, 0], data.iloc[:, 1], c=cluster_labels, cmap='viridis', s=100, alpha=0.7)
    plt.title('Кластеризация федеральных округов')
    plt.xlabel(data.columns[0])
    plt.ylabel(data.columns[1])
    plt.legend(handles=scatter.legend_elements()[0], labels=set(cluster_labels))
    plt.grid(True)
    plt.savefig('output/districts/plots/district_scatter_clusters.png', dpi=300, bbox_inches='tight')
    plt.close()
