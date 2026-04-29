"""
transform_skills.py — Super-Skill de Transformación
Skills: scale_columns, encode_categoricals
Delega en: DataScaler, pd.get_dummies / pd.factorize
"""

from src.core.agents.base import register_skill
from src.core.domain_services import DataScaler
from src.core.models import AnalysisSession


@register_skill("scale_columns", description="Escala columnas numéricas (Min-Max o Z-Score)")
def scale_columns(session: AnalysisSession, columns: list[str], method: str) -> dict:
    """
    Parámetros:
        columns: lista de columnas a escalar.
        method: "Min-Max" | "Z-Score"
    """
    if not session.has_data():
        return {"error": "No hay datos en la sesión."}

    df_new = DataScaler.apply_scaling(session.current_df, columns, method)
    session.current_df = df_new
    session.add_log(f"Skill: scale_columns → método='{method}', columnas={columns}")

    preview = df_new.head(10).fillna("").to_dict(orient="records") if df_new is not None else []
    return {"preview": preview}


@register_skill("encode_categoricals", description="Codifica columnas categóricas (one-hot o label encoding)")
def encode_categoricals(session: AnalysisSession, columns: list[str], method: str = "one-hot") -> dict:
    """
    Parámetros:
        columns: lista de columnas categóricas a codificar.
        method: "one-hot" (pd.get_dummies) | "label" (pd.factorize)

    Principio de reutilización: un solo skill con `method` como discriminador
    evita crear dos skills separadas (OneHotEncoderSkill, LabelEncoderSkill)
    que compartirían guardia de datos, log y preview.
    """
    if not session.has_data():
        return {"error": "No hay datos en la sesión."}

    df = session.current_df.copy()
    new_columns = []

    if method == "one-hot":
        df = __import__("pandas").get_dummies(df, columns=columns, drop_first=False)
        new_columns = [c for c in df.columns if any(c.startswith(col + "_") for col in columns)]
    elif method == "label":
        import pandas as pd
        for col in columns:
            if col in df.columns:
                df[col], _ = pd.factorize(df[col])
                new_columns.append(col)
    else:
        return {"error": f"Método '{method}' no soportado. Use 'one-hot' o 'label'."}

    session.current_df = df
    session.add_log(f"Skill: encode_categoricals → método='{method}', columnas={columns}")

    preview = df.head(10).fillna("").to_dict(orient="records")
    return {"preview": preview, "new_columns": new_columns}
