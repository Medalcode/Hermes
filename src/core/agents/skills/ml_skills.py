"""
ml_skills.py — Super-Skill de Machine Learning
Skills: kmeans_cluster
Delega en: Clusterer.kmeans()
"""
from typing import List
from src.core.agents.base import register_skill, SkillResult
from src.core.models import AnalysisSession
from src.core.domain_services import Clusterer


@register_skill("kmeans_cluster", description="Aplica clustering K-Means al DataFrame de la sesión")
def kmeans_cluster(session: AnalysisSession, columns: List[str], k: int = 3) -> dict:
    if not session.has_data():
        return {"error": "No hay datos en la sesión."}

    df_new, message = Clusterer.kmeans(session.current_df, columns, k)
    session.current_df = df_new
    session.add_log(f"Skill: kmeans_cluster → k={k}, columnas={columns}, resultado='{message}'")

    preview = df_new.head(10).fillna("").to_dict(orient="records") if df_new is not None else []
    return {"preview": preview, "message": message}
