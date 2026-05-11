import pandas as pd
import re

file_path = "3inf_MP_2024.xlsx"
target_year = 2024

xls = pd.ExcelFile(file_path)
print("Sheets:", xls.sheet_names)

found_in_sheet = False
sheet_to_load = None
for sheet_name in xls.sheet_names:
    try:
        df_head = pd.read_excel(xls, sheet_name=sheet_name, header=None, nrows=15)
        for r in range(len(df_head)):
            for c in range(min(5, len(df_head.columns))):
                val = str(df_head.iloc[r, c]).lower()
                if "малым" in val and "предприятием" in val:
                    print(f"[{sheet_name}] ({r},{c}) => {val}")
                    match = re.search(r'\b(20\d{2})\b', val)
                    if match:
                        y = int(match.group(1))
                        print(f"[{sheet_name}] Found year {y}")
                        if y == target_year:
                            sheet_to_load = sheet_name
                            found_in_sheet = True
                            break
            if found_in_sheet: break
    except Exception as e:
        print(f"Error on sheet {sheet_name}: {e}")
    if found_in_sheet: break

print(f"Chosen sheet: {sheet_to_load}")
