import streamlit as st
import os
import io
import shutil
import time
from contextlib import redirect_stdout
from PIL import Image
import pandas as pd

# Импорты бизнес-логики
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

# Настройка страницы (добавляем скрытие сайдбара на уровне конфига)
st.set_page_config(
    page_title="Анализ цифровизации РФ",
    page_icon="🇷🇺",
    layout="wide",
    initial_sidebar_state="collapsed" # Сворачиваем сайдбар
)

# Кастомный CSS для скрытия системных элементов Streamlit и стилизации (Светлая тема)
hide_streamlit_style = """
<style>
    /* Скрываем гамбургер-меню в правом верхнем углу */
    #MainMenu {visibility: hidden;}
    /* Скрываем футер "Made with Streamlit" */
    footer {visibility: hidden;}
    /* Скрываем хедер (полоску сверху) */
    header {visibility: hidden;}

    /* Полностью скрываем боковую панель Streamlit и кнопку ее открытия */
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }

    /* Сдвигаем основной контент вверх, убирая пустой отступ */
    .block-container {
        padding-top: 1rem !important;
        max-width: 1400px;
    }

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Сдвигаем главный заголовок выше */
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-top: -3rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        padding: 0;
        letter-spacing: -0.5px;
    }
    
    .sub-title {
        font-size: 1.1rem;
        font-weight: 400;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* Стилизация кнопок - убрали нижний марджин, чтобы не было пустых мест */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 60px;
        font-size: 1.05rem;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
        border: 1px solid #e2e8f0;
        background-color: white;
        color: #1e293b;
        margin-bottom: 12px; /* Расстояние между кнопками вместо пустых карточек */
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2);
        border-color: #3b82f6;
        color: #2563eb;
    }
    
    /* Стилизация консоли логов (Светлая тема) */
    .console-box {
        background-color: #f1f5f9;
        color: #0f172a;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 0.85rem;
        padding: 1.5rem;
        border-radius: 12px;
        height: 380px;
        overflow-y: auto;
        border: 1px solid #cbd5e1;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
        line-height: 1.6;
        white-space: pre-wrap;
    }

    /* Убираем рамки карточек, делаем заголовки секций аккуратнее */
    .section-title {
        color: #1e293b;
        font-weight: 600;
        margin-bottom: 1rem;
        font-size: 1.25rem;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.5rem;
    }
    
    /* Убираем пустые label_visibility="collapsed" отступы */
    div[data-testid="stFileUploader"] { margin-bottom: 1rem; }
    div[data-testid="stSelectbox"] { margin-bottom: 1rem; }
    div.row-widget.stButton { margin-bottom: 0.5rem; }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Заголовок
st.markdown("""
<div class="main-header">
    <h1 class="main-title">Платформа кластерного анализа регионов РФ</h1>
    <p class="sub-title">Интеллектуальная система оценки уровня цифровизации на основе методов машинного обучения</p>
</div>
""", unsafe_allow_html=True)

# Инициализация состояния
if 'log_text' not in st.session_state:
    st.session_state.log_text = "Система готова к работе. Ожидание загрузки данных...\n"
if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False

# Основной контент разбит на 3 колонки: [Настройки] [Модули] [Логи]
col_settings, col_modules, col_logs = st.columns([1, 1, 1.8], gap="medium")

with col_settings:
    st.markdown('<div class="section-title">⚙️ Параметры</div>', unsafe_allow_html=True)
    
    st.markdown("**📁 Исходные данные**")
    # Убрали label_visibility и просто используем пустое название
    uploaded_file = st.file_uploader("", type=["xlsx", "xls"], label_visibility="collapsed")
    
    # Сохранение файла
    file_path = None
    if uploaded_file is not None:
        file_path = "temp_uploaded_data.xlsx"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.file_uploaded = True
        st.success("✅ Данные загружены")
        if "Ожидание загрузки данных" in st.session_state.log_text:
            st.session_state.log_text = "Данные загружены. Выберите модуль аналитики для запуска...\n"
    else:
        st.session_state.file_uploaded = False
        if os.path.exists("temp_uploaded_data.xlsx"):
            file_path = "temp_uploaded_data.xlsx"
            st.session_state.file_uploaded = True
            st.success("✅ Ранее загружено")
        else:
            st.warning("⚠️ Ожидание данных")
            
    st.markdown("<br>**📅 Год исследования**", unsafe_allow_html=True)
    year = st.selectbox(
        "",
        options=[2024, 2023, 2022],
        index=0,
        label_visibility="collapsed"
    )

with col_modules:
    st.markdown('<div class="section-title">🚀 Аналитика</div>', unsafe_allow_html=True)
    
    # Кнопки теперь идут подряд, без section-card
    st.markdown("<br>", unsafe_allow_html=True) # Небольшой отступ для выравнивания с загрузчиком
    dist_btn = st.button("🌍 Макро-анализ (ФО)", key="btn1", disabled=not st.session_state.file_uploaded)
    reg_btn = st.button("🗺️ Мезо-анализ (Внутри ФО)", key="btn2", disabled=not st.session_state.file_uploaded)
    all_reg_btn = st.button("🇷🇺 Микро-анализ (Все РФ)", key="btn3", disabled=not st.session_state.file_uploaded)

with col_logs:
    st.markdown('<div class="section-title">🖥️ Журнал</div>', unsafe_allow_html=True)
    log_placeholder = st.empty()
    
    def render_log(text):
        log_placeholder.markdown(f'<div class="console-box">{text}</div>', unsafe_allow_html=True)
    
    render_log(st.session_state.log_text)

# Обработка нажатий
def process_analysis(level_name, process_func):
    st.session_state.log_text = f"[{time.strftime('%H:%M:%S')}] Инициализация модуля: {level_name}...\n"
    render_log(st.session_state.log_text)
    
    progress_bar = st.progress(0)
    
    try:
        # Перехватываем print() из сервисов
        with io.StringIO() as buf, redirect_stdout(buf):
            process_func()
            output = buf.getvalue()
            
        st.session_state.log_text += output + f"\n[{time.strftime('%H:%M:%S')}] ✅ Модуль '{level_name}' успешно отработал."
        render_log(st.session_state.log_text)
        progress_bar.progress(100)
        st.toast(f"Анализ '{level_name}' завершен!", icon="🎉")
        
    except Exception as e:
        progress_bar.empty()
        st.session_state.log_text += f"\n[{time.strftime('%H:%M:%S')}] ❌ ОШИБКА: {str(e)}"
        render_log(st.session_state.log_text)
        st.error(f"Критическая ошибка выполнения: {str(e)}")

# Функции-обертки для каждого уровня
def run_level_1():
    print(f"Загрузка структуры данных из {file_path} за {year} год...")
    if os.path.exists("output/districts"): shutil.rmtree("output/districts")
    os.makedirs("output/districts", exist_ok=True)
    
    print("Создание пайплайна обработки...")
    data_loader = DistrictDataLoader(file_path)
    clustering_strategy = KMeansClusteringStrategy()
    analyzer = ClusterAnalyzer()
    visualizer = DistrictVisualizer()
    pipeline = Pipeline(data_loader, clustering_strategy, analyzer, visualizer)
    
    print("Выполнение вычислений K-Means и генерация отчетов...")
    pipeline.run(year)

def run_level_2():
    if os.path.exists("output/regions"): shutil.rmtree("output/regions")
    os.makedirs("output/regions", exist_ok=True)
    
    print("Шаг 1/5: Расчет WCSS (Метод локтя) для каждого округа...")
    plot_regions_elbow(year)
    print("Шаг 2/5: Кластеризация K-Means (k=3) по макрорегионам...")
    cluster_regions_by_district(year)
    print("Шаг 3/5: Консолидация локальных результатов в единую матрицу...")
    merge_region_clusters()
    print("Шаг 4/5: Факторный анализ дисперсии центроидов...")
    analyze_cluster_district_factors()
    print("Шаг 5/5: Рендеринг визуализаций (радары, барчарты)...")
    plot_cluster_subjects()
    plot_district_subject_clusters()

def run_level_3():
    if os.path.exists("output/all_regions"): shutil.rmtree("output/all_regions")
    os.makedirs("output/all_regions", exist_ok=True)
    print("Запуск глобального алгоритма кластеризации...")
    run_global_clustering()

# Запуск
if dist_btn: process_analysis("Макроуровень (ФО)", run_level_1)
if reg_btn: process_analysis("Мезоуровень (Внутри ФО)", run_level_2)
if all_reg_btn: process_analysis("Микроуровень (Глобальный)", run_level_3)

# ---------------------------------------------------------
# БЛОК РЕЗУЛЬТАТОВ (ОТРИСОВКА СОХРАНЕННЫХ ФАЙЛОВ)
# ---------------------------------------------------------
st.markdown("---")
st.markdown("## 📊 Визуализация результатов")
st.caption("Здесь отображаются артефакты (графики и таблицы), сгенерированные в ходе работы модулей.")

tab1, tab2, tab3 = st.tabs(["Федеральные округа (Макро)", "Регионы по округам (Мезо)", "Все субъекты РФ (Микро)"])

def display_results(folder_path):
    if os.path.exists(folder_path):
        st.success(f"Данные успешно сгенерированы и доступны в каталоге: `{folder_path}`")
        
        # Поиск таблиц и картинок
        excel_files = []
        images = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                if file.endswith('.xlsx'):
                    excel_files.append(full_path)
                elif file.endswith(('.png', '.jpg', '.jpeg')):
                    images.append(full_path)
        
        # Таблицы
        if excel_files:
            st.markdown("### 📑 Сводные таблицы")
            for xl_file in excel_files:
                with st.expander(f"📄 {os.path.basename(xl_file)}", expanded=False):
                    try:
                        df = pd.read_excel(xl_file)
                        st.dataframe(df, use_container_width=True)
                        
                        # Кнопка скачивания
                        with open(xl_file, "rb") as f:
                            st.download_button(
                                label=f"💾 Скачать {os.path.basename(xl_file)}",
                                data=f,
                                file_name=os.path.basename(xl_file),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"btn_{xl_file}"
                            )
                    except Exception as e:
                        st.error(f"Не удалось отобразить таблицу: {str(e)}")
        
        st.markdown("---")
        
        # Картинки
        if images:
            st.markdown("### 📈 Графики и диаграммы")
            # Сортируем картинки (сначала общие графики, потом конкретные кластеры/округа)
            heatmaps = [img for img in images if 'heatmap' in img.lower() or 'ranking' in img.lower() or 'scatter' in img.lower() or 'elbow' in img.lower()]
            others = [img for img in images if img not in heatmaps]
            
            # Показываем общие графики крупно
            if heatmaps:
                for img_path in heatmaps:
                    try:
                        st.image(Image.open(img_path), caption=os.path.basename(img_path), use_container_width=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                    except: pass
            
            # Показываем остальные сеткой
            if others:
                st.markdown("#### Детализация по кластерам/округам")
                cols = st.columns(3)
                for i, img_path in enumerate(others):
                    with cols[i % 3]:
                        try:
                            st.image(Image.open(img_path), caption=os.path.basename(img_path), use_container_width=True)
                        except: pass
        
        if not excel_files and not images:
             st.info("Директория создана, но в ней нет файлов. Возможно, алгоритм отработал с ошибкой.")
            
    else:
        st.info("💡 Запустите соответствующий модуль аналитики (кнопки выше), чтобы сгенерировать результаты для этого раздела.")

with tab1: display_results("output/districts")
with tab2: display_results("output/regions")
with tab3: display_results("output/all_regions")
