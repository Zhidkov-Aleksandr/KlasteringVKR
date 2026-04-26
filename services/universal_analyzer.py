import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
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
        plt.plot(K, distortions, marker='o', color='blue', linestyle='-', alpha=0.6)
        
        # Выделение точки k=3
        if 3 in K:
            k_idx = list(K).index(3)
            plt.plot(3, distortions[k_idx], marker='o', color='red', markersize=10, label='Оптимальное k=3')
            plt.annotate('Оптимум (k=3)', 
                         xy=(3, distortions[k_idx]), 
                         xytext=(3.5, distortions[k_idx] + (max(distortions)-min(distortions))*0.05),
                         arrowprops=dict(facecolor='red', shrink=0.05, width=1, headwidth=5),
                         fontsize=9, color='red', fontweight='bold')

        plt.xlabel('Количество кластеров (k)')
        plt.ylabel('Внутрикластерная ошибка (WCSS)')
        plt.title(f'Метод локтя\n{self.level_name}')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/diagrams/elbow_method.png", dpi=300)
        plt.close()

    # === ВАЛИДАЦИЯ ЧИСЛА КЛАСТЕРОВ (добавлено) ===
    def calculate_cluster_validation(self, chosen_k=3):
        """
        Расчет дополнительных метрик валидации: силуэт, Дэвис-Болдин, Калинский-Харабаш.
        """
        print(f"[{self.level_name}] Расчет метрик валидации (Силуэт, Дэвис-Болдин, Калинский-Харабаш)...")

        results = []
        inertias = []
        max_k = min(11, len(self.data))
        if max_k <= 2:
            print(f"[{self.level_name}] Недостаточно данных для расчета метрик валидации (нужно k >= 2).")
            return

        k_range = range(1, max_k)

        for k in k_range:
            model = KMeans(n_clusters=k, random_state=42, n_init=10)
            model.fit(self.X_scaled)
            inertias.append(model.inertia_)

            if k >= 2:
                labels = model.labels_
                sil = silhouette_score(self.X_scaled, labels)
                db = davies_bouldin_score(self.X_scaled, labels)
                ch = calinski_harabasz_score(self.X_scaled, labels)
                results.append({
                    'k': k,
                    'Silhouette': round(sil, 4),
                    'Davies-Bouldin': round(db, 4),
                    'Calinski-Harabasz': round(ch, 2)
                })

        # 2. РЕЗУЛЬТАТЫ В ТАБЛИЦЕ
        df_res = pd.DataFrame(results)
        df_print = df_res.copy()
        df_print['Оптимум'] = df_print['k'].apply(lambda x: ' <---' if x == chosen_k else '')
        print("\nЧисленное обоснование выбора числа кластеров:")
        print(df_print.to_string(index=False))

        # 3. КОМБИНИРОВАННЫЙ ГРАФИК
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle(f"Определение оптимального числа кластеров (k)\n{self.level_name}", fontsize=16, fontweight='bold')

        # Subplot 1: Метод локтя (SSE)
        axs[0, 0].plot(k_range, inertias, marker='o', color='blue', linestyle='-', alpha=0.7)
        axs[0, 0].set_title('Метод локтя (Inertia/WCSS)', fontsize=12)
        axs[0, 0].axvline(x=chosen_k, color='red', linestyle='--', label=f'Выбрано k={chosen_k}')
        axs[0, 0].set_ylabel('Inertia')
        axs[0, 0].legend()

        # Subplot 2: Коэффициент силуэта
        axs[0, 1].plot(df_res['k'], df_res['Silhouette'], marker='o', color='green', linestyle='-', alpha=0.7)
        axs[0, 1].set_title('Коэффициент силуэта (выше - лучше)', fontsize=12)
        best_sil_k = df_res.loc[df_res['Silhouette'].idxmax(), 'k']
        axs[0, 1].axvline(x=chosen_k, color='red', linestyle='--')
        axs[0, 1].axvline(x=best_sil_k, color='green', linestyle=':', label=f'Max Silh (k={best_sil_k})')
        axs[0, 1].set_ylabel('Score')
        axs[0, 1].legend()

        # Subplot 3: Индекс Дэвиса-Болдина
        axs[1, 0].plot(df_res['k'], df_res['Davies-Bouldin'], marker='o', color='orange', linestyle='-', alpha=0.7)
        axs[1, 0].set_title('Индекс Дэвиса-Болдина (ниже - лучше)', fontsize=12)
        best_db_k = df_res.loc[df_res['Davies-Bouldin'].idxmin(), 'k']
        axs[1, 0].axvline(x=chosen_k, color='red', linestyle='--')
        axs[1, 0].axvline(x=best_db_k, color='green', linestyle=':', label=f'Min DB (k={best_db_k})')
        axs[1, 0].set_ylabel('Score')
        axs[1, 0].legend()

        # Subplot 4: Индекс Калинского-Харабаша
        axs[1, 1].plot(df_res['k'], df_res['Calinski-Harabasz'], marker='o', color='purple', linestyle='-', alpha=0.7)
        axs[1, 1].set_title('Индекс Калинского-Харабаша (выше - лучше)', fontsize=12)
        best_ch_k = df_res.loc[df_res['Calinski-Harabasz'].idxmax(), 'k']
        axs[1, 1].axvline(x=chosen_k, color='red', linestyle='--')
        axs[1, 1].axvline(x=best_ch_k, color='green', linestyle=':', label=f'Max CH (k={best_ch_k})')
        axs[1, 1].set_ylabel('Score')
        axs[1, 1].legend()

        for ax in axs.flat:
            ax.set_xlabel('Количество кластеров (k)')
            ax.grid(True, linestyle='--', alpha=0.6)

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(f"{self.output_dir}/diagrams/cluster_validation.png", dpi=300)
        plt.close()

        # 4. ИТОГОВЫЙ ВЫВОД
        print(f"\nСводка методов: Локоть k={chosen_k} | Силуэт k={best_sil_k} | Дэвис-Болдин k={best_db_k} | Калинский-Харабаш k={best_ch_k}")
        if chosen_k == best_sil_k == best_db_k == best_ch_k:
            print(f"Консенсус: все методы подтверждают оптимальность k={chosen_k}.")
        else:
            print(f"Консенсус: методы дают разные рекомендации. k={chosen_k} сохранен согласно логике исследования.")

    # === DBSCAN ВАЛИДАЦИЯ (добавлено) ===
    def calculate_dbscan_validation(self, kmeans_k=3):
        """
        Дополнительная валидация через DBSCAN для оценки плотности и структуры кластеров.
        """
        print(f"\n[{self.level_name}] DBSCAN: запуск оценки числа кластеров через плотность...")

        # Получаем силуэт K-Means для сравнения
        kmeans_model = KMeans(n_clusters=kmeans_k, random_state=42, n_init=10)
        kmeans_labels = kmeans_model.fit_predict(self.X_scaled)
        kmeans_sil = silhouette_score(self.X_scaled, kmeans_labels)

        # 1. СЕТКА ПАРАМЕТРОВ
        eps_values = [round(x, 2) for x in list(np.arange(0.3, 2.1, 0.1))]
        min_samples_values = [3, 4, 5, 6, 7]
        dbscan_results = []

        for eps in eps_values:
            for ms in min_samples_values:
                db = DBSCAN(eps=eps, min_samples=ms).fit(self.X_scaled)
                labels = db.labels_

                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                noise_ratio = (labels == -1).sum() / len(labels)

                # Фильтрация по условиям задачи
                if 2 <= n_clusters <= 8 and noise_ratio <= 0.15:
                    # Считаем силуэт только для не-шумовых точек
                    mask = labels != -1
                    if len(set(labels[mask])) > 1:
                        sil = silhouette_score(self.X_scaled[mask], labels[mask])
                        dbscan_results.append({
                            'eps': eps,
                            'min_samples': ms,
                            'n_clusters': n_clusters,
                            'noise_ratio': round(noise_ratio * 100, 1),
                            'silhouette': round(sil, 4)
                        })

        if not dbscan_results:
            print("DBSCAN: подходящих конфигураций не найдено (k от 2 до 8, шум <= 15%).")
            return

        # 2. ТАБЛИЦА РЕЗУЛЬТАТОВ
        df_db = pd.DataFrame(dbscan_results).sort_values(by='silhouette', ascending=False)
        print("\nDBSCAN: подбор параметров (отфильтровано: 2≤k≤8, шум≤15%)")
        df_print = df_db.head(10).copy()
        df_print['best_mark'] = [' <--- лучший' if i == 0 else '' for i in range(len(df_print))]

        # Переименуем для красивого вывода
        print(df_print[['eps', 'min_samples', 'n_clusters', 'noise_ratio', 'silhouette', 'best_mark']].to_string(index=False))

        # 3. ЛУЧШИЙ РЕЗУЛЬТАТ И СРАВНЕНИЕ
        best = df_db.iloc[0]
        print(f"\nDBSCAN лучший результат: eps={best['eps']}, min_samples={best['min_samples']} → k={int(best['n_clusters'])} кластеров, шум={best['noise_ratio']}%, силуэт={best['silhouette']}")
        print(f"Сравнение: K-Means k={kmeans_k} (силуэт={round(kmeans_sil, 4)}) vs DBSCAN k={int(best['n_clusters'])} (силуэт={best['silhouette']})")

        if best['silhouette'] > kmeans_sil:
            print("DBSCAN показал лучшее разделение — рассмотреть как дополнительный метод")
        else:
            print("K-Means с k=3 превосходит DBSCAN по качеству разделения — выбор подтверждён")

        # 4. ГРАФИК
        plt.figure(figsize=(10, 6))

        # Размер точек обратно пропорционален шуму (минимум 20, чтобы было видно)
        sizes = [max(20, 200 * (1 - r/100)) for r in df_db['noise_ratio']]

        scatter = plt.scatter(
            df_db['n_clusters'],
            df_db['silhouette'],
            c=df_db['min_samples'],
            s=sizes,
            cmap='viridis',
            alpha=0.6,
            edgecolors='w'
        )

        # Аннотация лучшей точки
        plt.annotate(
            f"Best: eps={best['eps']}, ms={best['min_samples']}",
            xy=(best['n_clusters'], best['silhouette']),
            xytext=(best['n_clusters'] + 0.2, best['silhouette']),
            arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
            fontsize=9, fontweight='bold'
        )

        # Линия K-Means
        plt.axhline(y=kmeans_sil, color='red', linestyle='--', label=f"K-Means k={kmeans_k} (силуэт={round(kmeans_sil, 4)})")

        plt.title("DBSCAN: силуэт по числу найденных кластеров", fontsize=14)
        plt.xlabel("Количество найденных кластеров (k)", fontsize=11)
        plt.ylabel("Коэффициент силуэта (non-noise)", fontsize=11)

        cbar = plt.colorbar(scatter)
        cbar.set_label('min_samples')
        plt.legend(loc='lower right')
        plt.grid(True, linestyle='--', alpha=0.5)

        os.makedirs(f"{self.output_dir}/plots", exist_ok=True)
        plt.savefig(f"{self.output_dir}/plots/dbscan_validation.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"График DBSCAN сохранен: {self.output_dir}/plots/dbscan_validation.png")

    # === КОНЕЦ DBSCAN ВАЛИДАЦИИ ===

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

    def get_pca_plotly(self):
        """Возвращает интерактивную фигуру Plotly для отображения в Streamlit"""
        if len(self.data) < 2:
            return None

        pca = PCA(n_components=2, random_state=42)
        X_pca = pca.fit_transform(self.X_scaled)
        
        # Подготовка данных для Plotly
        plot_df = pd.DataFrame(
            X_pca, 
            columns=['PC1', 'PC2'], 
            index=self.data.index
        )
        plot_df['Кластер'] = self.data['Кластер'].astype(str)
        plot_df['Описание'] = self.data['Описание кластера']
        plot_df['Объект'] = self.data.index

        # Цвета как в статичном графике
        color_map = {
            '1': '#fde725', 
            '2': '#21918c', 
            '3': '#440154'
        }

        fig = px.scatter(
            plot_df, 
            x='PC1', 
            y='PC2', 
            color='Кластер',
            hover_name='Объект',
            hover_data={'Кластер': True, 'Описание': True, 'PC1': False, 'PC2': False},
            color_discrete_map=color_map,
            title=f"Интерактивное распределение: {self.level_name}",
            labels={'PC1': 'Главная компонента 1', 'PC2': 'Главная компонента 2'}
        )

        fig.update_traces(marker=dict(size=12, line=dict(width=1, color='White')))
        fig.update_layout(legend_title_text='Кластер')
        
        return fig

    def get_choropleth_plotly(self):
        """Создает интерактивную карту РФ с кластерами"""
        # Оставляем карту ТОЛЬКО для глобального уровня (Все субъекты РФ)
        if "Все субъекты РФ" not in self.level_name:
            return None

        import requests
        
        # НОВАЯ РАБОЧАЯ ССЫЛКА
        geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/russia.geojson"
        try:
            response = requests.get(geojson_url, timeout=10)
            if response.status_code != 200:
                return None
            repo = response.json()
        except:
            return None

        # Подготовка данных
        plot_df = self.data.copy()
        plot_df['Region'] = plot_df.index
        
        # Добавляем ключ для маппинга в GeoJSON
        for feature in repo['features']:
            feature['id'] = feature['properties']['name']

        color_map = {'1': '#fde725', '2': '#21918c', '3': '#440154'}

        fig = px.choropleth(
            plot_df,
            geojson=repo,
            locations='Region',
            color=plot_df['Кластер'].astype(str),
            color_discrete_map=color_map,
            hover_name='Region',
            hover_data={'Кластер': True, 'Описание кластера': True},
            title=f"Географическое распределение кластеров: {self.level_name}",
            labels={'color': 'Кластер'},
            height=700 # Увеличиваем высоту фигуры
        )

        fig.update_geos(
            visible=False, 
            fitbounds="locations", # Автоматически подгоняет масштаб под Россию
        )
        
        fig.update_layout(
            margin={"r":0,"t":50,"l":0,"b":0},
            legend_title_text='Кластер'
        )
        
        return fig

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
        print(f"[{self.level_name}] Начало полного цикла анализа...")
        self.plot_elbow()
        self.calculate_cluster_validation(chosen_k=k)
        self.calculate_dbscan_validation(kmeans_k=k)
        self.run_clustering(k=k)
        self.export_tables()
        self.plot_heatmap()
        self.plot_pca_scatter()
        
        # Сохраняем интерактивную версию PCA
        try:
            fig_pca = self.get_pca_plotly()
            if fig_pca:
                path_pca = f"{self.output_dir}/plots/pca_interactive.html"
                fig_pca.write_html(path_pca)
                print(f"[{self.level_name}] PCA HTML сохранен: {path_pca}")
        except Exception as e:
            print(f"[{self.level_name}] Ошибка сохранения PCA HTML: {e}")
            
        # Сохраняем интерактивную карту
        try:
            fig_map = self.get_choropleth_plotly()
            if fig_map:
                path_map = f"{self.output_dir}/plots/map_interactive.html"
                fig_map.write_html(path_map)
                print(f"[{self.level_name}] Карта HTML сохранена: {path_map}")
            else:
                print(f"[{self.level_name}] Карта не создана (get_choropleth_plotly вернул None)")
        except Exception as e:
            print(f"[{self.level_name}] Ошибка сохранения Карты HTML: {e}")
            
        self.plot_radars_and_bars()
        print(f"[{self.level_name}] Анализ успешно завершен!")
