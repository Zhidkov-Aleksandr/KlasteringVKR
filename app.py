import streamlit as st
import os
import io
import shutil
import time
from contextlib import redirect_stdout
from PIL import Image
import pandas as pd
import sqlite3
import streamlit.components.v1 as components

# Импорты бизнес-логики
from models.data_service import DistrictDataLoader
from services.universal_analyzer import UniversalClusterAnalyzer
from models.database import DB_NAME
from utils.test_runner import run_project_tests

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

# При инициализации очищаем состояние, чтобы старые файлы не подхватывались автоматически
if 'app_initialized' not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.log_text = "Система готова к работе. Ожидание загрузки данных...\n"
    # Удаляем временный файл чтобы заставить грузить новый
    if os.path.exists("temp_uploaded_data.xlsx"):
        try:
            os.remove("temp_uploaded_data.xlsx")
        except:
            pass
    # Очищаем старые результаты
    for folder in ["output/districts", "output/regions", "output/all_regions"]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
            except:
                pass

if 'log_text' not in st.session_state:
    st.session_state.log_text = "Система готова к работе. Ожидание загрузки данных...\n"

# Основной контент разбит на 3 колонки: [Настройки] [Модули] [Логи]
col_settings, col_modules, col_logs = st.columns([1, 1, 1.8], gap="medium")

with col_settings:
    st.markdown('<div class="section-title">⚙️ Параметры</div>', unsafe_allow_html=True)
    
    st.markdown("**📁 Исходные данные**")
    
    uploaded_file = st.file_uploader("", type=["xlsx", "xls"], label_visibility="collapsed")
    
    file_path = None
    file_is_ready = False
    
    if uploaded_file is not None:
        file_path = "temp_uploaded_data.xlsx"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        file_is_ready = True
        st.success("✅ Данные загружены")
        if "Ожидание загрузки данных" in st.session_state.log_text:
            st.session_state.log_text = "Данные загружены. Выберите модуль аналитики для запуска...\n"
    else:
        st.warning("⚠️ Ожидание данных")
        file_is_ready = False
        if os.path.exists("temp_uploaded_data.xlsx"):
            try:
                os.remove("temp_uploaded_data.xlsx")
            except Exception:
                pass

with col_modules:
    st.markdown('<div class="section-title">🔎 Аналитика</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True) 
    # Используем use_container_width=True для всех кнопок
    dist_btn = st.button("🌍 Макро-анализ (Все ФО)", key="btn1", disabled=not file_is_ready, use_container_width=True)
    reg_btn = st.button("🗺️ Мезо-анализ (Внутри каждого ФО)", key="btn2", disabled=not file_is_ready, use_container_width=True)
    all_reg_btn = st.button("🇷🇺 Микро-анализ (Все регионы РФ)", key="btn3", disabled=not file_is_ready, use_container_width=True)

with col_logs:
    st.markdown('<div class="section-title">🖥️ Журнал</div>', unsafe_allow_html=True)
    log_placeholder = st.empty()
    
    def render_log(text):
        log_placeholder.markdown(f'<div class="console-box">{text}</div>', unsafe_allow_html=True)
    
    render_log(st.session_state.log_text)


# Фиксированный год для базы данных
DEFAULT_YEAR = 2024

# Инициализация флагов для принудительного обновления UI
if 'update_key' not in st.session_state:
    st.session_state.update_key = 0

# Обработка нажатий
def process_analysis(level_name, process_func):
    st.session_state.log_text = f"[{time.strftime('%H:%M:%S')}] Инициализация модуля: {level_name}...\n"
    render_log(st.session_state.log_text)
    
    progress_bar = st.progress(0)
    
    try:
        # Сначала загружаем данные в БД (это общее для всех уровней)
        with io.StringIO() as buf, redirect_stdout(buf):
            data_loader = DistrictDataLoader(file_path)
            data_loader.load_data(DEFAULT_YEAR) 
        
        # Выполняем саму логику уровня
        with io.StringIO() as buf, redirect_stdout(buf):
            process_func(DEFAULT_YEAR)
            output = buf.getvalue()
            
        st.session_state.log_text += output + f"\n[{time.strftime('%H:%M:%S')}] ✅ Модуль '{level_name}' успешно отработал."
        render_log(st.session_state.log_text)
        progress_bar.progress(100)
        
        st.toast(f"Анализ '{level_name}' завершен!", icon="🎉")
        
        # Увеличиваем ключ, чтобы Streamlit принудительно перерисовал блок с результатами
        st.session_state.update_key += 1
        
    except Exception as e:
        progress_bar.empty()
        st.session_state.log_text += f"\n[{time.strftime('%H:%M:%S')}] ❌ ОШИБКА: {str(e)}"
        render_log(st.session_state.log_text)
        st.error(f"Критическая ошибка выполнения: {str(e)}")

# --- УНИВЕРСАЛЬНЫЕ ФУНКЦИИ ЗАПУСКА АНАЛИЗА ---

def run_level_1(year):
    print(f"Запуск макро-анализа (Федеральные округа)...")
    # Полностью очищаем папку перед новым запуском
    if os.path.exists("output/districts"): shutil.rmtree("output/districts")
    
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT fd.name as district, i.name as indicator, v.value
    FROM values_data v
    JOIN indicators i ON v.indicator_id = i.id
    JOIN federal_districts fd ON v.territory_id = fd.id
    WHERE v.territory_type = 'district' AND v.year = ?
    """
    df = pd.read_sql_query(query, conn, params=(year,))
    conn.close()

    matrix = df.pivot(index="district", columns="indicator", values="value")
    
    analyzer = UniversalClusterAnalyzer(
        data=matrix, 
        output_dir="output/districts", 
        level_name="Федеральные округа РФ"
    )
    analyzer.run_all(k=3)


def run_level_2(year):
    # Полностью очищаем папку перед новым запуском
    if os.path.exists("output/regions"): shutil.rmtree("output/regions")

    print(f"Запуск мезо-анализа (Регионы по ФО)...")
    conn = sqlite3.connect(DB_NAME)
    districts = pd.read_sql("SELECT id, name FROM federal_districts", conn)

    all_meso_results = []
    elbow_data_dict = {}  # Store elbow data for all districts

    for _, district in districts.iterrows():
        d_id = district["id"]
        d_name = district["name"]

        query = f"""
        SELECT r.name as region, i.name as indicator, v.value
        FROM values_data v
        JOIN regions r ON v.territory_id = r.id
        JOIN indicators i ON v.indicator_id = i.id
        WHERE v.territory_type = 'region' AND r.federal_district_id = {d_id} AND v.year = {year}
        """
        df = pd.read_sql(query, conn)
        if df.empty: continue

        matrix = df.pivot(index="region", columns="indicator", values="value")

        d_name_safe = d_name.replace(" ", "_")
        analyzer = UniversalClusterAnalyzer(
            data=matrix,
            output_dir=f"output/regions/{d_name_safe}",
            level_name=d_name
        )
        analyzer.run_all(k=3)

        # Collect elbow data for global comparison
        if analyzer.elbow_K is not None and analyzer.elbow_distortions is not None:
            elbow_data_dict[d_name] = (analyzer.elbow_K, analyzer.elbow_distortions)

        # Сбор данных для глобального сравнения
        if analyzer.cluster_means is not None:
            means_copy = analyzer.cluster_means.copy()
            means_copy['Округ'] = d_name
            means_copy['Кластер'] = means_copy.index
            means_copy['Описание кластера'] = means_copy.index.map(analyzer.cluster_names_map)
            all_meso_results.append(means_copy)

    conn.close()

    if all_meso_results:
        combined_df = pd.concat(all_meso_results, ignore_index=True)
        UniversalClusterAnalyzer.plot_meso_comparison(
            combined_df,
            "output/regions/global_meso_comparison.png"
        )
        UniversalClusterAnalyzer.plot_meso_comparison_interactive(
            combined_df,
            "output/regions/global_meso_comparison.html"
        )
        UniversalClusterAnalyzer.plot_meso_comparison_radar(
            combined_df,
            "output/regions/global_meso_comparison_radar.png"
        )

    # Generate global elbow method comparison
    if elbow_data_dict:
        UniversalClusterAnalyzer.plot_meso_elbow_comparison(
            elbow_data_dict,
            "output/regions/global_meso_elbow_method.png"
        )

    print("Мезо-анализ по всем федеральным округам завершен.")


def run_level_3(year):
    # Полностью очищаем папку перед новым запуском
    if os.path.exists("output/all_regions"): shutil.rmtree("output/all_regions")
        
    print(f"Запуск микро-анализа (Все субъекты РФ)...")
    
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT r.name as region, i.name as indicator, v.value
    FROM values_data v
    JOIN regions r ON v.territory_id = r.id
    JOIN indicators i ON v.indicator_id = i.id
    WHERE v.territory_type = 'region' AND v.year = ?
    """
    df = pd.read_sql_query(query, conn, params=(year,))
    conn.close()

    matrix = df.pivot(index="region", columns="indicator", values="value")
    
    analyzer = UniversalClusterAnalyzer(
        data=matrix, 
        output_dir="output/all_regions", 
        level_name="Все субъекты РФ"
    )
    analyzer.run_all(k=3)

# Запуск
if dist_btn: process_analysis("Макроуровень (ФО)", run_level_1)
if reg_btn: process_analysis("Мезоуровень (Внутри ФО)", run_level_2)
if all_reg_btn: process_analysis("Микроуровень (Глобальный)", run_level_3)

# ---------------------------------------------------------
# БЛОК РЕЗУЛЬТАТОВ (УНИВЕРСАЛЬНЫЙ)
# ---------------------------------------------------------
st.markdown("---")
st.markdown("## 📊 Визуализация результатов")
st.caption("Разверните вкладки ниже, чтобы просмотреть результаты (таблицы, графики, диаграммы) для каждого уровня аналитики.")

tab1, tab2, tab3, tab4 = st.tabs(["🌍 Федеральные округа (Макро)", "🗺️ Регионы по округам (Мезо)", "🇷🇺 Все субъекты РФ (Микро)", "🛠️ Тестирование"])

def render_level_data(folder_path, prefix="", unique_key=""):
    """
    Универсальная функция рендеринга всех артефактов для одного датасета.
    """
    excel_files, images, html_files = {}, {}, {}
    
    # Собираем все файлы, индексируя их по имени для удобства
    for root, _, files in os.walk(folder_path):
        for file in files:
            full_path = os.path.join(root, file)
            if file.endswith('.xlsx'):
                excel_files[file] = full_path
            elif file.endswith(('.png', '.jpg', '.jpeg')):
                images[file] = full_path
            elif file.endswith('.html'):
                html_files[file] = full_path

    # 1. Обоснование выбора числа кластеров
    validation_files_exist = any(f in images for f in ['elbow_method.png', 'silhouette_score.png', 'davies_bouldin_score.png', 'calinski_harabasz_score.png', 'dbscan_validation.png'])
    if validation_files_exist:
        with st.expander(f"{prefix}📉 Обоснование выбора числа кластеров (k)", expanded=False):
            st.info("💡 Здесь представлены результаты различных алгоритмов для определения оптимального числа кластеров.")
            
            # Интерактивный дашборд
            if 'consensus_dashboard.html' in html_files:
                with open(html_files['consensus_dashboard.html'], 'r', encoding='utf-8') as f:
                    components.html(f.read(), height=550)
            
            # Таблица консенсуса
            if 'consensus_table.xlsx' in excel_files:
                st.markdown("##### Сводная таблица (Консенсус)")
                try:
                    df_consensus = pd.read_excel(excel_files['consensus_table.xlsx'])
                    st.dataframe(df_consensus, use_container_width=True)
                except Exception as e:
                    st.error(f"Ошибка чтения таблицы консенсуса: {e}")
            
            # Графики методов
            st.markdown("##### Графики алгоритмов")
            col1, col2 = st.columns(2)
            with col1:
                if 'elbow_method.png' in images: st.image(Image.open(images['elbow_method.png']), caption='Метод локтя (Инерция)')
                if 'davies_bouldin_score.png' in images: st.image(Image.open(images['davies_bouldin_score.png']), caption='Индекс Дэвиса-Болдина (ниже - лучше)')
                if 'dbscan_validation.png' in images: st.image(Image.open(images['dbscan_validation.png']), caption='DBSCAN (Оценка через плотность)')
            with col2:
                if 'silhouette_score.png' in images: st.image(Image.open(images['silhouette_score.png']), caption='Коэффициент силуэта (выше - лучше)')
                if 'calinski_harabasz_score.png' in images: st.image(Image.open(images['calinski_harabasz_score.png']), caption='Индекс Калинского-Харабаша (выше - лучше)')

    # 2. Таблицы
    if 'cluster_assignments.xlsx' in excel_files:
        with st.expander(f"{prefix}📑 Таблица принадлежности к кластерам", expanded=False):
            try:
                df = pd.read_excel(excel_files['cluster_assignments.xlsx'])
                st.dataframe(df.drop(columns=[c for c in df.columns if 'Unnamed' in c], errors='ignore'), use_container_width=True)
                with open(excel_files['cluster_assignments.xlsx'], "rb") as f:
                    st.download_button("💾 Скачать", f, "cluster_assignments.xlsx", key=f"btn_assig_{unique_key}")
            except Exception as e:
                st.error(f"Ошибка чтения: {e}")

    if 'cluster_means.xlsx' in excel_files:
        with st.expander(f"{prefix}📑 Таблица средних значений факторов", expanded=False):
            try:
                df = pd.read_excel(excel_files['cluster_means.xlsx'])
                st.dataframe(df.drop(columns=[c for c in df.columns if 'Unnamed' in c], errors='ignore'), use_container_width=True)
                with open(excel_files['cluster_means.xlsx'], "rb") as f:
                    st.download_button("💾 Скачать", f, "cluster_means.xlsx", key=f"btn_means_{unique_key}")
            except Exception as e:
                st.error(f"Ошибка чтения: {e}")

    # 3. Визуализации
    if 'heatmap_factors.png' in images:
        with st.expander(f"{prefix}🔥 Тепловая карта различий факторов", expanded=False):
            st.image(Image.open(images['heatmap_factors.png']), use_container_width=True)

    if 'map_interactive.html' in html_files:
        with st.expander(f"{prefix}🗺️ Интерактивная карта кластеров", expanded=False):
            with open(html_files['map_interactive.html'], 'r', encoding='utf-8') as f:
                components.html(f.read(), height=750)

    if 'pca_interactive.html' in html_files or 'pca_scatter.png' in images:
        with st.expander(f"{prefix}📍 Пространственное распределение кластеров (PCA)", expanded=False):
            if 'pca_interactive.html' in html_files:
                with open(html_files['pca_interactive.html'], 'r', encoding='utf-8') as f:
                    components.html(f.read(), height=600)
            elif 'pca_scatter.png' in images:
                st.image(Image.open(images['pca_scatter.png']), use_container_width=True)

    # Обобщающие диаграммы
    comp_files_exist = any(f in images for f in ['clusters_comparison.png', 'clusters_comparison_split.png', 'clusters_comparison_radar.png'])
    if comp_files_exist:
        with st.expander(f"{prefix}📊 Обобщающие диаграммы: сравнение всех кластеров", expanded=False):
            if 'clusters_comparison.png' in images: st.image(Image.open(images['clusters_comparison.png']), use_container_width=True)
            if 'clusters_comparison_split.png' in images: st.image(Image.open(images['clusters_comparison_split.png']), use_container_width=True)
            if 'clusters_comparison_radar.png' in images: st.image(Image.open(images['clusters_comparison_radar.png']), use_container_width=True)

    # Детализация по кластерам
    radars = [f for f in images if 'radar_cluster_' in f]
    bars = [f for f in images if 'bar_cluster_' in f]
    if radars or bars:
        with st.expander(f"{prefix}📊 Детализация по кластерам (Радары и диаграммы)", expanded=False):
            cluster_nums = sorted(list(set([f.split('cluster_')[1].split('.')[0] for f in radars + bars])))
            for num in cluster_nums:
                st.markdown(f"#### Кластер {num}")
                r_col, b_col = st.columns(2)
                if f"radar_cluster_{num}.png" in images: r_col.image(Image.open(images[f"radar_cluster_{num}.png"]), use_container_width=True)
                if f"bar_cluster_{num}.png" in images: b_col.image(Image.open(images[f"bar_cluster_{num}.png"]), use_container_width=True)
                st.markdown("---")

def display_results(folder_path, tab_id):
    if os.path.exists(folder_path) and os.listdir(folder_path):
        # Глобальное сравнение для мезо-уровня
        if tab_id == "meso":
            global_files = {
                'img': os.path.join(folder_path, "global_meso_comparison.png"),
                'html': os.path.join(folder_path, "global_meso_comparison.html"),
                'radar': os.path.join(folder_path, "global_meso_comparison_radar.png"),
                'elbow': os.path.join(folder_path, "global_meso_elbow_method.png")
            }
            if any(os.path.exists(p) for p in global_files.values()):
                with st.expander("🇷🇺 Глобальное сравнение: Все федеральные округа (мезо-уровень)", expanded=True):
                    if os.path.exists(global_files['html']):
                        st.markdown("**Интерактивная диаграмма:**")
                        with open(global_files['html'], 'r', encoding='utf-8') as f:
                            components.html(f.read(), height=750, scrolling=True)
                    if os.path.exists(global_files['img']):
                        st.markdown("**Статическая диаграмма:**")
                        st.image(Image.open(global_files['img']), use_container_width=True)
                    if os.path.exists(global_files['radar']):
                        st.markdown("**Радарная диаграмма:**")
                        st.image(Image.open(global_files['radar']), use_container_width=True)
                    if os.path.exists(global_files['elbow']):
                        st.markdown("**Сравнение метода локтя по всем округам:**")
                        st.image(Image.open(global_files['elbow']), use_container_width=True)
                st.markdown("---")

        # Рендеринг данных для каждого уровня/подуровня
        system_folders = ['tables', 'plots', 'diagrams']
        subdirs = [d for d in os.listdir(folder_path) 
                   if os.path.isdir(os.path.join(folder_path, d)) and d not in system_folders]

        if subdirs:
            st.success(f"Анализ успешно завершен. Разверните нужный округ для просмотра данных:")
            for subdir_name in subdirs:
                with st.expander(f"🗺️ {subdir_name.replace('_', ' ')}"):
                    render_level_data(os.path.join(folder_path, subdir_name), unique_key=f"{tab_id}_{subdir_name}")
        else:
            st.success(f"Анализ успешно завершен. Результаты ниже:")
            render_level_data(folder_path, unique_key=tab_id)
    else:
        st.info("💡 Запустите соответствующий модуль аналитики, чтобы сгенерировать результаты.")

# Используем st.session_state.update_key, чтобы принудительно перерисовывать вкладки
with tab1: 
    st.markdown(f'<div style="display:none">{st.session_state.update_key}</div>', unsafe_allow_html=True)
    display_results("output/districts", "macro")
with tab2: 
    st.markdown(f'<div style="display:none">{st.session_state.update_key}</div>', unsafe_allow_html=True)
    display_results("output/regions", "meso")
with tab3: 
    st.markdown(f'<div style="display:none">{st.session_state.update_key}</div>', unsafe_allow_html=True)
    display_results("output/all_regions", "micro")

with tab4:
    st.markdown("### 🧪 Модульное и интеграционное тестирование")
    st.write("Нажмите кнопку ниже, чтобы запустить автоматическую проверку математических модулей и алгоритмов системы.")
    
    test_btn = st.button("🚀 Запустить системные тесты")
    
    if test_btn:
        with st.spinner("Выполнение тестов..."):
            try:
                exit_code, report = run_project_tests()
                if exit_code == 0:
                    st.success("✅ Все тесты пройдены успешно!")
                else:
                    st.warning(f"⚠️ Тестирование завершено с предупреждениями или ошибками (Код: {exit_code})")
                with st.expander("📄 Подробный отчет о тестировании", expanded=True):
                    st.code(report)
            except Exception as e:
                st.error(f"Ошибка при запуске тестов: {e}")
                st.info("Убедитесь, что библиотека pytest установлена в окружении.")