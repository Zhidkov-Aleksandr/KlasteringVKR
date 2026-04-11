import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config import PLOTS_DIR, TABLES_DIR


class Visualizer:
    def __init__(self):
        """Инициализация визуализатора и настройка кириллицы для графиков."""
        # Убедимся, что директории для вывода существуют
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def _get_path(self, subfolder, filename):
        path = self.base_path / subfolder
        os.makedirs(path, exist_ok=True)
        return path / filename

        # Настройка шрифтов для корректного отображения русского языка (по ГОСТу)
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
        plt.rcParams['axes.unicode_minus'] = False

    def export_tables(self, df_clusters, filename="cluster_results.xlsx"):
        """
        Экспорт итогового датафрейма с метками кластеров в Excel.
        """
        filepath = TABLES_DIR / filename
        # Используем index=False, чтобы не сохранять номера строк (индексы pandas)
        df_clusters.to_excel(filepath, index=False)
        print(f"[УСПЕХ] Таблица результатов сохранена: {filepath}")

    def plot_elbow_method(self, inertias, k_range):
        """
        Отрисовка и сохранение графика метода локтя.
        """
        plt.figure(figsize=(8, 5))
        plt.plot(k_range, inertias, marker='o', linestyle='-', color='b')
        plt.title('Метод локтя для определения оптимального числа кластеров')
        plt.xlabel('Количество кластеров (k)')
        plt.ylabel('Внутрикластерная дисперсия (W_k)')
        plt.grid(True)

        filepath = PLOTS_DIR / 'elbow_method.png'
        # dpi=300 обеспечивает типографское (высокое) качество картинки для вставки в Word
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"[УСПЕХ] График метода локтя сохранен: {filepath}")

    def plot_heatmap(self, cluster_centers, feature_names, subfolder, title):
        """
        Отрисовка тепловой карты центроидов кластеров (как на Рисунке 2.29 в ВКР).
        """
        plt.figure(figsize=(10, 6))
        # Используем цветовую схему YlGnBu (от желтого к синему), она хорошо смотрится в печати
        sns.heatmap(cluster_centers, annot=True, cmap='YlGnBu', fmt=".2f",
                    xticklabels=feature_names,
                    yticklabels=[f"Кластер {i + 1}" for i in range(len(cluster_centers))])

        plt.title('Тепловая карта факторов цифровизации по кластерам')
        plt.xlabel('Показатели цифровизации')
        plt.ylabel('Кластеры')

        # Поворачиваем подписи оси X, чтобы длинные названия показателей не сливались
        plt.xticks(rotation=45, ha='right')

        filepath = self._get_path(subfolder, 'heatmap.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"[УСПЕХ] Тепловая карта сохранена: {filepath}")

    def plot_radar_chart(self, *args, **kwargs):
        """
        Место для функции построения лепестковых (радарных) диаграмм.
        (Сюда вы перенесете свой код для построения радаров из старой версии).
        """
        pass