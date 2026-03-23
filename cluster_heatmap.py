import seaborn as sns
import matplotlib.pyplot as plt
import os


def plot_cluster_heatmap(cluster_means):

    # создаём папку plots если её нет
    os.makedirs("plots", exist_ok=True)

    plt.figure(figsize=(12,6))

    sns.heatmap(
        cluster_means,
        annot=True,
        fmt=".1f",
        cmap="YlOrRd",
        linewidths=0.5
    )

    plt.title("Различия факторов цифровизации между кластерами федеральных округов")

    plt.ylabel("Кластеры")
    plt.xlabel("Показатели цифровизации")

    plt.tight_layout()

    plt.savefig("plots/cluster_heatmap.png", dpi=300)

    plt.close()