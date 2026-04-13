import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
from math import pi
import os


class UniversalClusterAnalyzer:
    """
    Универсальный класс для проведения кластерного анализа,
    генерации таблиц и построения всех необходимых визуализаций
    (метод локтя, тепловая карта, PCA-точечная диаграмма, радары, столбчатые диаграммы).
    """

    def __init__(self, data: pd.DataFrame, output_dir: str, level_name: str):
        """
        :param data: Датафрейм, где индексы - это объекты кластеризации (Округа, Регионы и т.д.),
                     а столбцы - факторы (показатели цифровизации).
        :param output_dir: Базовая папка для сохранения результатов (например, 'output/districts').
        :param level_name: Название уровня для графиков (например, 'Федеральные округа').
        """
        self.data = data.copy()
        
        # Заменяем пропуски минимальными значениями по столбцу (пенализация за отсутствие данных)
        self.data = self.data.apply(lambda col: col.fillna(col.min()))
        
        self.output_dir = output_dir
        self.level_name = level_name
        self.scaler = StandardScaler()
        self.X_scaled = self.scaler.fit_transform(self.data)
        
        self.n_clusters = None
        self.kmeans = None
        self.cluster_labels = None
        self.cluster_means = None
        self.cluster_names_map = {}

        # Создаем нужные директории
        os.makedirs(f"{self.output_dir}/diagrams", exist_ok=True)
        os.makedirs(f"{self.output_dir}/tables", exist_ok=True)
        os.makedirs(f"{self.output_dir}/plots", exist_ok=True)

    def plot_elbow(self):
        """1. Метод локтя"""
        print(f"[{self.level_name}] Расчет оптимального числа кластеров (Метод локтя)...")
        distortions = []
        max_k = min(11, len(self.data))
        if max_k <= 1: max_k = 2
        K = range(1, max_k)
        
        for k in K:
            model = KMeans(n_clusters=k, random_state=42, n_init=10)
            model.fit(self.X_scaled)
            distortions.append(model.inertia_)

        plt.figure(figsize=(6, 4))
        plt.plot(K, distortions, marker='o', color='blue', linestyle='-')
        plt.xlabel('Количество кластеров (k)')
        plt.ylabel('Внутрикластерная ошибка (WCSS)')
        plt.title(f'Метод локтя\n{self.level_name}')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/diagrams/elbow_method.png", dpi=300)
        plt.close()

    def run_clustering(self, k=3):
        """Выполнение K-Means и логическая сортировка кластеров"""
        print(f"[{self.level_name}] Выполнение кластеризации (K-Means, k={k})...")
        self.n_clusters = min(k, len(self.data))
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        
        # Получаем сырые метки
        raw_labels = self.kmeans.fit_predict(self.X_scaled)
        self.data['Cluster_Raw'] = raw_labels
        
        # Умная сортировка кластеров по уровню развития
        means_initial = self.data.groupby('Cluster_Raw').mean(numeric_only=True)
        
        cluster_mapping = {}
        if self.n_clusters == 3:
            # Пытаемся найти лидера по ключевым факторам, например 'ИИ' или среднему скору
            if 'ИИ' in means_initial.columns:
                c_advanced = means_initial['ИИ'].idxmax()
            else:
                c_advanced = means_initial.mean(axis=1).idxmax()
                
            remaining = [c for c in means_initial.index if c != c_advanced]
            
            # Сравниваем оставшиеся два по Платформам или общему скору
            score_col = 'Цифровые платформы' if 'Цифровые платформы' in means_initial.columns else means_initial.columns[0]
            if means_initial.loc[remaining[0], score_col] > means_initial.loc[remaining[1], score_col]:
                c_potential = remaining[0]
                c_outsider = remaining[1]
            else:
                c_potential = remaining[1]
                c_outsider = remaining[0]
            cluster_mapping = {c_advanced: 1, c_potential: 2, c_outsider: 3}
            
        elif self.n_clusters == 2:
            scores = means_initial.mean(axis=1).sort_values(ascending=False)
            cluster_mapping = {scores.index[0]: 1, scores.index[1]: 3}
        else:
            cluster_mapping = {c: c+1 for c in range(self.n_clusters)}
            
        self.data['Кластер'] = self.data['Cluster_Raw'].map(cluster_mapping)
        self.data.drop(columns=['Cluster_Raw'], inplace=True)
        
        # Задаем имена кластерам
        names_dict = {1: 'Передовые', 2: 'С потенциалом развития', 3: 'Аутсайдеры'}
        self.data['Описание кластера'] = self.data['Кластер'].map(names_dict).fillna("Кластер")
        
        self.cluster_means = self.data.groupby('Кластер').mean(numeric_only=True).round(2)
        self.cluster_names_map = {c: names_dict.get(c, f"Кластер {c}") for c in self.cluster_means.index}

    def export_tables(self):
        """2. и 3. Сохранение Excel таблиц"""
        print(f"[{self.level_name}] Сохранение таблиц кластеризации...")
        
        # Таблица принадлежности
        export_df = self.data[['Кластер', 'Описание кластера']].copy()
        export_df.sort_values(by=['Кластер', export_df.index.name if export_df.index.name else 'index'], inplace=True)
        export_df.to_excel(f"{self.output_dir}/tables/cluster_assignments.xlsx")
        
        # Таблица средних значений
        self.cluster_means.to_excel(f"{self.output_dir}/tables/cluster_means.xlsx")

    def plot_heatmap(self):
        """4. Тепловая карта различий"""
        print(f"[{self.level_name}] Генерация тепловой карты...")
        plt.figure(figsize=(12, 6))
        sns.heatmap(
            self.cluster_means,
            annot=True,
            fmt=".1f",
            cmap="YlOrRd",
            linewidths=0.5
        )
        plt.title(f"Различия факторов цифровизации\n({self.level_name})")
        plt.ylabel("Кластеры")
        plt.xlabel("Показатели")
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/plots/heatmap_factors.png", dpi=300)
        plt.close()

    def plot_pca_scatter(self):
        """5. Точечная диаграмма (PCA)"""
        print(f"[{self.level_name}] Построение 2D проекции PCA...")
        
        # Если количество уникальных точек меньше 2, PCA работать не будет
        if len(self.data) < 2:
            print(f"[{self.level_name}] Пропуск PCA: недостаточно данных (менее 2 объектов)")
            return

        pca = PCA(n_components=2, random_state=42)
        X_pca = pca.fit_transform(self.X_scaled)

        # Считаем центроиды вручную на основе уже отмапленных данных, чтобы избежать путаницы с метками
        centroids_pca = []
        valid_clusters = []
        for c in sorted(self.data['Кластер'].unique()):
            idx = self.data['Кластер'] == c
            if any(idx):
                centroids_pca.append(X_pca[idx].mean(axis=0))
                valid_clusters.append(c)
        
        if not centroids_pca:
            return
            
        centroids_pca = np.array(centroids_pca)

        plt.figure(figsize=(10, 7.5))
        colors = {1: '#fde725', 2: '#21918c', 3: '#440154'}

        for i, c in enumerate(valid_clusters):
            idx = self.data['Кластер'] == c
            plt.scatter(
                X_pca[idx, 0], X_pca[idx, 1],
                c=colors.get(c, '#000000'),
                label=f"{self.cluster_names_map.get(c, str(c))}",
                s=100, alpha=0.8, edgecolors='white', linewidth=0.5
            )

            # Отрисовка центроидов
            cx, cy = centroids_pca[i, 0], centroids_pca[i, 1]
            plt.scatter(cx, cy, c='red', s=250, marker='^', edgecolors='black', zorder=5)
            
            plt.annotate(
                f'Центр:\n{self.cluster_names_map.get(c, str(c))}',
                xy=(cx, cy), xytext=(0, 15), textcoords='offset points',
                ha='center', va='bottom', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.9), zorder=6
            )

        plt.title(f"Пространственное распределение кластеров (PCA)\n{self.level_name}")
        plt.xlabel("Главная компонента 1")
        plt.ylabel("Главная компонента 2")
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=True)
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/plots/pca_scatter.png", dpi=300, bbox_inches='tight')
        plt.close()

    def plot_radars_and_bars(self):
        """6. Детализация по кластерам (радары и столбчатые диаграммы)"""
        print(f"[{self.level_name}] Построение радарных и столбчатых диаграмм...")
        categories = self.cluster_means.columns.tolist()
        N = len(categories)
        angles = [n / float(N) * 2 * pi for n in range(N)]
        angles += angles[:1]

        for c in self.cluster_means.index:
            # Радар
            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
            values = self.cluster_means.loc[c].values.flatten().tolist()
            values += values[:1]

            ax.plot(angles, values, linewidth=2, linestyle='solid')
            ax.fill(angles, values, alpha=0.4)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, size=8)
            ax.set_title(f"Профиль: {self.cluster_names_map.get(c, str(c))}", size=14, y=1.1)
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/diagrams/radar_cluster_{c}.png", dpi=300)
            plt.close()

            # Барчарт
            plt.figure(figsize=(10, 6))
            vals = self.cluster_means.loc[c]
            vals.plot(kind="bar")
            plt.title(f"Средние значения факторов\n{self.level_name} - Кластер {c} ({self.cluster_names_map.get(c, '')})")
            plt.ylabel("Значение")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/plots/bar_cluster_{c}.png", dpi=300)
            plt.close()

    def run_all(self, k=3):
        """Запуск всего цикла анализа для уровня"""
        self.plot_elbow()
        self.run_clustering(k=k)
        self.export_tables()
        self.plot_heatmap()
        self.plot_pca_scatter()
        self.plot_radars_and_bars()
        print(f"[{self.level_name}] Анализ успешно завершен!")
