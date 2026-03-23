import matplotlib.pyplot as plt
import numpy as np
import os


def plot_cluster_radar(cluster_means, results):

    # создаем папку если ее нет
    os.makedirs("plots/clusters", exist_ok=True)

    factors = cluster_means.columns.tolist()

    angles = np.linspace(0, 2*np.pi, len(factors), endpoint=False)
    angles = np.concatenate((angles, [angles[0]]))

    # названия кластеров
    cluster_names = {
        1: "Передовые округа",
        2: "Округа с потенциалом развития",
        3: "Округа-аутсайдеры"
    }

    for cluster_id, row in cluster_means.iterrows():

        values = row.values.tolist()
        values.append(values[0])

        # округа в кластере
        districts = results[results["cluster"] == cluster_id]["district"].tolist()

        # перенос строк каждые 2 округа
        lines = []
        for i in range(0, len(districts), 2):
            lines.append(", ".join(districts[i:i+2]))

        districts_text = "\n".join(lines)

        plt.figure(figsize=(8,8))

        ax = plt.subplot(111, polar=True)

        ax.plot(angles, values)
        ax.fill(angles, values, alpha=0.25)

        ax.set_thetagrids(angles[:-1] * 180/np.pi, factors)

        title = f"Кластер {cluster_id}: {cluster_names.get(cluster_id,'')}\n({districts_text})"

        plt.title(title, pad=30)

        plt.savefig(f"plots/clusters/cluster_{cluster_id}.png",
                    dpi=300,
                    bbox_inches="tight")

        plt.close()