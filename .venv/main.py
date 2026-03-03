from database import create_database
from excel_loader import load_excel

create_database() #

load_excel("Данные по федеральным округам.xlsx", 2024)