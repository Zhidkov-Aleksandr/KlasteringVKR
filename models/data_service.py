import pandas as pd
from models.architecture import DataLoader
from models.database import create_database
from utils.excel_loader import load_excel


class DistrictDataLoader(DataLoader):
    def __init__(self, excel_file: str):
        self.excel_file = excel_file

    def load_data(self, year: int) -> pd.DataFrame:
        # Создаем базу данных
        create_database()


        # Загружаем Excel
        load_excel(self.excel_file, year)


        return pd.DataFrame()