import pandas as pd

try:
    xls = pd.ExcelFile("3inf_MP_2024.xlsx")
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, header=None)
        print(f"--- Sheet: {sheet} ---")
        print(df.iloc[8:15, 0:5])
except Exception as e:
    print(e)
