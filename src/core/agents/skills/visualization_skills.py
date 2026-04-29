"""
visualization_skills.py — Super-Skill de Visualización
Skills: plot (fusión paramétrica de plot_distribution + plot_correlation + plot_regression + plot_clusters)
Delega en: PlottingAdapter

FUSIÓN JUSTIFICADA:
    Las 4 funciones de plotting comparten:
    - Guardia session.has_data()
    - Llamada a PlottingAdapter.*
    - Serialización fig.to_json()
    - Log de sesión
    Se unifican con el parámetro `type` (mismo patrón que el endpoint /api/plot).
"""
import json

from src.adapters.visualization.plotter import PlottingAdapter
from src.core.agents.base import register_skill
from src.core.models import AnalysisSession

_VALID_PLOT_TYPES = {"distribution", "correlation", "regression", "cluster"}


@register_skill(
    "plot",
    description=(
        "Genera una visualización interactiva. "
        "type: 'distribution' | 'correlation' | 'regression' | 'cluster'"
    ),
)
def plot(
    session: AnalysisSession,
    type: str,
    col: str | None = None,
    x: str | None = None,
    y: str | None = None,
) -> dict:
    """
    Super-Skill paramétrica de visualización.
    Parámetros:
        type:  tipo de gráfico (discriminador)
        col:   columna para distribución
        x, y:  columnas para regresión o clusters
    """
    if not session.has_data():
        return {"error": "No hay datos en la sesión."}

    if type not in _VALID_PLOT_TYPES:
        return {"error": f"Tipo '{type}' no válido. Use: {_VALID_PLOT_TYPES}"}

    df = session.current_df
    fig = None

    if type == "correlation":
        fig = PlottingAdapter.plot_correlation_heatmap(df)
    elif type == "distribution":
        fig = PlottingAdapter.plot_distribution(df, col)
    elif type == "regression":
        fig = PlottingAdapter.plot_regression(df, x, y)
    elif type == "cluster":
        fig = PlottingAdapter.plot_clusters(df, x, y)

    if fig is None:
        return {"error": f"No se pudo generar el gráfico de tipo '{type}'. Verifica columnas y datos."}

    session.add_log(f"Skill: plot → type='{type}', col={col}, x={x}, y={y}")
    return {"figure_json": json.loads(fig.to_json())}
