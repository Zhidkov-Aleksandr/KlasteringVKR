import pandas as pd
import sqlite3
import re

file_path = "3inf_MP_2024.xlsx"
xls = pd.ExcelFile(file_path)
print("Sheets:", xls.sheet_names)

target_year = 2024
sheet_to_load = None
if len(xls.sheet_names) > 1:
    for sheet_name in xls.sheet_names:
        try:
            df_head = pd.read_excel(xls, sheet_name=sheet_name, header=None, nrows=15)
            sheet_year = None
            for r in range(min(15, len(df_head))):
                for c in range(len(df_head.columns)):
                    val = str(df_head.iloc[r, c])
                    match = re.search(r'\b(20\d{2})\b', val)
                    if match:
                        y = int(match.group(1))
                        if y == target_year:
                            sheet_year = y
                            break
                if sheet_year == target_year:
                    break
            
            if sheet_year == target_year:
                sheet_to_load = sheet_name
                break
        except Exception as e:
            print(e)
            continue

print(f"Chosen sheet: {sheet_to_load}")

if sheet_to_load:
    df = pd.read_excel(xls, sheet_name=sheet_to_load, header=None)
    start_row = 10
    region_col = 2
    
    found = False
    for r in range(min(30, len(df))):
        for c in range(min(10, len(df.columns))):
            val = str(df.iloc[r, c]).strip().lower()
            if "центральный федеральный округ" in val or val == "центральный федеральный округ":
                start_row = r
                region_col = c
                found = True
                break
        if found:
            break

    print(f"start_row: {start_row}, region_col: {region_col}")
    print(df.iloc[start_row:start_row+5, region_col:region_col+3])
