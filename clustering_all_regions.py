import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from math import pi
from sklearn.decomposition import PCA
import os


def run_global_clustering():
    print("Запуск глобальной кластеризации всех субъектов РФ...")

    conn = sqlite3.connect('digitalization.db')
    query = """
    SELECT r.name as region, i.name as indicator, v.value
    FROM values_data v
    JOIN regions r ON v.territory_id = r.id
    JOIN indicators i ON v.indicator_id = i.id
    WHERE v.territory_type = 'region'
    """
    df = pd.read_sql(query, conn)
    conn.close()

    # Формирование матрицы (строки - регионы, столбцы - факторы)
    matrix = df.pivot(index="region", columns="indicator", values="value")

    # Замена пропусков на минимальное значение по стране (для пенализации)
    matrix = matrix.fillna(matrix.min())

    # Масштабирование данных
    scaler = StandardScaler()
    X = scaler.fit_transform(matrix)

    # Метод локтя
    distortions = []
    K = range(1, 11)
    for k in K:
        kmeans_model = KMeans(n_clusters=k, random_state=42)
        kmeans_model.fit(X)
        distortions.append(kmeans_model.inertia_)

    plt.figure(figsize=(6, 4))
    plt.plot(K, distortions, marker='o', color='blue', linestyle='-')
    plt.xlabel('Количество кластеров (k)')
    plt.ylabel('Внутрикластерная ошибка')
    plt.title('Метод локтя\nВсе субъекты РФ')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('2_75_elbow_all_regions.png', dpi=300)
    plt.close()

    # Кластеризация (k=3)
    kmeans = KMeans(n_clusters=3, random_state=42)
    matrix['Cluster_Raw'] = kmeans.fit_predict(X)

    # Умная сортировка кластеров по логике ВКР
    means_initial = matrix.groupby('Cluster_Raw').mean(numeric_only=True)
    c_advanced = means_initial['ИИ'].idxmax()
    remaining = [c for c in means_initial.index if c != c_advanced]
    if means_initial.loc[remaining[0], 'Цифровые платформы'] > means_initial.loc[remaining[1], 'Цифровые платформы']:
        c_potential = remaining[0]
        c_outsider = remaining[1]
    else:
        c_potential = remaining[1]
        c_outsider = remaining[0]

    cluster_mapping = {c_advanced: 1, c_potential: 2, c_outsider: 3}
    matrix['Кластер'] = matrix['Cluster_Raw'].map(cluster_mapping)
    matrix = matrix.drop(columns=['Cluster_Raw'])

    cluster_names = {1: 'Передовые субъекты', 2: 'Субъекты с потенциалом развития', 3: 'Субъекты-аутсайдеры'}
    matrix['Описание кластера'] = matrix['Кластер'].map(cluster_names)

    # Сохранение таблицы регионов
    export_df = matrix[['Кластер', 'Описание кластера']].copy()
    export_df.index.name = 'Регион'
    export_df.sort_values(by=['Кластер', 'Регион'], inplace=True)
    export_df.to_excel('all_regions_clusters.xlsx')

    # Сохранение средних значений (с округлением)
    means = matrix.groupby('Кластер').mean(numeric_only=True).round(2)
    means.to_excel('Table_2_12_Cluster_Means.xlsx')

    # ----------------------------------------------------
    # ТЕПЛОВАЯ КАРТА В ЕДИНОМ СТИЛЕ ПРОЕКТА
    # ----------------------------------------------------
    plt.figure(figsize=(12, 6))
    sns.heatmap(
        means,  # Кластеры по Y, Показатели по X
        annot=True,
        fmt=".1f",
        cmap="YlOrRd",
        linewidths=0.5
    )
    plt.title("Различия факторов цифровизации между глобальными кластерами субъектов РФ")
    plt.ylabel("Кластеры")
    plt.xlabel("Показатели цифровизации")
    plt.tight_layout()
    plt.savefig('2_76_heatmap_all_regions.png', dpi=300)
    plt.close()

    # ----------------------------------------------------
    # ПОСТРОЕНИЕ ДИАГРАММ ДЛЯ КАЖДОГО КЛАСТЕРА
    # ----------------------------------------------------
    categories = means.columns.tolist()
    N = len(categories)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    for c in [1, 2, 3]:
        # Радарная диаграмма
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        values = means.loc[c].values.flatten().tolist()
        values += values[:1]

        ax.plot(angles, values, linewidth=2, linestyle='solid')
        ax.fill(angles, values, alpha=0.4)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=8)
        ax.set_title(f'{cluster_names[c]}', size=14, y=1.1)
        plt.tight_layout()
        radar_num = 2.78 if c == 1 else (2.80 if c == 2 else 2.82)
        plt.savefig(f'{str(radar_num).replace(".", "_")}_radar_cluster_{c}.png', dpi=300)
        plt.close()

        # СТОЛБЧАТАЯ ДИАГРАММА В ЕДИНОМ СТИЛЕ ПРОЕКТА
        plt.figure(figsize=(10, 6))
        vals = means.loc[c]  # Извлекаем данные одного кластера

        # Строим вертикальные столбцы встроенным методом pandas как в изначальном скрипте
        vals.plot(kind="bar")

        plt.title(f"Все субъекты РФ\nКластер {c} ({cluster_names[c]})")
        plt.ylabel("Среднее значение показателя")
        plt.xlabel("")  # Убираем подпись оси X, так как сами названия показателей всё объясняют
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        bar_num = 2.77 if c == 1 else (2.79 if c == 2 else 2.81)
        plt.savefig(f'{str(bar_num).replace(".", "_")}_bar_cluster_{c}.png', dpi=300)
        plt.close()

        # ----------------------------------------------------
        # ПОСТРОЕНИЕ ТОЧЕЧНОЙ ДИАГРАММЫ (SCATTER PLOT) С ПОМОЩЬЮ PCA
        # ----------------------------------------------------
        pca = PCA(n_components=2, random_state=42)
        X_pca = pca.fit_transform(X)

        # Проекция вычисленных центроидов в новое 2D пространство
        centroids_pca = pca.transform(kmeans.cluster_centers_)

        # Немного увеличим высоту графика, чтобы снизу поместилась легенда
        plt.figure(figsize=(10, 7.5))

        # Цветовая палитра для кластеров (в стиле viridis)
        colors = {1: '#fde725', 2: '#21918c', 3: '#440154'}

        # Отрисовка точек по каждому кластеру отдельно для формирования правильной легенды
        for c in [1, 2, 3]:
            idx = matrix['Кластер'] == c
            plt.scatter(
                X_pca[idx, 0], X_pca[idx, 1],
                c=colors[c],
                label=f'Точки кластера: {cluster_names[c]}',
                s=80, alpha=0.8, edgecolors='white', linewidth=0.5
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
        for raw_c, mapped_c in cluster_mapping.items():
            cx, cy = centroids_pca[raw_c, 0], centroids_pca[raw_c, 1]
            plt.annotate(
                f'Центр:\n{cluster_names[mapped_c]}',
                xy=(cx, cy),
                xytext=(0, 15),  # Сдвиг текста на 15 пикселей вверх от центра треугольника
                textcoords='offset points',
                ha='center', va='bottom',
                fontsize=9, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.9),
                zorder=6
            )

        plt.title(
            "Пространственное распределение кластеров субъектов РФ\n(Точечная диаграмма на основе метода главных компонент)")
        plt.xlabel("Главная компонента 1 (Агрегированный вектор базовых IT-решений)")
        plt.ylabel("Главная компонента 2 (Агрегированный вектор наукоемких инноваций)")

        # Размещение легенды под графиком
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=True)
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()

        # Сохранение точечной диаграммы
        plt.savefig('2_83_scatter_clusters.png', dpi=300, bbox_inches='tight')
        plt.close()

        print("Глобальная кластеризация завершена. Файлы сохранены в корне проекта в едином стиле.")
