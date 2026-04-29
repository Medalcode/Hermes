"""
ml_skills.py — Super-Skill de Machine Learning
Skills: kmeans_cluster
Delega en: Clusterer.kmeans()
"""

from src.core.agents.base import register_skill
from src.core.domain_services import Clusterer
from src.core.models import AnalysisSession


@register_skill("kmeans_cluster", description="Aplica clustering K-Means al DataFrame de la sesión")
def kmeans_cluster(session: AnalysisSession, columns: list[str], k: int = 3) -> dict:
    if not session.has_data():
        return {"error": "No hay datos en la sesión."}

    df_new, message = Clusterer.kmeans(session.current_df, columns, k)
    session.current_df = df_new
    session.add_log(f"Skill: kmeans_cluster → k={k}, columnas={columns}, resultado='{message}'")

    preview = df_new.head(10).fillna("").to_dict(orient="records") if df_new is not None else []
    return {"preview": preview, "message": message}
