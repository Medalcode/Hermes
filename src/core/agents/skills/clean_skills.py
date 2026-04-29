"""
clean_skills.py — Super-Skill de Limpieza
Skills: clean_nulls, drop_duplicates
Delega en: DataCleaner, pd.DataFrame nativo

NOTA: El archivo legacy `clean_nulls.py` en este mismo directorio
es HUÉRFANO y puede eliminarse. Su lógica está consolidada aquí.
"""

from src.core.agents.base import register_skill
from src.core.domain_services import DataCleaner
from src.core.models import AnalysisSession


@register_skill("clean_nulls", description="Trata valores nulos en columnas específicas usando el método indicado")
def clean_nulls(session: AnalysisSession, columns: list[str], method: str) -> dict:
    if not session.has_data():
        return {"error": "No hay datos en la sesión."}

    df_new, affected = DataCleaner.handle_nulls(session.current_df, columns, method)
    session.current_df = df_new
    session.add_log(f"Skill: clean_nulls → método='{method}', columnas={columns}, afectados={affected}")

    preview = df_new.head(10).fillna("").to_dict(orient="records") if df_new is not None else []
    return {"preview": preview, "affected_count": affected}


@register_skill("drop_duplicates", description="Elimina filas duplicadas del DataFrame de la sesión")
def drop_duplicates(session: AnalysisSession, subset: list[str] | None = None) -> dict:
    if not session.has_data():
        return {"error": "No hay datos en la sesión."}

    df = session.current_df
    initial_rows = len(df)
    df_clean = df.drop_duplicates(subset=subset)
    affected = initial_rows - len(df_clean)

    session.current_df = df_clean
    session.add_log(f"Skill: drop_duplicates → subset={subset}, eliminadas={affected} filas")

    preview = df_clean.head(10).fillna("").to_dict(orient="records")
    return {"preview": preview, "affected_count": affected}
