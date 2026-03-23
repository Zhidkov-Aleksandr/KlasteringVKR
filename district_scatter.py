import os
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


def plot_district_scatter(data, clusters, centers):
    # Масштабируем данные заново, так как KMeans обучался на стандартизированных данных
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(data)

    # ----------------------------------------------------
    # ПОСТРОЕНИЕ ТОЧЕЧНОЙ ДИАГРАММЫ (SCATTER PLOT) С ПОМОЩЬЮ PCA
    # ----------------------------------------------------
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)

    # Проекция вычисленных центроидов в новое 2D пространство
    centroids_pca = pca.transform(centers)

    # Немного увеличим высоту графика, чтобы снизу поместилась легенда
    plt.figure(figsize=(10, 7.5))

    # Цветовая палитра для кластеров (в стиле viridis)
    colors = {1: '#fde725', 2: '#21918c', 3: '#440154'}

    # Названия кластеров для округов
    cluster_names = {
        1: "Передовые округа",
        2: "Округа с потенциалом развития",
        3: "Округа-аутсайдеры"
    }

    # Отрисовка точек по каждому кластеру отдельно
    for c in [1, 2, 3]:
        # Массив булевых значений для фильтрации нужного кластера
        idx = (clusters == c)

        plt.scatter(
            X_pca[idx, 0], X_pca[idx, 1],
            c=colors[c],
            label=f'Точки кластера: {cluster_names[c]}',
            s=120, alpha=0.8, edgecolors='white', linewidth=0.5
        )

        # Добавим текстовые подписи названий самих округов рядом с точками
        for i, district_name in enumerate(data.index[idx]):
            # Сократим "федеральный округ" до "ФО", чтобы график был аккуратным
            short_name = district_name.replace(" федеральный округ", " ФО")
            plt.annotate(
                short_name,
                xy=(X_pca[idx, 0][i], X_pca[idx, 1][i]),
                xytext=(6, 6),  # небольшой сдвиг текста от точки
                textcoords='offset points',
                fontsize=8,
                alpha=0.9,
                zorder=7
            )

    # Отрисовка центроидов (красные треугольники)
    plt.scatter(
        centroids_pca[:, 0],
        centroids_pca[:, 1],
        c='red',
        s=250,
        marker='^',
        label='Центроиды',
        edgecolors='black',
        zorder=5  # Выводим поверх всех остальных точек
    )

    # Добавление текстовых подписей к каждому центроиду
    for raw_c in range(len(centers)):
        cx, cy = centroids_pca[raw_c, 0], centroids_pca[raw_c, 1]

        # Индексы центроидов (из KMeans) начинаются с 0, а наши кластеры с 1
        mapped_c = raw_c + 1

        plt.annotate(
            f'Центр:\n{cluster_names[mapped_c]}',
            xy=(cx, cy),
            xytext=(0, 15),
            textcoords='offset points',
            ha='center', va='bottom',
            fontsize=9, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.9),
            zorder=6
        )

    plt.title(
        "Пространственное распределение кластеров федеральных округов\n(Точечная диаграмма на основе метода главных компонент)")
    plt.xlabel("Главная компонента 1")
    plt.ylabel("Главная компонента 2")

    # Размещение легенды под графиком
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=True)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()

    # Сохранение точечной диаграммы в папку с остальными графиками округов
    os.makedirs("plots/districts", exist_ok=True)
    plt.savefig('plots/districts/district_scatter_clusters.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("Точечная диаграмма (scatter plot) для федеральных округов успешно сохранена.")