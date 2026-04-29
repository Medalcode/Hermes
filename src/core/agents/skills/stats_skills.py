"""
stats_skills.py — Super-Skill de Estadísticas
Skills: compute_stats (fusión paramétrica de compute_descriptive + compute_correlation)
Delega en: StatisticalAnalyzer

FUSIÓN JUSTIFICADA:
    compute_descriptive y compute_correlation del catálogo anterior comparten:
    - Guardia de datos (session.has_data())
    - Instanciación de StatisticalAnalyzer
    - Log de la sesión
    - Retorno de dict
    Se unifican con el parámetro stat_type.
"""
from src.core.agents.base import register_skill
from src.core.domain_services import StatisticalAnalyzer
from src.core.models import AnalysisSession

_VALID_STAT_TYPES = {"descriptive", "correlation", "distribution_shape"}


@register_skill(
    "compute_stats",
    description=(
        "Calcula estadísticas sobre el DataFrame. "
        "stat_type: 'descriptive' | 'correlation' | 'distribution_shape'"
    ),
)
def compute_stats(session: AnalysisSession, stat_type: str) -> dict:
    """
    Super-Skill paramétrica.
    Parámetros:
        stat_type:
            "descriptive"        → describe() extendido con mediana
            "correlation"        → matriz de correlación de Pearson
            "distribution_shape" → Skewness y Kurtosis por columna

    Principio de reutilización: antes de crear compute_correlation como skill
    separada, se verificó que su lógica es idéntica a compute_descriptive
    salvo el método de StatisticalAnalyzer invocado.
    """
    if not session.has_data():
        return {"error": "No hay datos en la sesión."}

    if stat_type not in _VALID_STAT_TYPES:
        return {"error": f"stat_type '{stat_type}' no válido. Use: {_VALID_STAT_TYPES}"}

    analyzer = StatisticalAnalyzer()

    if stat_type == "descriptive":
        result_df = analyzer.calculate_descriptive_stats(session.current_df)
        output = result_df.to_dict() if not result_df.empty else {}
    elif stat_type == "correlation":
        result_df = analyzer.calculate_correlation_matrix(session.current_df)
        output = result_df.to_dict() if not result_df.empty else {}
    elif stat_type == "distribution_shape":
        result_df = analyzer.calculate_distribution_shape(session.current_df)
        output = result_df.to_dict() if not result_df.empty else {}
    else:
        output = {}

    session.add_log(f"Skill: compute_stats → stat_type='{stat_type}'")
    return {"result": output, "stat_type": stat_type}
