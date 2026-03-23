import pandas as pd
import sqlite3
from database import DB_NAME

FACTORS = [
    "Интернет",
    "Веб-сайт или соцсети",
    "Цифровые платформы",
    "Маркетплейсы",
    "Финансовые цифровые платформы",
    "ИИ",
    "Облачные сервисы",
    "Интернет вещей",
    "Промышленные роботы",
    "Big Data",
    "ЦОД"
]


def load_excel(file_path, year):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Загружаем файл без заголовков
    df = pd.read_excel(file_path, header=None)

    current_district_id = None

    for index, row in df.iterrows():

        # Начинаем с 11 строки (индекс 10)
        if index < 10:
            continue

        territory_name = str(row[2]).strip()

        # Пропускаем пустые строки
        if territory_name == "nan":
            continue

        # Проверяем — округ или субъект
        if "федеральный округ" in territory_name.lower():

            # Добавляем округ
            cursor.execute("""
                INSERT OR IGNORE INTO federal_districts (name)
                VALUES (?)
            """, (territory_name,))

            cursor.execute("""
                SELECT id FROM federal_districts WHERE name = ?
            """, (territory_name,))
            current_district_id = cursor.fetchone()[0]

            territory_type = "district"
            territory_id = current_district_id

        else:
            # Это субъект
            cursor.execute("""
                INSERT OR IGNORE INTO regions (name, federal_district_id)
                VALUES (?, ?)
            """, (territory_name, current_district_id))

            cursor.execute("""
                SELECT id FROM regions WHERE name = ?
            """, (territory_name,))
            territory_id = cursor.fetchone()[0]

            territory_type = "region"

        # Обрабатываем 11 факторов (D=3 до N=13)
        for i in range(11):
            value = row[3 + i]

            # Пропускаем пустые значения и прочерки
            if pd.isna(value) or str(value).strip() == "-":
                continue

            # Добавляем индикатор
            cursor.execute("""
            INSERT OR IGNORE INTO indicators (name)
            VALUES (?)
            """, (FACTORS[i],))

            cursor.execute("""
                SELECT id FROM indicators WHERE name = ?
            """, (FACTORS[i],))
            indicator_id = cursor.fetchone()[0]

            # Сохраняем значение
            cursor.execute("""
                INSERT INTO values_data
                (territory_type, territory_id, indicator_id, year, value)
                VALUES (?, ?, ?, ?, ?)
            """, (territory_type, territory_id, indicator_id, year, float(value)))

    conn.commit()
    conn.close()

    print("Загрузка завершена успешно.") #