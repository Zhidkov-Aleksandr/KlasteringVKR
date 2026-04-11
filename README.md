Программно-аналитический комплекс для кластеризации регионов

## Запуск

### Консольная версия
```bash
python controllers/main.py
```

### Графическая версия (GUI)
```bash
python controllers/gui_main.py
```

**Примечание:** Запускайте GUI в отдельном окне командной строки Windows для корректной работы диалогов выбора файла.

## Структура проекта

Проект организован по принципам MVC архитектуры:

```
controllers/          # Контроллеры (основная логика)
├── main.py          # Консольная версия
└── gui_main.py      # Запуск GUI

models/              # Модели (данные и бизнес-логика)
├── architecture.py  # Абстрактные классы
├── data_service.py  # Загрузка данных
├── clustering_service.py  # Сервис кластеризации
├── analysis_service.py    # Сервис анализа
└── database.py      # Работа с БД

views/               # Представления (GUI и визуализация)
├── gui.py           # Основное GUI окно
├── gui_components.py # Компоненты GUI
├── visualization_service.py  # Сервис визуализации
└── [файлы графиков] # elbow_method.py, district_plots.py, etc.

services/            # Сервисы (специфическая бизнес-логика)
├── clustering.py    # Кластеризация округов
├── clustering_all_regions.py  # Кластеризация всех регионов
├── regions_clustering.py     # Кластеризация регионов
├── merge_region_clusters.py  # Объединение кластеров
├── analysis_cluster_factors.py  # Анализ факторов
├── cluster_subject_plots.py   # Графики кластеров субъектов
├── district_subject_cluster_plots.py  # Графики округов
└── regions_elbow.py  # Метод локтя для регионов

utils/               # Утилиты
├── excel_loader.py  # Загрузка Excel
├── cleanup_plots.py # Очистка графиков
├── cluster_analysis.py  # Анализ кластеров
└── district_clustering.py  # Кластеризация округов

data/                # Данные
└── digitalization.db  # База данных
```

## Структура выходных данных

Все файлы сохраняются в папку `output/` со следующей структурой:

```
output/
├── districts/          # Кластеризация федеральных округов
│   ├── tables/         # Таблицы (Excel)
│   ├── plots/          # Графики (PNG)
│   └── diagrams/       # Диаграммы (PNG)
├── regions/            # Кластеризация регионов по округам
│   ├── tables/         # Таблицы (Excel)
│   ├── plots/          # Графики (PNG)
│   └── diagrams/       # Диаграммы (PNG)
└── all_regions/        # Кластеризация всех регионов
    ├── tables/         # Таблицы (Excel)
    ├── plots/          # Графики (PNG)
    └── diagrams/       # Диаграммы (PNG)
```

## Особенности

- **Очистка выходных данных**: При запуске каждого типа анализа (федеральные округа, регионы, все регионы) соответствующая папка в `output/` автоматически очищается перед записью новых данных.
- **Структурированный вывод**: Все файлы сохраняются в организованной иерархии директорий в папке `output/`.
- **Отсутствие промежуточных файлов**: Промежуточные данные хранятся внутри `output/`, старые директории `plots/` и `results/` не создаются.

## Зависимости
- pandas
- scikit-learn
- matplotlib
- openpyxl
- seaborn
- customtkinter

Установите зависимости:
```bash
pip install -r requirements.txt
```
