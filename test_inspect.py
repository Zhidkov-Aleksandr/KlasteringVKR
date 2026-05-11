import pandas as pd
import re

file_path = "3inf_MP_2024.xlsx"
xls = pd.ExcelFile(file_path)
print("Sheets:", xls.sheet_names)

available_years = []
for sheet_name in xls.sheet_names:
    try:
        df_head = pd.read_excel(xls, sheet_name=sheet_name, header=None, nrows=10)
        for r in range(len(df_head)):
            for c in range(min(5, len(df_head.columns))):
                val = str(df_head.iloc[r, c]).lower()
                if "малым" in val and "предприятием" in val:
                    print(f"[{sheet_name}] Found at ({r},{c}): {val}")
                    match = re.search(r'\b(20\d{2})\b', val)
                    if match:
                        y = int(match.group(1))
                        print(f"[{sheet_name}] Found year: {y}")
                        if y not in available_years:
                            available_years.append(y)
    except Exception as e:
        print(f"[{sheet_name}] Error: {e}")

print("Available years:", available_years)
