import matplotlib.pyplot as plt
import os


def plot_factor_ranking(factors):

    os.makedirs("plots", exist_ok=True)

    factors_sorted = factors.sort_values(ascending=False)

    plt.figure(figsize=(10,6))

    factors_sorted.plot(kind="bar")

    plt.title("Ранжирование факторов различий между кластерами федеральных округов")

    plt.xlabel("Показатели цифровизации")
    plt.ylabel("Степень различий между кластерами")

    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()

    plt.savefig("plots/factor_ranking.png", dpi=300)

    plt.close()