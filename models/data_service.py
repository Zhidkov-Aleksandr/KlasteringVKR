import pandas as pd
from models.architecture import DataLoader
from models.database import create_database
from utils.excel_loader import load_excel
from utils.district_clustering import get_district_matrix
from utils.cleanup_plots import cleanup_images


class DistrictDataLoader(DataLoader):
    def __init__(self, excel_file: str):
        self.excel_file = excel_file

    def load_data(self, year: int) -> pd.DataFrame:
        # Создаем базу данных
        create_database()

        # Удаляем старые изображения
        cleanup_images()

        # Загружаем Excel
        load_excel(self.excel_file, year)

        # Получаем матрицу округов
        data = get_district_matrix(year)

        return data