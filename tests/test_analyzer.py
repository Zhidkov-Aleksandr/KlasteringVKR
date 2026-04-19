import pytest
import pandas as pd
import numpy as np
from services.universal_analyzer import UniversalClusterAnalyzer
import os

@pytest.fixture
def mock_data():
    """Фиктивные данные для тестирования (3 региона, 2 фактора)."""
    data = {
        'Фактор 1': [10, 50, 100],
        'Фактор 2': [5, 45, 95]
    }
    df = pd.DataFrame(data, index=['Регион А (Аутсайдер)', 'Регион Б (Середняк)', 'Регион В (Лидер)'])
    return df

@pytest.fixture
def analyzer(mock_data, tmp_path):
    """Создает экземпляр анализатора с временной директорией для вывода."""
    return UniversalClusterAnalyzer(mock_data, str(tmp_path), "Тестовый Уровень")

def test_initialization(analyzer):
    """Проверка правильной инициализации и масштабирования (StandardScaler)."""
    assert analyzer.data is not None
    assert analyzer.X_scaled is not None
    assert analyzer.X_scaled.shape == (3, 2)
    # Проверка, что StandardScaler отработал: среднее должно быть ~0, дисперсия ~1
    assert np.allclose(analyzer.X_scaled.mean(axis=0), [0, 0], atol=1e-5)

def test_missing_data_handling(tmp_path):
    """Проверка: пропуски заменяются минимальным значением по столбцу."""
    df_missing = pd.DataFrame({'F1': [10, np.nan, 30], 'F2': [5, 15, 25]}, index=['R1', 'R2', 'R3'])
    ana = UniversalClusterAnalyzer(df_missing, str(tmp_path), "Test Missing")
    # np.nan в R2 должен был стать 10.0 (минимум по 'F1')
    assert ana.data.loc['R2', 'F1'] == 10.0

def test_run_clustering(analyzer):
    """Проверка запуска K-Means и умной сортировки кластеров (Лидер -> Кластер 1)."""
    analyzer.run_clustering(k=3)
    assert analyzer.n_clusters == 3
    assert 'Кластер' in analyzer.data.columns
    assert 'Описание кластера' in analyzer.data.columns
    
    # Лидер должен оказаться в Кластере 1
    leader_cluster = analyzer.data.loc['Регион В (Лидер)', 'Кластер']
    assert leader_cluster == 1
    assert analyzer.data.loc['Регион В (Лидер)', 'Описание кластера'] == 'Передовые'

def test_export_directories_created(analyzer, tmp_path):
    """Проверка, что все необходимые папки создаются автоматически."""
    assert os.path.exists(os.path.join(tmp_path, "diagrams"))
    assert os.path.exists(os.path.join(tmp_path, "tables"))
    assert os.path.exists(os.path.join(tmp_path, "plots"))