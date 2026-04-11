import customtkinter as ctk
from views.gui_components import FileLoader, LogManager, AnalysisController, UIController


class ClusteringGUI:
    def __init__(self):
        ctk.set_appearance_mode("dark")  # Темная тема
        ctk.set_default_color_theme("blue")  # Синяя тема

        self.root = ctk.CTk()
        self.root.title("Кластеризация данных")
        self.root.geometry("800x600")

        # Создаем UIController первым
        self.ui_controller = UIController(self.root)

        # Создаем компоненты
        self.log_textbox = self.ui_controller.widgets['log_textbox']
        self.log_manager = LogManager(self.log_textbox)
        self.file_loader = FileLoader(self.log_manager)
        self.analysis_controller = AnalysisController(self.file_loader, self.log_manager)

        # Устанавливаем зависимости в UIController
        self.ui_controller.set_dependencies(self.file_loader, self.analysis_controller)

        # Устанавливаем callback для file_loader
        self.file_loader.set_on_file_loaded(self.ui_controller.enable_analysis_buttons)

        # Создаем виджеты
        self.ui_controller.create_widgets()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    gui = ClusteringGUI()
    gui.run()