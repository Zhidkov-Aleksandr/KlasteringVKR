import pandas as pd
import numpy as np
import logging
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from config import N_CLUSTERS, RANDOM_STATE, CLUSTER_NAMES, FEATURE_COLUMNS


class ClusteringModel:
    def __init__(self, n_clusters=N_CLUSTERS, random_state=RANDOM_STATE):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.scaler = StandardScaler()
        # Строго используем init='k-means++' как заявлено в ВКР
        self.kmeans = KMeans(n_clusters=self.n_clusters, init='k-means++',
                             random_state=self.random_state, n_init=10)
        self.pca = PCA(n_components=2, random_state=self.random_state)

    def extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """Извлекает только числовые колонки факторов для математики."""
        return df[FEATURE_COLUMNS].values

    def calculate_elbow_method(self, df: pd.DataFrame, max_k: int = 10):
        """
        Рассчитывает внутрикластерную дисперсию (инерцию) для k от 1 до max_k.
        Возвращает данные для построения графика «метода локтя».
        """
        logging.info(f"Расчет метода локтя для k от 1 до {max_k}...")
        X = self.extract_features(df)
        X_scaled = self.scaler.fit_transform(X)

        inertias = []
        k_range = range(1, max_k + 1)

        for k in k_range:
            model = KMeans(n_clusters=k, init='k-means++', random_state=self.random_state, n_init=10)
            model.fit(X_scaled)
            inertias.append(model.inertia_)

        return list(k_range), inertias

    def fit_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Основной процесс кластеризации.
        Масштабирует данные, обучает модель, применяет PCA и возвращает размеченный датафрейм.
        """
        logging.info(f"Запуск алгоритма K-means++ (Количество кластеров: {self.n_clusters})")
        result_df = df.copy()

        # 1. Подготовка и масштабирование
        X = self.extract_features(result_df)
        X_scaled = self.scaler.fit_transform(X)

        # 2. Обучение и предсказание
        cluster_labels = self.kmeans.fit_predict(X_scaled)

        # Присваиваем метки (алгоритм выдает 0, 1, 2. Мы делаем 1, 2, 3 для ВКР)
        result_df['Номер кластера'] = cluster_labels + 1

        # Добавляем текстовые названия кластеров из config.py
        result_df['Название кластера'] = result_df['Номер кластера'].map(CLUSTER_NAMES)

        # 3. Снижение размерности (PCA) для 2D-графиков
        logging.info("Применение метода главных компонент (PCA) для проекции 11D -> 2D.")
        pca_coords = self.pca.fit_transform(X_scaled)
        result_df['PCA_X'] = pca_coords[:, 0]
        result_df['PCA_Y'] = pca_coords[:, 1]

        # 4. Расчет центроидов (средних значений факторов по каждому кластеру)
        # Это нужно для построения тепловой карты
        centroids = result_df.groupby('Номер кластера')[FEATURE_COLUMNS].mean()

        logging.info("Кластеризация успешно завершена.")
        return result_df, centroids