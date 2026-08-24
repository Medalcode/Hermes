import io

import numpy as np
import pandas as pd

from src.adapters.fs.file_io import FileSystemAdapter
from src.adapters.visualization.plotter import PlottingAdapter
from src.core.domain_services import (
    Clusterer,
    DataCleaner,
    DataScaler,
    OutlierManager,
    StatisticalAnalyzer,
)


# --- StatisticalAnalyzer Edge Cases ---
def test_statistical_analyzer_empty_df():
    analyzer = StatisticalAnalyzer()
    assert StatisticalAnalyzer.get_numeric_columns(None) == []
    assert StatisticalAnalyzer.get_categorical_columns(None) == []
    assert analyzer.calculate_descriptive_stats(pd.DataFrame()).empty
    assert analyzer.calculate_distribution_shape(pd.DataFrame()).empty
    assert analyzer.calculate_correlation_matrix(pd.DataFrame()).empty


def test_statistical_analyzer_check_normality():
    analyzer = StatisticalAnalyzer()
    is_normal, p_val = analyzer.check_normality(pd.Series([1, 2]))
    assert not is_normal
    assert p_val == 0.0

    is_normal, p_val = analyzer.check_normality(pd.Series([1, 2, 3, 4, 5, 6, 7]))
    assert is_normal


# --- DataCleaner & Strategies Edge Cases ---
def test_data_cleaner_all_strategies():
    df = pd.DataFrame(
        {
            "num": [10.0, 20.0, np.nan, 40.0, 50.0],
            "cat": ["a", "b", np.nan, "b", "b"],
        }
    )

    cleaner = DataCleaner()

    # Median
    df_med, count = cleaner.handle_nulls(df.copy(), ["num"], "Llenar con mediana (Mejora 5)")
    assert count == 1
    assert df_med.loc[2, "num"] == 30.0

    # Max
    df_max, _ = cleaner.handle_nulls(df.copy(), ["num"], "Llenar con máximo")
    assert df_max.loc[2, "num"] == 50.0

    # Min
    df_min, _ = cleaner.handle_nulls(df.copy(), ["num"], "Llenar con mínimo")
    assert df_min.loc[2, "num"] == 10.0

    # Zero
    df_zero, _ = cleaner.handle_nulls(df.copy(), ["num"], "Llenar con cero")
    assert df_zero.loc[2, "num"] == 0.0

    # Mode
    df_mode, _ = cleaner.handle_nulls(df.copy(), ["cat"], "Llenar con moda (Categórica)")
    assert df_mode.loc[2, "cat"] == "b"

    # Invalid strategy
    df_inv, count_inv = cleaner.handle_nulls(df.copy(), ["num"], "Invalida")
    assert count_inv == 0


def test_data_cleaner_none_df():
    df_clean, count = DataCleaner.handle_nulls(None, ["a"], "Eliminar filas")
    assert df_clean is None
    assert count == 0


# --- DataScaler & Scaling Strategies ---
def test_data_scaler_zscore_and_constant():
    scaler = DataScaler()
    df = pd.DataFrame({"constant": [5.0, 5.0, 5.0], "var": [10.0, 20.0, 30.0]})

    # Constant column min-max
    df_minmax = scaler.apply_scaling(df, ["constant"], "Min-Max")
    assert (df_minmax["constant"] == 0).all()

    # Z-Score
    df_zscore = scaler.apply_scaling(df, ["var"], "Z-Score")
    assert abs(df_zscore["var"].mean()) < 1e-5

    # Constant Z-score
    df_zconst = scaler.apply_scaling(df, ["constant"], "Z-Score")
    assert (df_zconst["constant"] == 0).all()

    # Invalid method
    df_inv = scaler.apply_scaling(df, ["var"], "Invalid")
    assert (df_inv["var"] == df["var"]).all()


# --- OutlierManager Edge Cases ---
def test_outlier_manager_capping_and_invalid_col():
    df = pd.DataFrame({"A": [1.0, 2.0, 3.0, 4.0, 100.0]})

    # Capping
    df_cap, count, msg = OutlierManager.detect_and_treat(df, "A", "Capping (Winsorización)")
    assert count == 1
    assert "Winsorizados" in msg
    assert df_cap["A"].max() < 100.0

    # Non-existent column
    _, count_err, msg_err = OutlierManager.detect_and_treat(df, "NonExistent", "Informar")
    assert count_err == 0
    assert "Error" in msg_err


# --- Clusterer Edge Cases ---
def test_clusterer_insufficient_data():
    df = pd.DataFrame({"X": [1.0], "Y": [1.0]})
    _, msg = Clusterer.kmeans(df, ["X", "Y"], k=3)
    assert "Error" in msg


# --- FileSystemAdapter Tests ---
def test_file_system_adapter_excel_and_errors():
    adapter = FileSystemAdapter()
    assert adapter.load_file(None)[0] is None

    # CSV single column error
    csv_bytes = io.BytesIO(b"col1\nval1\nval2\n")
    csv_bytes.name = "single.csv"
    _, err = adapter.load_file(csv_bytes, delimiter=",")
    assert " Error: CSV de una sola columna" in err or "Error: CSV de una sola columna" in err

    # Export formats
    df = pd.DataFrame({"a": [1, 2]})
    file_path, err = adapter.export_file(df, "CSV")
    assert "datos_procesados.csv" in file_path

    file_path_xlsx, err_xlsx = adapter.export_file(df, "Excel")
    assert "datos_procesados.xlsx" in file_path_xlsx

    _, err_inv = adapter.export_file(df, "Invalid")
    assert err_inv == "Formato desconocido."


# --- PlottingAdapter Tests ---
def test_plotting_adapter_all_charts():
    df = pd.DataFrame({"a": [1, 2, 3, 4], "b": [10, 20, 30, 40], "Cluster": [0, 1, 0, 1]})

    assert PlottingAdapter.plot_correlation_heatmap(None) is None
    assert PlottingAdapter.plot_correlation_heatmap(pd.DataFrame()) is None
    assert PlottingAdapter.plot_correlation_heatmap(df) is not None

    assert PlottingAdapter.plot_distribution(df, "a") is not None
    assert PlottingAdapter.plot_distribution(df, "nonexistent") is None

    assert PlottingAdapter.plot_regression(df, "a", "b") is not None
    assert PlottingAdapter.plot_regression(df, "a", "nonexistent") is None

    assert PlottingAdapter.plot_clusters(df, "a", "b") is not None
    assert PlottingAdapter.plot_clusters(df, "a", "nonexistent") is None
