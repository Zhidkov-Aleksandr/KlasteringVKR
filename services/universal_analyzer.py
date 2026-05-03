import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
        self.data = data.copy()
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
        self.elbow_K = None          # K values from elbow calculation
        self.elbow_distortions = None # Distortion/inertia values from elbow
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

        # Store elbow data for later use in global comparisons
        self.elbow_K = K
        self.elbow_distortions = distortions

        plt.figure(figsize=(8, 5))
        plt.plot(K, distortions, marker='o', color='blue', linestyle='-', alpha=0.7)
        
        if 3 in K:
            k_idx = list(K).index(3)
            plt.plot(3, distortions[k_idx], marker='o', color='red', markersize=10, label='Оптимальное k=3')
            plt.annotate('Оптимум (k=3)', 
                         xy=(3, distortions[k_idx]), 
                         xytext=(3.5, distortions[k_idx] + (max(distortions)-min(distortions))*0.05),
                         arrowprops=dict(facecolor='red', shrink=0.05, width=1, headwidth=5),
                         fontsize=10, color='red', fontweight='bold')

        plt.xlabel('Количество кластеров (k)', fontsize=12)
        plt.ylabel('Внутрикластерная ошибка (WCSS)', fontsize=12)
        plt.title(f'Метод локтя\n{self.level_name}', fontsize=14)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/diagrams/elbow_method.png", dpi=300)
        plt.close()

    def calculate_and_plot_validation_metrics(self, chosen_k=3):
        """Расчет и построение графиков для метрик валидации кластеризации."""
        print(f"[{self.level_name}] Расчет метрик валидации (Силуэт, Дэвис-Болдин, Калинский-Харабаш)...")
        results = []
        max_k = min(11, len(self.data))
        if max_k <= 2:
            print(f"[{self.level_name}] Недостаточно данных для расчета метрик валидации.")
            return None

        k_range = range(2, max_k)
        for k in k_range:
            model = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = model.fit_predict(self.X_scaled)
            sil = silhouette_score(self.X_scaled, labels)
            db = davies_bouldin_score(self.X_scaled, labels)
            ch = calinski_harabasz_score(self.X_scaled, labels)
            results.append({'k': k, 'Силуэт': sil, 'Дэвис-Болдин': db, 'Калинский-Харабаш': ch})

        df_res = pd.DataFrame(results)
        
        # --- Построение и сохранение отдельных графиков ---
        # Коэффициент силуэта
        plt.figure(figsize=(8, 5))
        plt.plot(df_res['k'], df_res['Силуэт'], marker='o', color='green', linestyle='-', alpha=0.7)
        plt.title(f'Коэффициент силуэта\n({self.level_name})', fontsize=14)
        plt.xlabel('Количество кластеров (k)', fontsize=12)
        plt.ylabel('Значение', fontsize=12)
        plt.axvline(x=df_res.loc[df_res['Силуэт'].idxmax(), 'k'], color='red', linestyle='--', label='Оптимум')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/diagrams/silhouette_score.png", dpi=300)
        plt.close()

        # Индекс Дэвиса-Болдина
        plt.figure(figsize=(8, 5))
        plt.plot(df_res['k'], df_res['Дэвис-Болдин'], marker='o', color='orange', linestyle='-', alpha=0.7)
        plt.title(f'Индекс Дэвиса-Болдина\n({self.level_name})', fontsize=14)
        plt.xlabel('Количество кластеров (k)', fontsize=12)
        plt.ylabel('Значение', fontsize=12)
        plt.axvline(x=df_res.loc[df_res['Дэвис-Болдин'].idxmin(), 'k'], color='red', linestyle='--', label='Оптимум')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/diagrams/davies_bouldin_score.png", dpi=300)
        plt.close()

        # Индекс Калинского-Харабаша
        plt.figure(figsize=(8, 5))
        plt.plot(df_res['k'], df_res['Калинский-Харабаш'], marker='o', color='purple', linestyle='-', alpha=0.7)
        plt.title(f'Индекс Калинского-Харабаша\n({self.level_name})', fontsize=14)
        plt.xlabel('Количество кластеров (k)', fontsize=12)
        plt.ylabel('Значение', fontsize=12)
        plt.axvline(x=df_res.loc[df_res['Калинский-Харабаш'].idxmax(), 'k'], color='red', linestyle='--', label='Оптимум')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/diagrams/calinski_harabasz_score.png", dpi=300)
        plt.close()

        # Возвращаем оптимальные значения
        return {
            'Коэффициент силуэта': df_res.loc[df_res['Силуэт'].idxmax(), 'k'],
            'Индекс Дэвиса-Болдина': df_res.loc[df_res['Дэвис-Болдин'].idxmin(), 'k'],
            'Индекс Калинского-Харабаша': df_res.loc[df_res['Калинский-Харабаш'].idxmax(), 'k']
        }

    def calculate_dbscan_validation(self):
        """Валидация через DBSCAN для оценки плотности и структуры кластеров."""
        print(f"\n[{self.level_name}] DBSCAN: запуск оценки числа кластеров...")
        eps_values = [round(x, 2) for x in np.arange(0.3, 2.1, 0.1)]
        min_samples_values = [3, 4, 5]
        dbscan_results = []

        for eps in eps_values:
            for ms in min_samples_values:
                db = DBSCAN(eps=eps, min_samples=ms).fit(self.X_scaled)
                labels = db.labels_
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                noise_ratio = (labels == -1).sum() / len(labels)
                if 2 <= n_clusters <= 8 and noise_ratio <= 0.15:
                    mask = labels != -1
                    if len(set(labels[mask])) > 1:
                        sil = silhouette_score(self.X_scaled[mask], labels[mask])
                        dbscan_results.append({'eps': eps, 'min_samples': ms, 'n_clusters': n_clusters, 'noise_ratio': noise_ratio, 'silhouette': sil})
        
        if not dbscan_results:
            print("DBSCAN: подходящих конфигураций не найдено.")
            return None

        df_db = pd.DataFrame(dbscan_results).sort_values(by='silhouette', ascending=False)
        best = df_db.iloc[0]
        
        # График
        plt.figure(figsize=(10, 6))
        sizes = [max(20, 200 * (1 - r)) for r in df_db['noise_ratio']]
        scatter = plt.scatter(df_db['n_clusters'], df_db['silhouette'], c=df_db['min_samples'], s=sizes, cmap='viridis', alpha=0.6, edgecolors='w')
        plt.annotate(f"Best: k={int(best['n_clusters'])}\neps={best['eps']}, ms={best['min_samples']}", xy=(best['n_clusters'], best['silhouette']), xytext=(best['n_clusters'] + 0.2, best['silhouette']), arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5))
        plt.title("DBSCAN: силуэт по числу найденных кластеров", fontsize=14)
        plt.xlabel("Количество кластеров (k)", fontsize=11)
        plt.ylabel("Коэффициент силуэта", fontsize=11)
        cbar = plt.colorbar(scatter)
        cbar.set_label('Мин. количество образцов (min_samples)')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.savefig(f"{self.output_dir}/diagrams/dbscan_validation.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        return {'DBSCAN': int(best['n_clusters'])}

    @staticmethod
    def plot_consensus_dashboard(consensus_df, output_path):
        """Создает интерактивный дашборд для консенсуса по выбору k."""
        if consensus_df.empty:
            return
        
        fig = px.bar(
            consensus_df,
            x='Метод',
            y='Оптимальное k',
            color='Метод',
            text='Оптимальное k',
            title='Консенсус по выбору оптимального числа кластеров (k)'
        )
        fig.update_traces(textposition='outside', textfont_size=14)
        fig.update_layout(
            yaxis=dict(tickmode='linear', dtick=1, range=[0, consensus_df['Оптимальное k'].max() + 1]),
            height=500,
            showlegend=False,
            xaxis_title="",
            yaxis_title="Рекомендуемое число кластеров",
            title_font_size=18
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.write_html(output_path)

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
        plt.xticks(rotation=90, ha="center")
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
            # Увеличиваем width до 0.8, чтобы уменьшить зазоры между столбиками
            vals.plot(kind="bar", width=0.8, color='#3498db', edgecolor='black', alpha=0.8)
            plt.title(f"Средние значения факторов\n{self.level_name} - Кластер {c} ({self.cluster_names_map.get(c, '')})")
            plt.ylabel("Значение показателя")
            plt.xlabel("Показатель использования цифровых технологий")
            plt.xticks(rotation=90, ha="center")
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/plots/bar_cluster_{c}.png", dpi=300)
            plt.close()

    def plot_comparison_radars(self):
        """Обобщающая радарная диаграмма: сравнение всех кластеров на одном графике"""
        print(f"[{self.level_name}] Построение обобщающей радарной диаграммы...")
        categories = self.cluster_means.columns.tolist()
        N = len(categories)
        angles = [n / float(N) * 2 * pi for n in range(N)]
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        
        colors = {1: '#fde725', 2: '#21918c', 3: '#440154'}
        
        for c in self.cluster_means.index:
            values = self.cluster_means.loc[c].values.flatten().tolist()
            values += values[:1]
            
            c_color = colors.get(c, '#888888')
            c_name = self.cluster_names_map.get(c, str(c))
            
            ax.plot(angles, values, linewidth=2, linestyle='solid', color=c_color, label=f"Кластер {c}: {c_name}")
            ax.fill(angles, values, alpha=0.1, color=c_color)
            
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=9)
        plt.title(f"Сравнительный анализ кластеров по факторам цифровизации\n({self.level_name})", size=14, y=1.1, fontweight='bold')
        
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/plots/clusters_comparison_radar.png", dpi=300, bbox_inches='tight')
        plt.close()

    def plot_comparison_bars(self):
        """7. Обобщающая диаграмма: сравнение всех кластеров на одном графике"""
        print(f"[{self.level_name}] Построение сравнительной диаграммы кластеров...")
        
        df_plot = self.cluster_means.T
        colors = {1: '#fde725', 2: '#21918c', 3: '#440154'}
        current_colors = [colors.get(c, '#888888') for c in self.cluster_means.index]
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Группы столбиков максимально близко друг к другу (width=0.9)
        df_plot.plot(kind='bar', ax=ax, width=0.9, color=current_colors, edgecolor='black', alpha=0.9)
        
        plt.title(f"Сравнительный анализ кластеров по факторам цифровизации\n({self.level_name})", fontsize=16, fontweight='bold')
        plt.ylabel("Среднее значение показателя", fontsize=14)
        plt.xlabel("Показатель использования цифровых технологий", fontsize=14)
        
        handles, labels = ax.get_legend_handles_labels()
        new_labels = [f"Кластер {l}: {self.cluster_names_map.get(int(l), '')}" for l in labels]
        plt.legend(handles, new_labels, loc='upper right', frameon=True, shadow=True, fontsize='medium')
        
        # Вертикальные подписи для ВКР
        plt.xticks(rotation=90, ha="center", fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        plt.tight_layout()
        
        plt.savefig(f"{self.output_dir}/plots/clusters_comparison.png", dpi=300)
        plt.close()

    def plot_comparison_bars_split(self):
        """Новая обобщающая диаграмма, разделенная на 2 части (кластеры 1-2 вверх, кластер 3 вниз)"""
        print(f"[{self.level_name}] Построение разделенной сравнительной диаграммы кластеров...")
        
        df_plot = self.cluster_means.T.copy()
        
        if 3 not in df_plot.columns:
            print(f"[{self.level_name}] Пропуск разделенной диаграммы: требуется 3 кластера.")
            return

        # Делаем значения для кластера 3 отрицательными
        df_plot[3] = df_plot[3] * -1
        
        colors = {1: '#fde725', 2: '#21918c', 3: '#440154'}
        current_colors = [colors.get(c, '#888888') for c in df_plot.columns]
        
        fig, ax = plt.subplots(figsize=(16, 12)) # Более вытянутая по вертикали
        
        # Строим бары
        df_plot.plot(kind='bar', ax=ax, width=0.9, color=current_colors, edgecolor='black', alpha=0.9, zorder=2)
        
        # Линия нуля
        ax.axhline(0, color='black', linewidth=1.5, zorder=3)
        
        ax.set_title(f"Сравнительный анализ кластеров (разделенный вид)\n({self.level_name})", fontsize=18, fontweight='bold')
        
        # Легенда
        handles, labels = ax.get_legend_handles_labels()
        new_labels = [f"Кластер {l}: {self.cluster_names_map.get(int(l), '')}" for l in labels]
        ax.legend(handles, new_labels, loc='upper right', frameon=True, shadow=True, fontsize='medium')
        
        ax.set_ylabel("Значение показателя", fontsize=14)
        ax.set_xlabel("") # Убираем общую подпись оси X
        
        # Скрываем стандартные подписи оси X, так как мы добавим свои по центру
        ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)

        # Делаем значения по оси Y абсолютными, чтобы кластер 3 не казался "отрицательным" в реальности
        yticks = ax.get_yticks()
        ax.set_yticklabels([f'{abs(y):.0f}' for y in yticks], fontsize=12)
        
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Добавляем текстовые метки показателей ровно по линии нуля
        for i, name in enumerate(df_plot.index):
            # Текст в прямоугольнике для читаемости поверх линии
            ax.text(i, 0, f' {name} ', ha='center', va='center', rotation=90, fontsize=11, fontweight='bold', zorder=4,
                    bbox=dict(facecolor='white', edgecolor='none', pad=2, alpha=0.8))

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        plt.savefig(f"{self.output_dir}/plots/clusters_comparison_split.png", dpi=300)
        plt.close()

    @staticmethod
    def plot_meso_comparison_interactive(combined_df, output_path):
        """
        Интерактивная диаграмма для мезо-уровня (Plotly).
        """
        if combined_df.empty:
            return

        print(f"Генерация интерактивного глобального сравнения мезо-уровня (все ФО)...")
        
        service_cols = ['Округ', 'Кластер', 'Описание кластера', 'Cluster_Raw', 'Кластер_ID']
        indicators = [c for c in combined_df.columns if c not in service_cols]
        
        id_vars = ['Округ', 'Кластер']
        if 'Описание кластера' in combined_df.columns:
            id_vars.append('Описание кластера')
            
        df_melted = combined_df.melt(
            id_vars=id_vars, 
            value_vars=indicators,
            var_name='Показатель', 
            value_name='Значение'
        )
        
        df_melted['ID'] = df_melted['Округ'] + " - Кл. " + df_melted['Кластер'].astype(str)
        df_melted = df_melted.sort_values(['Показатель', 'Округ', 'Кластер'])

        unique_districts = sorted(df_melted['Округ'].unique())
        dist_palette = sns.color_palette("tab10", len(unique_districts)).as_hex()
        dist_color_map = dict(zip(unique_districts, dist_palette))
        
        fig = go.Figure()
        
        unique_ids = sorted(df_melted['ID'].unique(), key=lambda x: (x.split(" - ")[0], x.split("Кл. ")[1]))

        for uid in unique_ids:
            df_sub = df_melted[df_melted['ID'] == uid]
            dist_name = df_sub['Округ'].iloc[0]
            cluster_num = df_sub['Кластер'].iloc[0]
            cluster_desc = df_sub['Описание кластера'].iloc[0] if 'Описание кластера' in df_sub.columns else f'Кластер {cluster_num}'
            
            fig.add_trace(go.Bar(
                x=df_sub['Показатель'],
                y=df_sub['Значение'],
                name=uid,
                marker_color=dist_color_map[dist_name],
                legendgroup=dist_name,
                hovertemplate=(
                    f"<b>{dist_name}</b><br>"
                    f"{cluster_desc} (Кластер {cluster_num})<br>"
                    "Показатель: %{x}<br>"
                    "Значение: %{y:.2f}<extra></extra>"
                )
            ))
            
        names_seen = set()
        for trace in fig.data:
            if trace.legendgroup in names_seen:
                trace.showlegend = False
            else:
                trace.name = trace.legendgroup
                names_seen.add(trace.legendgroup)

        fig.update_layout(
            barmode='group',
            title="Интерактивный сравнительный анализ (все федеральные округа)",
            xaxis_title="",
            yaxis_title="Значение показателя",
            legend_title="Федеральные округа",
            height=700,
            bargap=0.15,
            bargroupgap=0.0,
            hoverlabel=dict(bgcolor="white", font_size=13, font_family="Inter"),
            margin=dict(b=150)
        )
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.write_html(output_path)


    @staticmethod
    def plot_meso_comparison_radar(combined_df, output_path):
        """
        Обобщающая радарная диаграмма для мезо-уровня: все 8 округов и их кластеры.
        """
        if combined_df.empty:
            return

        print(f"Генерация глобального радарного сравнения мезо-уровня (все ФО)...")
        
        service_cols = ['Округ', 'Кластер', 'Описание кластера', 'Cluster_Raw', 'Кластер_ID']
        indicators = [c for c in combined_df.columns if c not in service_cols]
        
        N = len(indicators)
        angles = [n / float(N) * 2 * pi for n in range(N)]
        angles += angles[:1]
        
        unique_districts = sorted(combined_df['Округ'].unique())
        dist_palette = sns.color_palette("tab10", len(unique_districts))
        dist_color_map = dict(zip(unique_districts, dist_palette))
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
        
        for idx, row in combined_df.iterrows():
            dist_name = row['Округ']
            values = row[indicators].values.flatten().tolist()
            values += values[:1]
            
            c_color = dist_color_map[dist_name]
            
            ax.plot(angles, values, linewidth=1, linestyle='solid', color=c_color, alpha=0.6)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(indicators, size=8)
        plt.title("Глобальное радарное сравнение профилей цифровизации (все ФО и кластеры)", size=16, y=1.1, fontweight='bold')
        
        legend_elements = [mpatches.Patch(facecolor=dist_color_map[d], label=d) for d in unique_districts]
        plt.legend(handles=legend_elements, title="Федеральные округа", 
                   loc='upper right', bbox_to_anchor=(1.3, 1.1), frameon=True, shadow=True)
        
        plt.tight_layout()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

    @staticmethod
    def plot_meso_comparison(combined_df, output_path):
        """
        8. Обобщающая диаграмма для мезо-уровня.
        """
        if combined_df.empty:
            return

        print(f"Генерация глобального сравнения мезо-уровня (все ФО)...")
        
        service_cols = ['Округ', 'Кластер', 'Описание кластера', 'Cluster_Raw', 'Кластер_ID']
        indicators = [c for c in combined_df.columns if c not in service_cols]
        
        df_melted = combined_df.melt(
            id_vars=['Округ', 'Кластер'], 
            value_vars=indicators,
            var_name='Показатель', 
            value_name='Значение'
        )
        
        df_melted['ID'] = df_melted['Округ'] + " - Кл. " + df_melted['Кластер'].astype(str)
        df_melted = df_melted.sort_values(['Показатель', 'Округ', 'Кластер'])

        unique_districts = sorted(df_melted['Округ'].unique())
        dist_palette = sns.color_palette("tab10", len(unique_districts))
        dist_color_map = dict(zip(unique_districts, dist_palette))
        
        color_list = []
        unique_ids = sorted(df_melted['ID'].unique(), key=lambda x: (x.split(" - ")[0], x.split("Кл. ")[1]))
        for uid in unique_ids:
            dist_name = uid.split(" - ")[0]
            color_list.append(dist_color_map[dist_name])

        plt.figure(figsize=(22, 12))
        
        ax = sns.barplot(
            data=df_melted,
            x='Показатель',
            y='Значение',
            hue='ID',
            palette=color_list,
            width=0.95,      # Максимальная плотность (минимальное расстояние)
            edgecolor='black',
            linewidth=0.2
        )

        plt.title("Сравнительный анализ профилей цифровизации всех федеральных округов и их кластеров", fontsize=20, fontweight='bold')
        plt.ylabel("Значение показателя", fontsize=16)
        plt.xlabel("Показатель использования цифровых технологий", fontsize=16)
        plt.xticks(rotation=90, ha='center', fontsize=12) # Вертикальные подписи для ВКР
        
        legend_elements = [mpatches.Patch(facecolor=dist_color_map[d], label=d) for d in unique_districts]
        plt.legend(handles=legend_elements, title="Федеральные округа", 
                   loc='upper left', bbox_to_anchor=(1, 1), frameon=True, shadow=True, fontsize='large')

        plt.grid(axis='y', linestyle='--', alpha=0.5)
        plt.tight_layout()
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

    @staticmethod
    def plot_meso_elbow_comparison(elbow_data_dict, output_path):
        """
        Creates a combined elbow method plot for all federal districts.

        Args:
            elbow_data_dict: Dict mapping district_name -> (K_values, distortions)
            output_path: Path to save the combined plot
        """
        if not elbow_data_dict:
            return

        print(f"Генерация глобального графика метода локтя (все ФО)...")

        plt.figure(figsize=(12, 7))

        # Get color palette for districts
        districts = sorted(elbow_data_dict.keys())
        dist_palette = sns.color_palette("tab10", len(districts))
        color_map = dict(zip(districts, dist_palette))

        # Plot each district's elbow curve
        for district, (K_values, distortions) in elbow_data_dict.items():
            color = color_map[district]
            plt.plot(K_values, distortions, marker='o', linewidth=2.5,
                    label=district, color=color, alpha=0.7, markersize=6)

        plt.xlabel('Количество кластеров (k)', fontsize=12)
        plt.ylabel('Внутрикластерная ошибка (WCSS)', fontsize=12)
        plt.title('Метод локтя: Сравнение оптимального числа кластеров по федеральным округам',
                 fontsize=14, fontweight='bold')
        plt.legend(loc='best', frameon=True, shadow=True)
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Глобальный график метода локтя сохранен: {output_path}")

    def run_all(self, k=3):
        """Запуск всего цикла анализа для уровня"""
        print(f"===[{self.level_name}] Начало полного цикла анализа===")
        
        # --- Валидация ---
        self.plot_elbow()
        kmeans_validation_results = self.calculate_and_plot_validation_metrics(chosen_k=k)
        dbscan_validation_results = self.calculate_dbscan_validation()
        
        consensus_data = {'Метод локтя': k}
        if kmeans_validation_results:
            consensus_data.update(kmeans_validation_results)
        if dbscan_validation_results:
            consensus_data.update(dbscan_validation_results)
            
        consensus_df = pd.DataFrame(list(consensus_data.items()), columns=['Метод', 'Оптимальное k'])
        consensus_df.to_excel(f"{self.output_dir}/tables/consensus_table.xlsx", index=False)
        self.plot_consensus_dashboard(consensus_df, f"{self.output_dir}/plots/consensus_dashboard.html")
        
        # --- Основной анализ ---
        self.run_clustering(k=k)
        self.export_tables()
        self.plot_heatmap()
        self.plot_pca_scatter()
        
        try:
            fig_pca = self.get_pca_plotly()
            if fig_pca:
                fig_pca.write_html(f"{self.output_dir}/plots/pca_interactive.html")
        except Exception as e:
            print(f"[{self.level_name}] Ошибка сохранения PCA HTML: {e}")
            
        try:
            fig_map = self.get_choropleth_plotly()
            if fig_map:
                fig_map.write_html(f"{self.output_dir}/plots/map_interactive.html")
        except Exception as e:
            print(f"[{self.level_name}] Ошибка сохранения Карты HTML: {e}")
            
        self.plot_radars_and_bars()
        self.plot_comparison_radars()
        self.plot_comparison_bars()
        self.plot_comparison_bars_split()
        print(f"===[{self.level_name}] Анализ успешно завершен!===")