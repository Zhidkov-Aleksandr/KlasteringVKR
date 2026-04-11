from abc import ABC, abstractmethod
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import io
from contextlib import redirect_stdout, redirect_stderr
import matplotlib
import os
import shutil
matplotlib.use('Agg')  # Non-interactive backend to prevent GUI hanging

# Импорты из проекта
from models.architecture import Pipeline
from models.data_service import DistrictDataLoader
from models.clustering_service import KMeansClusteringStrategy
from models.analysis_service import ClusterAnalyzer
from views.visualization_service import DistrictVisualizer
from services.regions_elbow import plot_regions_elbow
from services.regions_clustering import cluster_regions_by_district
from services.analysis_cluster_factors import analyze_cluster_district_factors
from services.merge_region_clusters import merge_region_clusters
from services.cluster_subject_plots import plot_cluster_subjects
from services.district_subject_cluster_plots import plot_district_subject_clusters
from services.clustering_all_regions import run_global_clustering


class FileLoader:
    def __init__(self, log_manager, on_file_loaded=None):
        self.log_manager = log_manager
        self.excel_file = None
        self.on_file_loaded = on_file_loaded

    def set_on_file_loaded(self, callback):
        self.on_file_loaded = callback

    def load_excel(self):
        try:
            self.log_manager.log("Открытие диалога выбора файла...")
            file_path = filedialog.askopenfilename(
                title="Выберите Excel файл",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            self.log_manager.log(f"Диалог закрыт, путь: {file_path}")
            if file_path:
                self.excel_file = file_path
                self.log_manager.log(f"Файл загружен: {file_path}")
                if self.on_file_loaded:
                    self.on_file_loaded()
                return True
            else:
                self.log_manager.log("Файл не выбран")
                messagebox.showwarning("Предупреждение", "Файл не выбран")
                return False
        except Exception as e:
            self.log_manager.log(f"Ошибка при загрузке файла: {str(e)}")
            messagebox.showerror("Ошибка", f"Ошибка при загрузке файла: {str(e)}")
            return False


class LogManager:
    def __init__(self, textbox):
        self.textbox = textbox

    def log(self, message):
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end")
        self.textbox.master.update_idletasks()


class AnalysisController:
    def __init__(self, file_loader, log_manager, year=2024):
        self.file_loader = file_loader
        self.log_manager = log_manager
        self.year = year

    def run_district_analysis(self):
        if not self.file_loader.excel_file:
            messagebox.showerror("Ошибка", "Сначала загрузите Excel файл")
            return
        self._run_in_thread(self._district_analysis)

    def _district_analysis(self):
        self.log_manager.log("Запуск кластерного анализа федеральных округов...")

        # Очистка папки output/districts
        if os.path.exists("output/districts"):
            shutil.rmtree("output/districts")
        os.makedirs("output/districts", exist_ok=True)

        # Создаем сервисы
        data_loader = DistrictDataLoader(self.file_loader.excel_file)
        clustering_strategy = KMeansClusteringStrategy()
        analyzer = ClusterAnalyzer()
        visualizer = DistrictVisualizer()

        # Pipeline
        pipeline = Pipeline(data_loader, clustering_strategy, analyzer, visualizer)

        # Захватываем вывод
        with io.StringIO() as buf, redirect_stdout(buf):
            try:
                pipeline.run(self.year)
            except Exception as e:
                self.log_manager.log(f"Ошибка: {str(e)}")
            finally:
                output = buf.getvalue()
                self.log_manager.log(output)
                self.log_manager.log("Анализ федеральных округов завершен.")

    def run_regions_analysis(self):
        if not self.file_loader.excel_file:
            messagebox.showerror("Ошибка", "Сначала загрузите Excel файл")
            return
        self._run_in_thread(self._regions_analysis)

    def _regions_analysis(self):
        self.log_manager.log("Запуск кластерного анализа регионов по округам...")

        # Очистка папки output/regions
        if os.path.exists("output/regions"):
            shutil.rmtree("output/regions")
        os.makedirs("output/regions", exist_ok=True)

        with io.StringIO() as buf, redirect_stdout(buf):
            try:
                # Метод локтя для субъектов
                plot_regions_elbow(self.year)

                # Кластеризация субъектов по округам
                cluster_regions_by_district(self.year)

                # Анализ факторов субъектов РФ
                print("\nОбъединение кластеров субъектов...")
                merge_region_clusters()
                print("\nАнализ факторов различий между кластерами субъектов РФ...\n")
                analyze_cluster_district_factors()
                print("\nАнализ кластеров субъектов завершён.")

                # Построение диаграмм
                print("\nПостроение диаграмм кластеров субъектов...\n")
                plot_cluster_subjects()
                plot_district_subject_clusters()
            except Exception as e:
                self.log_manager.log(f"Ошибка: {str(e)}")
            finally:
                output = buf.getvalue()
                self.log_manager.log(output)
                self.log_manager.log("Анализ регионов по округам завершен.")

    def run_all_regions_analysis(self):
        if not self.file_loader.excel_file:
            messagebox.showerror("Ошибка", "Сначала загрузите Excel файл")
            return
        self._run_in_thread(self._all_regions_analysis)

    def _all_regions_analysis(self):
        self.log_manager.log("Запуск кластерного анализа всех регионов...")

        # Очистка папки output/all_regions
        if os.path.exists("output/all_regions"):
            shutil.rmtree("output/all_regions")
        os.makedirs("output/all_regions", exist_ok=True)

        with io.StringIO() as buf, redirect_stdout(buf):
            try:
                run_global_clustering()
            except Exception as e:
                self.log_manager.log(f"Ошибка: {str(e)}")
            finally:
                output = buf.getvalue()
                self.log_manager.log(output)
                self.log_manager.log("Анализ всех регионов завершен.")

    def _run_in_thread(self, func):
        thread = threading.Thread(target=func)
        thread.start()


class UIController:
    def __init__(self, root):
        self.root = root
        self.file_loader = None
        self.analysis_controller = None
        self.widgets = {}
        # Создаем log_textbox заранее
        self.widgets['log_textbox'] = ctk.CTkTextbox(
            self.root, wrap="word", font=("Consolas", 10)
        )

    def set_dependencies(self, file_loader, analysis_controller):
        self.file_loader = file_loader
        self.analysis_controller = analysis_controller

    def create_widgets(self):
        # Кнопка загрузки файла
        self.widgets['load_button'] = ctk.CTkButton(
            self.root, text="Загрузить Excel файл", command=self.file_loader.load_excel,
            font=("Arial", 14), height=40
        )
        self.widgets['load_button'].pack(pady=20, padx=20, fill="x")

        # Фрейм для кнопок анализа
        self.widgets['analysis_frame'] = ctk.CTkFrame(self.root)
        self.widgets['analysis_frame'].pack(pady=10, padx=20, fill="x")

        # Кнопки анализа
        self.widgets['district_button'] = ctk.CTkButton(
            self.widgets['analysis_frame'], text="1. Кластерный анализ федеральных округов",
            command=self.analysis_controller.run_district_analysis, state="disabled",
            font=("Arial", 12), height=35
        )
        self.widgets['district_button'].pack(pady=5, padx=10, fill="x")

        self.widgets['regions_button'] = ctk.CTkButton(
            self.widgets['analysis_frame'], text="2. Кластерный анализ регионов по каждому федеральному округу",
            command=self.analysis_controller.run_regions_analysis, state="disabled",
            font=("Arial", 12), height=35
        )
        self.widgets['regions_button'].pack(pady=5, padx=10, fill="x")

        self.widgets['all_regions_button'] = ctk.CTkButton(
            self.widgets['analysis_frame'], text="3. Кластерный анализ всех регионов",
            command=self.analysis_controller.run_all_regions_analysis, state="disabled",
            font=("Arial", 12), height=35
        )
        self.widgets['all_regions_button'].pack(pady=5, padx=10, fill="x")

        # Текстовое поле для логов
        self.widgets['log_textbox'].pack(pady=10, padx=20, fill="both", expand=True)
        # Включаем копирование текста
        self.widgets['log_textbox'].bind("<Control-c>", self._copy_text)

        # Фрейм для кнопок внизу
        self.widgets['bottom_frame'] = ctk.CTkFrame(self.root)
        self.widgets['bottom_frame'].pack(pady=20, padx=20, fill="x")

        # Кнопка копирования лога
        self.widgets['copy_log_button'] = ctk.CTkButton(
            self.widgets['bottom_frame'], text="Копировать лог", command=self._copy_all_log,
            font=("Arial", 12), height=30
        )
        self.widgets['copy_log_button'].pack(side="left", expand=True, padx=5)

        # Кнопка выхода
        self.widgets['exit_button'] = ctk.CTkButton(
            self.widgets['bottom_frame'], text="Выход", command=self.root.quit,
            fg_color="red", font=("Arial", 14), height=40
        )
        self.widgets['exit_button'].pack(side="right", expand=True, padx=5)

    def _copy_text(self, event):
        try:
            selected_text = self.widgets['log_textbox'].selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except:
            pass  # No selection

    def _copy_all_log(self):
        all_text = self.widgets['log_textbox'].get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(all_text)

    def enable_analysis_buttons(self):
        self.widgets['district_button'].configure(state="normal")
        self.widgets['regions_button'].configure(state="normal")
        self.widgets['all_regions_button'].configure(state="normal")