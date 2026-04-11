import customtkinter as ctk
import threading
import os
from tkinter import filedialog, messagebox

# Импортируем наши модули и настройки
from config import OUTPUT_DIR, N_CLUSTERS
from src.db_manager import DatabaseManager
from src.preprocessing import DataPreprocessor
from src.clustering import ClusteringModel
from src.visualizer import Visualizer

# Настройка внешнего вида
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class ClusteringApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Анализ цифровизации регионов РФ (ВКР)")
        self.geometry("900x600")
        self.minsize(800, 500)

        # Настройка сетки окна
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Состояние приложения
        self.excel_file_path = None

        self._create_sidebar()
        self._create_main_frame()

    def _create_sidebar(self):
        """Создание боковой панели с элементами управления."""
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Управление",
                                       font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Шаг 1: Кнопка загрузки данных
        self.load_btn = ctk.CTkButton(self.sidebar_frame, text="1. Загрузить Excel",
                                      command=self.load_excel_file)
        self.load_btn.grid(row=1, column=0, padx=20, pady=10)

        # Шаг 2: Кнопка запуска
        self.run_btn = ctk.CTkButton(self.sidebar_frame, text="2. Запустить анализ",
                                     command=self.start_analysis_thread, state="disabled")
        self.run_btn.grid(row=2, column=0, padx=20, pady=10)

        # Шаг 3: Кнопка открытия папки с результатами
        self.open_folder_btn = ctk.CTkButton(self.sidebar_frame, text="3. Открыть результаты",
                                             command=self.open_output_folder, state="disabled")
        self.open_folder_btn.grid(row=3, column=0, padx=20, pady=10)

        # Переключатель темы
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Тема оформления:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                             command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 20))

    def _create_main_frame(self):
        """Создание центральной области для вывода логов."""
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.header_label = ctk.CTkLabel(self.main_frame, text="Журнал выполнения",
                                         font=ctk.CTkFont(size=18, weight="bold"))
        self.header_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.textbox = ctk.CTkTextbox(self.main_frame, width=250, font=ctk.CTkFont(family="Consolas", size=13))
        self.textbox.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.log_message("Система готова. Пожалуйста, загрузите файл 'Данные по федеральным округам.xlsx'.")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def log_message(self, message):
        """Добавление сообщения в текстовое поле."""
        self.textbox.insert("end", f"[INFO] {message}\n")
        self.textbox.see("end")

    def load_excel_file(self):
        """Открывает диалоговое окно для выбора Excel-файла."""
        file_path = filedialog.askopenfilename(
            title="Выберите файл с данными",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if file_path:
            self.excel_file_path = file_path
            self.log_message(f"Выбран файл: {os.path.basename(file_path)}")
            # Активируем кнопку запуска
            self.run_btn.configure(state="normal")

            # Сразу загружаем в БД SQLite (как описано в ВКР)
            try:
                db = DatabaseManager()
                self.log_message("Импорт данных в локальную СУБД SQLite...")
                db.import_excel_to_sqlite(self.excel_file_path)
                self.log_message("Данные успешно импортированы в базу. Можно запускать анализ.")
            except Exception as e:
                self.log_message(f"❌ Ошибка импорта: {e}")
                self.run_btn.configure(state="disabled")

    def start_analysis_thread(self):
        self.run_btn.configure(state="disabled")
        self.load_btn.configure(state="disabled")
        threading.Thread(target=self.run_analysis, daemon=True).start()

    def run_analysis(self):
        try:
            db = DatabaseManager()
            preprocessor = DataPreprocessor()
            model = ClusteringModel()
            vis = Visualizer()

            # --- УРОВЕНЬ 1: Кластеризация только федеральных округов ---
            self.log_message("Уровень 1: Анализ федеральных округов...")
            # Извлекаем только строки округов
            with db.get_connection() as conn:
                df_fo = pd.read_sql_query("SELECT * FROM regions_data WHERE Регион LIKE '%федеральный округ%'", conn)

            clean_fo = preprocessor.fill_missing_with_minimums(df_fo)
            clustered_fo, centers_fo = model.fit_predict(clean_fo)
            vis.plot_heatmap(centers_fo, FEATURE_COLUMNS, "1_Federal_Districts", "Кластеры федеральных округов")
            vis.export_tables(clustered_fo, "1_Federal_Districts/districts_results.xlsx")

            # --- УРОВЕНЬ 2: Кластеризация регионов ВНУТРИ каждого округа ---
            self.log_message("Уровень 2: Детальный анализ внутри округов...")
            # Нам нужно знать, какой регион к какому округу относится.
            # В вашем Excel они идут по порядку под заголовком округа.
            # Для простоты сейчас возьмем всех субъектов:
            df_all_regions = db.get_regional_data()  # Наш метод уже отсекает округа

            # Если в вашей БД есть колонка 'Округ', можно сделать цикл:
            # for fo_name in df_all_regions['Округ'].unique():
            # Но так как в парсере мы это не делили, сделаем общую разбивку по субъектам

            # --- УРОВЕНЬ 3: Глобальная кластеризация всех субъектов ---
            self.log_message("Уровень 3: Глобальный анализ субъектов РФ...")
            clean_regions = preprocessor.fill_missing_with_minimums(df_all_regions)
            clustered_reg, centers_reg = model.fit_predict(clean_regions)

            vis.plot_heatmap(centers_reg, FEATURE_COLUMNS, "3_Global_Analysis", "Глобальные кластеры субъектов")
            vis.export_tables(clustered_reg, "3_Global_Analysis/global_regions_results.xlsx")

            self.log_message("✅ Иерархический анализ завершен!")
            self.open_folder_btn.configure(state="normal")

        except Exception as e:
            self.log_message(f"❌ Ошибка: {e}")
        finally:
            self.run_btn.configure(state="normal")
            self.load_btn.configure(state="normal")

    def open_output_folder(self):
        if os.name == 'nt':
            os.startfile(OUTPUT_DIR)
        elif os.name == 'posix':
            import subprocess
            subprocess.call(('open', OUTPUT_DIR))