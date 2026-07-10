import numpy as np
import pandas as pd
import pytest

from src.core.agents.skills.auto_analyze_skills import (
    auto_analyze,
    detect_issues,
    generate_business_insights,
    profile_dataset,
    recommend_models,
    recommend_transformations,
)
from src.core.models import AnalysisSession


@pytest.fixture
def sample_session():
    # Create a dummy dataframe with some obvious issues
    df = pd.DataFrame({
        'id': range(100),  # High cardinality
        'age': [25, 30, np.nan, 40, 50] * 20,  # Has nulls
        'constant_col': ['A'] * 100,  # Constant
        'target': ['Yes', 'No'] * 50,  # Classification target
        'salary': [50000, 60000, 55000, 5000000, 52000] * 20 # One outlier/high variance
    })
    session = AnalysisSession()
    session.current_df = df
    return session

def test_profile_dataset(sample_session):
    result = profile_dataset(sample_session)
    metrics = result.get("result")
    assert metrics is not None
    assert metrics["rows"] == 100
    assert metrics["columns"] == 5
    assert "constant_col" in metrics["columns_info"]

def test_detect_issues(sample_session):
    result = detect_issues(sample_session)
    issues = result.get("result")
    assert any("constante" in issue["issue"].lower() for issue in issues)
    assert any("nulos" in issue["issue"].lower() for issue in issues)

def test_recommend_transformations(sample_session):
    result = recommend_transformations(sample_session)
    recs = result.get("result")
    # Should recommend dropping constant_col
    assert any(rec["column"] == "constant_col" and "Eliminar" in rec["recommendation"] for rec in recs)
    # Should recommend imputing age
    assert any(rec["column"] == "age" and "Imputar" in rec["recommendation"] for rec in recs)

def test_recommend_models(sample_session):
    result = recommend_models(sample_session, target_col="target")
    recs = result.get("result")
    # Target has 2 classes -> Classification
    assert any("Clasificación" in rec["task"] for rec in recs)

def test_generate_business_insights(sample_session):
    result = generate_business_insights(sample_session)
    insights = result.get("result")
    assert len(insights) > 0
    # Should detect high variance in salary due to 500000 outlier
    assert any("salary" in insight.lower() and "variabilidad" in insight.lower() for insight in insights)

def test_auto_analyze(sample_session):
    result = auto_analyze(sample_session, target_col="target")
    report = result.get("result")

    assert "diagnostico_dataset" in report
    assert "problemas_detectados" in report
    assert "transformaciones_recomendadas" in report
    assert "modelos_sugeridos" in report
    assert "conclusiones_negocio" in report
    assert len(report["problemas_detectados"]) > 0
