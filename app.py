import streamlit as st
import os
import io
import shutil
import time
from contextlib import redirect_stdout
from PIL import Image
import pandas as pd
import sqlite3

# Импорты бизнес-логики
from models.data_service import DistrictDataLoader
from services.universal_analyzer import UniversalClusterAnalyzer
from models.database import DB_NAME

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
    if os.path.exists("temp_uploaded_data.xlsx"):
        try:
            os.remove("temp_uploaded_data.xlsx")
        except:
            pass
    # Также очищаем старые результаты при новом запуске
    for folder in ["output/districts", "output/regions", "output/all_regions"]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
            except:
                pass
                
    st.session_state.analysis_completed = {
        'macro': False,
        'meso': False,
        'micro': False
    }

if 'log_text' not in st.session_state:
    st.session_state.log_text = "Система готова к работе. Ожидание загрузки данных...\n"

# Основной контент разбит на 3 колонки: [Настройки] [Модули] [Логи]
col_settings, col_modules, col_logs = st.columns([1, 1, 1.8], gap="medium")

with col_settings:
    st.markdown('<div class="section-title">⚙️ Параметры</div>', unsafe_allow_html=True)
    
    st.markdown("**📁 Исходные данные**")
    
    # Файл загружается ТОЛЬКО если пользователь его сам выбрал.
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
        # ВАЖНО: Удаляем временный файл, если загрузчик пуст, чтобы старые данные не использовались!
        if os.path.exists("temp_uploaded_data.xlsx"):
            try:
                os.remove("temp_uploaded_data.xlsx")
            except Exception:
                pass
            
    st.markdown("<br>**📅 Год исследования**", unsafe_allow_html=True)
    year = st.selectbox(
        "",
        options=[2024, 2023, 2022],
        index=0,
        label_visibility="collapsed"
    )

with col_modules:
    st.markdown('<div class="section-title">🚀 Аналитика</div>', unsafe_allow_html=True)
    
    # Кнопки идут просто списком
    st.markdown("<br>", unsafe_allow_html=True) # Небольшой отступ для выравнивания с загрузчиком
    dist_btn = st.button("🌍 Макро-анализ (ФО)", key="btn1", disabled=not file_is_ready)
    reg_btn = st.button("🗺️ Мезо-анализ (Внутри ФО)", key="btn2", disabled=not file_is_ready)
    all_reg_btn = st.button("🇷🇺 Микро-анализ (Все РФ)", key="btn3", disabled=not file_is_ready)

with col_logs:
    st.markdown('<div class="section-title">🖥️ Журнал</div>', unsafe_allow_html=True)
    log_placeholder = st.empty()
    
    def render_log(text):
        log_placeholder.markdown(f'<div class="console-box">{text}</div>', unsafe_allow_html=True)
    
    render_log(st.session_state.log_text)

# Обработка нажатий
def process_analysis(level_key, level_name, process_func):
    st.session_state.log_text = f"[{time.strftime('%H:%M:%S')}] Инициализация модуля: {level_name}...\n"
    render_log(st.session_state.log_text)
    
    progress_bar = st.progress(0)
    
    try:
        # Сначала загружаем данные в БД (это общее для всех уровней)
        with io.StringIO() as buf, redirect_stdout(buf):
            data_loader = DistrictDataLoader(file_path)
            data_loader.load_data(year) 
        
        # Выполняем саму логику уровня
        with io.StringIO() as buf, redirect_stdout(buf):
            process_func()
            output = buf.getvalue()
            
        st.session_state.log_text += output + f"\n[{time.strftime('%H:%M:%S')}] ✅ Модуль '{level_name}' успешно отработал."
        render_log(st.session_state.log_text)
        progress_bar.progress(100)
        
        # Отмечаем анализ как выполненный (привязка теперь по наличию файлов, но флаг тоже меняем)
        st.session_state.analysis_completed[level_key] = True
        
        st.toast(f"Анализ '{level_name}' завершен!", icon="🎉")
        
    except Exception as e:
        progress_bar.empty()
        st.session_state.log_text += f"\n[{time.strftime('%H:%M:%S')}] ❌ ОШИБКА: {str(e)}"
        render_log(st.session_state.log_text)
        st.error(f"Критическая ошибка выполнения: {str(e)}")

# --- УНИВЕРСАЛЬНЫЕ ФУНКЦИИ ЗАПУСКА АНАЛИЗА ---

def run_level_1():
    print(f"Запуск макро-анализа (Федеральные округа) за {year} год...")
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


def run_level_2():
    if os.path.exists("output/regions"): shutil.rmtree("output/regions")
    
    print(f"Запуск мезо-анализа (Регионы по ФО) за {year} год...")
    conn = sqlite3.connect(DB_NAME)
    districts = pd.read_sql("SELECT id, name FROM federal_districts", conn)
    
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
        
    conn.close()
    print("Мезо-анализ по всем федеральным округам завершен.")


def run_level_3():
    if os.path.exists("output/all_regions"): shutil.rmtree("output/all_regions")
        
    print(f"Запуск микро-анализа (Все субъекты РФ) за {year} год...")
    
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

# Запуск (с передачей ключа)
if dist_btn: process_analysis('macro', "Макроуровень (ФО)", run_level_1)
if reg_btn: process_analysis('meso', "Мезоуровень (Внутри ФО)", run_level_2)
if all_reg_btn: process_analysis('micro', "Микроуровень (Глобальный)", run_level_3)

# ---------------------------------------------------------
# БЛОК РЕЗУЛЬТАТОВ (УНИВЕРСАЛЬНЫЙ)
# ---------------------------------------------------------
st.markdown("---")
st.markdown("## 📊 Визуализация результатов")
st.caption("Разверните вкладки ниже, чтобы просмотреть результаты (таблицы, графики, диаграммы) для каждого уровня аналитики.")

tab1, tab2, tab3 = st.tabs(["🌍 Федеральные округа (Макро)", "🗺️ Регионы по округам (Мезо)", "🇷🇺 Все субъекты РФ (Микро)"])

def render_level_data(folder_path, prefix=""):
    """
    Универсальная функция рендеринга всех артефактов (внутри раскрывающихся списков)
    для одного конкретного датасета (один ФО, или вся РФ).
    """
    excel_files = []
    images = []
    
    # Собираем файлы ТОЛЬКО из этой папки и нужных подпапок
    if os.path.exists(folder_path):
        for file in os.listdir(folder_path):
            full_path = os.path.join(folder_path, file)
            if os.path.isfile(full_path):
                if file.endswith('.xlsx'):
                    excel_files.append(full_path)
                elif file.endswith(('.png', '.jpg', '.jpeg')):
                    images.append(full_path)
        
        # Для вложенных папок tables/plots/diagrams
        for sub_f in ["tables", "plots", "diagrams"]:
            sub_p = os.path.join(folder_path, sub_f)
            if os.path.exists(sub_p):
                for file in os.listdir(sub_p):
                    full_path = os.path.join(sub_p, file)
                    if os.path.isfile(full_path):
                        if file.endswith('.xlsx'):
                            excel_files.append(full_path)
                        elif file.endswith(('.png', '.jpg', '.jpeg')):
                            images.append(full_path)

    # 1. Метод локтя
    elbow = [img for img in images if 'elbow' in img.lower()]
    if elbow:
        with st.expander(f"{prefix}📉 Метод локтя (Оптимальное число кластеров)", expanded=False):
            st.image(Image.open(elbow[0]), use_container_width=True)

    # 2. Таблица кластеризации (кто в каком кластере)
    assignment_file = [f for f in excel_files if 'assignments' in f.lower() or 'clusters' in f.lower()]
    if assignment_file:
        with st.expander(f"{prefix}📑 Таблица принадлежности к кластерам", expanded=False):
            try:
                df = pd.read_excel(assignment_file[0])
                if "Unnamed: 0" in df.columns: df = df.drop(columns=["Unnamed: 0"])
                st.dataframe(df, use_container_width=True)
                with open(assignment_file[0], "rb") as f:
                    st.download_button("💾 Скачать таблицу кластеров", f, os.path.basename(assignment_file[0]), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"btn_assig_{assignment_file[0]}")
            except Exception as e:
                st.error(f"Ошибка чтения: {e}")

    # 3. Таблица средних значений по кластерам
    means_file = [f for f in excel_files if 'means' in f.lower() or 'feature' in f.lower()]
    if means_file:
        with st.expander(f"{prefix}📑 Таблица средних значений факторов", expanded=False):
            try:
                df = pd.read_excel(means_file[0])
                if "Unnamed: 0" in df.columns: df = df.drop(columns=["Unnamed: 0"])
                st.dataframe(df, use_container_width=True)
                with open(means_file[0], "rb") as f:
                    st.download_button("💾 Скачать таблицу средних", f, os.path.basename(means_file[0]), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"btn_means_{means_file[0]}")
            except Exception as e:
                st.error(f"Ошибка чтения: {e}")

    # 4. Тепловая карта 
    heatmap = [img for img in images if 'heatmap' in img.lower()]
    if heatmap:
        with st.expander(f"{prefix}🔥 Тепловая карта различий факторов", expanded=False):
            st.image(Image.open(heatmap[0]), use_container_width=True)

    # 5. Точечная диаграмма (PCA)
    scatter = [img for img in images if 'scatter' in img.lower() or 'pca' in img.lower()]
    if scatter:
        with st.expander(f"{prefix}📍 Пространственное распределение кластеров (PCA)", expanded=False):
            st.image(Image.open(scatter[0]), use_container_width=True)

    # 6. Профили кластеров (Радары и столбцы)
    radars = [img for img in images if 'radar' in img.lower()]
    bars = [img for img in images if 'bar' in img.lower()]
    
    if radars or bars:
        with st.expander(f"{prefix}📊 Детализация по кластерам (Радары и диаграммы)", expanded=False):
            cluster_nums = set()
            for f in radars + bars:
                try:
                    base_name = os.path.basename(f)
                    num = base_name.split('cluster_')[1].split('.')[0]
                    cluster_nums.add(num)
                except: pass
            
            for num in sorted(list(cluster_nums)):
                st.markdown(f"#### Кластер {num}")
                r_col, b_col = st.columns(2)
                r_img = [img for img in radars if f"cluster_{num}" in img]
                b_img = [img for img in bars if f"cluster_{num}" in img]
                with r_col:
                    if r_img: st.image(Image.open(r_img[0]), use_container_width=True)
                with b_col:
                    if b_img: st.image(Image.open(b_img[0]), use_container_width=True)
                st.markdown("---")

def display_results(folder_path):
    if os.path.exists(folder_path):
        # Проверяем, пуста ли папка
        if not os.listdir(folder_path):
            st.info("💡 Запустите соответствующий модуль аналитики (кнопки выше), чтобы сгенерировать результаты для этого раздела.")
            return

        # Если это мезо-уровень (там папки внутри папок для каждого округа)
        # Мы проверяем, есть ли там вложенные папки, которые НЕ являются служебными (tables, plots, diagrams)
        subdirs = [os.path.join(folder_path, d) for d in os.listdir(folder_path) 
                  if os.path.isdir(os.path.join(folder_path, d)) and d not in ["tables", "plots", "diagrams"]]
        
        if subdirs:
            st.success(f"Анализ успешно завершен. Разверните нужный округ для просмотра данных:")
            for subdir in subdirs:
                district_name = os.path.basename(subdir).replace("_", " ")
                with st.expander(f"🗺️ {district_name}"):
                    render_level_data(subdir, prefix="")
        else:
            # Для макро и микро уровней просто рендерим корень
            st.success(f"Анализ успешно завершен. Результаты ниже:")
            render_level_data(folder_path)
            
    else:
        st.info("💡 Запустите соответствующий модуль аналитики (кнопки выше), чтобы сгенерировать результаты для этого раздела.")

# Мы проверяем только наличие папки, без жесткой зависимости от флага, чтобы контент не пропадал
with tab1: display_results("output/districts")
with tab2: display_results("output/regions")
with tab3: display_results("output/all_regions")
