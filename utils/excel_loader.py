import pandas as pd
import sqlite3
import re
from models.database import DB_NAME

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

def load_excel(file_path, target_year):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    xls = pd.ExcelFile(file_path)
    sheet_to_load = xls.sheet_names[0]

    # Ищем лист, соответствующий нужному году и содержащий данные
    if len(xls.sheet_names) > 1:
        print("Ищем нужный лист в многостраничном файле...")
        for sheet_name in xls.sheet_names:
            try:
                df_head = pd.read_excel(xls, sheet_name=sheet_name, header=None, nrows=50)
                has_target_year = False
                has_cfo = False
                
                for r in range(len(df_head)):
                    for c in range(min(10, len(df_head.columns))):
                        val = str(df_head.iloc[r, c]).lower()
                        val_clean = re.sub(r'\s+', ' ', val).strip()
                        
                        if "центральный федеральный округ" in val_clean:
                            has_cfo = True
                            
                        if r < 15:
                            years = re.findall(r'\b(20\d{2})\b', val)
                            if str(target_year) in years:
                                has_target_year = True
                                
                if has_cfo and has_target_year:
                    sheet_to_load = sheet_name
                    print(f"Найден подходящий лист: {sheet_to_load}")
                    break
            except Exception:
                continue

    # Загружаем целевой лист полностью
    df = pd.read_excel(xls, sheet_name=sheet_to_load, header=None)

    # Динамический поиск начала данных (строка и колонка с регионами)
    start_row = 10
    region_col = 2
    
    found_cfo = False
    for r in range(min(50, len(df))):
        for c in range(min(10, len(df.columns))):
            val = str(df.iloc[r, c]).lower()
            val = re.sub(r'\s+', ' ', val).strip()
            if "центральный федеральный округ" in val:
                start_row = r
                region_col = c
                found_cfo = True
                break
        if found_cfo:
            break

    # Ищем колонку, с которой начинаются факторы
    data_col_start = None
    for r in range(max(0, start_row - 10), start_row):
        for c in range(region_col + 1, len(df.columns)):
            val = str(df.iloc[r, c]).lower()
            if "интернет" in val and "вещей" not in val:
                data_col_start = c
                break
        if data_col_start is not None:
            break
            
    # Фолбэк
    if data_col_start is None:
        data_col_start = region_col + 1

    current_district_id = None
    inserted_count = 0

    for index, row in df.iterrows():
        if index < start_row:
            continue

        if region_col >= len(row):
            continue
            
        territory_name = str(row[region_col]).strip()

        if territory_name == "nan" or not territory_name or territory_name == "":
            continue

        if "федеральный округ" in territory_name.lower():
            cursor.execute("""
                INSERT OR IGNORE INTO federal_districts (name)
                VALUES (?)
            """, (territory_name,))

            cursor.execute("SELECT id FROM federal_districts WHERE name = ?", (territory_name,))
            res = cursor.fetchone()
            if res:
                current_district_id = res[0]
            else:
                continue

            territory_type = "district"
            territory_id = current_district_id

        else:
            if current_district_id is None:
                continue
                
            cursor.execute("""
                INSERT OR IGNORE INTO regions (name, federal_district_id)
                VALUES (?, ?)
            """, (territory_name, current_district_id))

            cursor.execute("SELECT id FROM regions WHERE name = ?", (territory_name,))
            res = cursor.fetchone()
            if res:
                territory_id = res[0]
            else:
                continue

            territory_type = "region"

        for i in range(11):
            col_idx = data_col_start + i
            if col_idx >= len(row):
                continue
            
            value = row[col_idx]
            
            if pd.isna(value) or str(value).strip() in ["-", "", "nan", "…", "..."]:
                continue

            try:
                # В Excel значения могут быть со строковым пробелом (тысячи) или запятой
                if isinstance(value, str):
                    value = value.replace(',', '.').replace(' ', '')
                float_val = float(value)
            except ValueError:
                continue

            cursor.execute("INSERT OR IGNORE INTO indicators (name) VALUES (?)", (FACTORS[i],))
            cursor.execute("SELECT id FROM indicators WHERE name = ?", (FACTORS[i],))
            indicator_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO values_data
                (territory_type, territory_id, indicator_id, year, value)
                VALUES (?, ?, ?, ?, ?)
            """, (territory_type, territory_id, indicator_id, target_year, float_val))
            
            inserted_count += 1

    if inserted_count == 0:
        conn.close()
        raise ValueError(f"Не удалось загрузить данные. Проверьте правильность структуры листа '{sheet_to_load}' и наличие числовых значений.")

    conn.commit()
    conn.close()
