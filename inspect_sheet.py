import pandas as pd

xls = pd.ExcelFile("raw_test.xlsx")
df = pd.read_excel(xls, sheet_name='3', header=None)
print(df.iloc[8:15, 0:5])
