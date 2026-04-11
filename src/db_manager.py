import sqlite3
import pandas as pd
import logging
from config import DB_PATH, FEATURE_COLUMNS


class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def import_excel_to_sqlite(self, excel_path):
        """
        Парсинг Excel со сложной структурой (с 11 строки) и сохранение в SQLite.
        """
        global current_fo
        try:
            logging.info(f"Запуск парсинга структуры Excel: {excel_path}")

            # Читаем файл без заголовков, чтобы обращаться по индексам (как в старом скрипте)
            df_raw = pd.read_excel(excel_path, header=None)

            parsed_rows = []

            # В вашем файле данные начинаются с индекса 10 (11-я строка)
            # Столбец 2 (индекс 2) — Название территории
            # Столбцы с 3 по 13 — Факторы цифровизации
            for index, row in df_raw.iterrows():
                if index < 10:
                    continue

                territory_name = str(row[2]).strip()

                # Если в названии есть "округ", запоминаем его как текущий
                if "федеральный округ" in territory_name.lower():
                    current_fo = territory_name
                    # Округа тоже сохраняем (для Уровня 1)

                # Пропускаем пустые строки или технические пометки
                if territory_name == "nan" or not territory_name:
                    continue

                # Собираем данные по 11 факторам (согласно порядку в вашем Excel)
                # Важно: порядок в row[3:14] должен соответствовать порядку в FEATURE_COLUMNS в config.py
                row_data = {
                    "Регион": territory_name
                    "Округ": current_fo
                }

                for i, factor_name in enumerate(FEATURE_COLUMNS):
                    val = row[3 + i]
                    # Обработка прочерков и пустых значений как в старом коде
                    if pd.isna(val) or str(val).strip() == "-":
                        row_data[factor_name] = None
                    else:
                        try:
                            row_data[factor_name] = float(val)
                        except:
                            row_data[factor_name] = None

                parsed_rows.append(row_data)

            # Создаем чистый DataFrame
            df_final = pd.DataFrame(parsed_rows)

            # Сохраняем в SQLite
            with self.get_connection() as conn:
                df_final.to_sql('regions_data', conn, if_exists='replace', index=False)

            logging.info(f"Успешно обработано {len(df_final)} территорий.")
            return True

        except Exception as e:
            logging.error(f"Ошибка парсинга структуры Excel: {e}")
            raise

    def get_regional_data(self):
        try:
            with self.get_connection() as conn:
                # Извлекаем данные, отсекая агрегированные строки (РФ и округа),
                # если это нужно для кластеризации только субъектов.
                query = "SELECT * FROM regions_data WHERE Регион NOT LIKE '%федеральный округ%' AND Регион != 'Российская Федерация'"
                df = pd.read_sql_query(query, conn)
            return df
        except Exception as e:
            logging.error(f"Ошибка извлечения из БД: {e}")
            raise