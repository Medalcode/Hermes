import pandas as pd
import pytest

from src.adapters.fs.file_io import FileSystemAdapter
from src.adapters.visualization.plotter import PlottingAdapter
from src.core.agents.base import AgentManager
from src.core.agents.skills.io_skills import set_file_io_provider
from src.core.agents.skills.visualization_skills import set_plotter_provider
from src.core.models import AnalysisSession


@pytest.fixture(autouse=True)
def setup_providers():
    set_file_io_provider(FileSystemAdapter())
    set_plotter_provider(PlottingAdapter())


@pytest.fixture
def agent_mgr():
    return AgentManager()


@pytest.fixture
def sample_session():
    df = pd.DataFrame(
        {
            "num1": [10.0, 20.0, 30.0, 40.0, 100.0],
            "num2": [1.0, 2.0, 3.0, 4.0, 5.0],
            "cat1": ["red", "blue", "red", "blue", "green"],
        }
    )
    session = AnalysisSession()
    session.current_df = df
    return session


# --- Transform Skills Tests ---
def test_scale_columns_zscore(agent_mgr, sample_session):
    result = agent_mgr.execute_skill(
        "scale_columns", sample_session, columns=["num1"], method="Z-Score"
    )
    assert result.preview is not None
    assert "error" not in result.changes
    # Z-Score mean should be ~0
    scaled = sample_session.current_df["num1"]
    assert abs(scaled.mean()) < 1e-5


def test_scale_columns_no_data(agent_mgr):
    empty_session = AnalysisSession()
    result = agent_mgr.execute_skill(
        "scale_columns", empty_session, columns=["num1"], method="Min-Max"
    )
    assert result.changes.get("error") == "No hay datos en la sesión."


def test_encode_categoricals_onehot(agent_mgr, sample_session):
    result = agent_mgr.execute_skill(
        "encode_categoricals", sample_session, columns=["cat1"], method="one-hot"
    )
    assert "new_columns" in result.changes
    assert "cat1_red" in sample_session.current_df.columns


def test_encode_categoricals_label(agent_mgr, sample_session):
    result = agent_mgr.execute_skill(
        "encode_categoricals", sample_session, columns=["cat1"], method="label"
    )
    assert "new_columns" in result.changes
    assert pd.api.types.is_numeric_dtype(sample_session.current_df["cat1"])


def test_encode_categoricals_invalid_method(agent_mgr, sample_session):
    result = agent_mgr.execute_skill(
        "encode_categoricals", sample_session, columns=["cat1"], method="invalid"
    )
    assert "error" in result.changes


# --- Stats Skills Tests ---
def test_compute_stats_correlation(agent_mgr, sample_session):
    result = agent_mgr.execute_skill("compute_stats", sample_session, stat_type="correlation")
    assert "result" in result.changes
    assert "num1" in result.changes["result"]


def test_compute_stats_distribution_shape(agent_mgr, sample_session):
    result = agent_mgr.execute_skill(
        "compute_stats", sample_session, stat_type="distribution_shape"
    )
    assert "result" in result.changes
    assert "Curtosis (Normal = 0)" in result.changes["result"]


def test_compute_stats_invalid_type(agent_mgr, sample_session):
    result = agent_mgr.execute_skill("compute_stats", sample_session, stat_type="invalid_stat")
    assert "error" in result.changes


# --- Visualization Skills Tests ---
def test_plot_distribution(agent_mgr, sample_session):
    result = agent_mgr.execute_skill("plot", sample_session, type="distribution", col="num1")
    assert "figure_json" in result.changes


def test_plot_regression(agent_mgr, sample_session):
    result = agent_mgr.execute_skill("plot", sample_session, type="regression", x="num1", y="num2")
    assert "figure_json" in result.changes


def test_plot_cluster(agent_mgr, sample_session):
    sample_session.current_df["Cluster"] = [0, 0, 1, 1, 0]
    result = agent_mgr.execute_skill("plot", sample_session, type="cluster", x="num1", y="num2")
    assert "figure_json" in result.changes


def test_plot_invalid_type(agent_mgr, sample_session):
    result = agent_mgr.execute_skill("plot", sample_session, type="invalid_type")
    assert "error" in result.changes


# --- Clean Skills (Outliers) Tests ---
def test_handle_outliers_capping(agent_mgr, sample_session):
    result = agent_mgr.execute_skill(
        "handle_outliers", sample_session, column="num1", treatment="Capping (Winsorización)"
    )
    assert result.changes.get("count") >= 0
    assert "preview" in result.changes


def test_handle_outliers_no_data(agent_mgr):
    empty_session = AnalysisSession()
    result = agent_mgr.execute_skill(
        "handle_outliers", empty_session, column="num1", treatment="Informar"
    )
    assert result.changes.get("error") == "No hay datos en la sesión."
