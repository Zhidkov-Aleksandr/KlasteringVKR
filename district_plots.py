import matplotlib.pyplot as plt
import os


def plot_districts(data):

    os.makedirs("plots/districts", exist_ok=True)

    for district in data.index:

        values = data.loc[district]

        plt.figure(figsize=(10,6))

        values.plot(kind="bar")

        plt.title(district)
        plt.ylabel("Значение показателя")
        plt.xticks(rotation=45, ha="right")

        plt.tight_layout()

        filename = f"plots/districts/{district}.png"

        plt.savefig(filename, dpi=300)

        plt.close()