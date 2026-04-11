import matplotlib.pyplot as plt
import os

def plot_district_cluster_charts(data, cluster_labels):
    """
    Строит и сохраняет круговые диаграммы для каждого федерального округа.
    """
    # Создаем директорию, если она не существует
    os.makedirs("output/districts/plots", exist_ok=True)

    for district, values in data.iterrows():
        plt.figure(figsize=(8, 6))
        values.plot(kind='pie', autopct='%1.1f%%', startangle=90)
        plt.title(f'Показатели для {district}')
        plt.ylabel('')
        filename = f"output/districts/plots/{district}.png"
        plt.savefig(filename, dpi=300)
        plt.close()
