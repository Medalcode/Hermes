import numpy as np
import pandas as pd

from src.core.domain_services import (
    Clusterer,
    DataCleaner,
    DataScaler,
    OutlierManager,
    StatisticalAnalyzer,
)


# --- 1. Statistical Analyzer Tests ---
def test_statistical_analyzer_descriptive():
    df = pd.DataFrame({'A': [1, 2, 3, 4, 5]})
    analyzer = StatisticalAnalyzer()
    stats = analyzer.calculate_descriptive_stats(df)

    assert 'mean' in stats.columns
    assert stats.loc['A', 'mean'] == 3.0
    assert stats.loc['A', 'median'] == 3.0

def test_statistical_analyzer_categorical_check():
    df = pd.DataFrame({'A': [1, 2], 'B': ['a', 'b']})
    assert 'A' in StatisticalAnalyzer.get_numeric_columns(df)
    assert 'B' in StatisticalAnalyzer.get_categorical_columns(df)

# --- 2. Data Cleaner Tests ---
def test_data_cleaner_mean_imputation():
    df = pd.DataFrame({'A': [1, 2, np.nan, 4, 5]})
    cleaner = DataCleaner()
    df_clean, count = cleaner.handle_nulls(df, ['A'], "Llenar con promedio")

    assert count == 1
    assert df_clean['A'].isnull().sum() == 0
    assert df_clean.loc[2, 'A'] == 3.0 # Mean of 1,2,4,5 is 3

def test_data_cleaner_drop_rows():
    df = pd.DataFrame({'A': [1, np.nan, 3]})
    df_clean, count = DataCleaner.handle_nulls(df, ['A'], "Eliminar filas")

    assert count == 1
    assert len(df_clean) == 2

# --- 3. Data Scaler Tests ---
def test_data_scaler_minmax():
    df = pd.DataFrame({'A': [10, 20, 30]})
    scaler = DataScaler()
    df_scaled = scaler.apply_scaling(df, ['A'], "Min-Max")

    assert df_scaled['A'].min() == 0.0
    assert df_scaled['A'].max() == 1.0

# --- 4. Outlier Manager Tests ---
def test_outlier_manager_detection():
    # 100 is an obvious outlier here
    df = pd.DataFrame({'A': [1, 2, 3, 100]})
    df_out, count, msg = OutlierManager.detect_and_treat(df, 'A', "Informar")

    assert count == 1
    assert "Solo detectados" in msg

def test_outlier_manager_removal():
    df = pd.DataFrame({'A': [1, 2, 3, 100]})
    df_out, count, msg = OutlierManager.detect_and_treat(df, 'A', "Eliminar registros")

    assert count == 1
    assert len(df_out) == 3
    assert 100 not in df_out['A'].values

# --- 5. Clusterer Tests ---
def test_clusterer_kmeans():
    # Two clear clusters: (0,0) variants and (10,10) variants
    df = pd.DataFrame({
        'X': [0, 1, 10, 11],
        'Y': [0, 1, 10, 11]
    })

    df_clustered, msg = Clusterer.kmeans(df, ['X', 'Y'], k=2)

    assert 'Cluster' in df_clustered.columns
    assert len(df_clustered['Cluster'].unique()) == 2
    assert "Clustering completado" in msg
