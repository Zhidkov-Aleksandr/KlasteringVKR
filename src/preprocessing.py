import pandas as pd
import logging
from config import FEATURE_COLUMNS


class DataPreprocessor:
    def __init__(self):
        """Инициализация модуля предобработки данных."""
        pass

    def fill_missing_with_minimums(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Обрабатывает пропущенные значения (NaN) в наборе данных.
        Согласно методологии ВКР, пропуски заполняются минимальным
        зафиксированным значением фактора по всей стране (пенализация за отсутствие технологий).
        """
        logging.info("Начало предобработки данных: поиск и заполнение пропусков.")

        # Создаем копию датафрейма, чтобы не изменять исходные данные напрямую
        clean_df = df.copy()

        # Проверяем наличие колонок с факторами цифровизации
        available_features = [col for col in FEATURE_COLUMNS if col in clean_df.columns]

        if not available_features:
            logging.error("В данных не найдены колонки с факторами цифровизации!")
            raise ValueError("Отсутствуют целевые колонки для обработки.")

        total_missing_filled = 0

        # Проходим по каждому показателю цифровизации
        for col in available_features:
            # Считаем количество пропусков в колонке
            missing_count = clean_df[col].isna().sum()

            if missing_count > 0:
                # Находим глобальный минимум по этому показателю в стране
                min_value = clean_df[col].min()

                # Заполняем пропуски найденным минимумом
                clean_df[col] = clean_df[col].fillna(min_value)
                total_missing_filled += missing_count

                logging.debug(f"Колонка '{col}': заполнено {missing_count} пропусков значением {min_value:.2f}")

        logging.info(f"Предобработка завершена. Всего заполнено пропущенных значений: {total_missing_filled}.")

        # Убедимся, что данные имеют числовой формат (float) для работы алгоритма K-means
        for col in available_features:
            clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce')

        return clean_df