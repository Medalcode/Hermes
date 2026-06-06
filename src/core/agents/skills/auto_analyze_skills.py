import pandas as pd
import numpy as np
from typing import Dict, Any

from src.core.agents.base import register_skill, SkillResult
from src.core.models import AnalysisSession

@register_skill(
    "profile_dataset",
    description="Calcula métricas estadísticas generales, tipos de datos, distribución de nulos y cardinalidad del dataset."
)
def profile_dataset(session: AnalysisSession) -> dict:
    if not session.has_data():
        return {"error": "No hay datos en la sesión."}

    df = session.current_df
    
    rows = len(df)
    cols = len(df.columns)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
    
    memory_usage = df.memory_usage(deep=True).sum() / (1024 * 1024) # en MB
    
    metrics = {
        "rows": rows,
        "columns": cols,
        "numeric_columns": len(numeric_cols),
        "categorical_columns": len(categorical_cols),
        "datetime_columns": len(datetime_cols),
        "memory_usage_mb": round(memory_usage, 2),
        "columns_info": {}
    }
    
    for col in df.columns:
        col_type = str(df[col].dtype)
        null_count = df[col].isnull().sum()
        null_percent = round((null_count / rows) * 100, 2) if rows > 0 else 0
        n_unique = df[col].nunique()
        
        info = {
            "type": col_type,
            "nulls": int(null_count),
            "null_percent": float(null_percent),
            "unique": int(n_unique)
        }
        
        if col in numeric_cols:
            info["mean"] = float(df[col].mean()) if not df[col].isnull().all() else None
            info["std"] = float(df[col].std()) if not df[col].isnull().all() else None
            info["min"] = float(df[col].min()) if not df[col].isnull().all() else None
            info["max"] = float(df[col].max()) if not df[col].isnull().all() else None
            info["skewness"] = float(df[col].skew()) if not df[col].isnull().all() else None
            
        metrics["columns_info"][col] = info
        
    session.add_log("Skill: profile_dataset ejecutada.")
    return {"result": metrics}

@register_skill(
    "detect_issues",
    description="Evalúa la calidad de los datos y detecta problemas como nulos, alta correlación y desbalanceo."
)
def detect_issues(session: AnalysisSession) -> dict:
    if not session.has_data():
        return {"error": "No hay datos en la sesión."}

    df = session.current_df
    issues = []
    
    rows = len(df)
    if rows == 0:
        return {"result": [{"severity": "high", "issue": "Dataset vacío"}]}
        
    # Check nulls and constants
    for col in df.columns:
        null_percent = df[col].isnull().sum() / rows
        if null_percent > 0.5:
            issues.append({"severity": "high", "column": col, "issue": f"Más del 50% de valores nulos ({null_percent*100:.1f}%)"})
        elif null_percent > 0.1:
            issues.append({"severity": "medium", "column": col, "issue": f"Valores nulos presentes ({null_percent*100:.1f}%)"})
            
        if df[col].nunique() == 1:
            issues.append({"severity": "high", "column": col, "issue": "Columna constante (1 solo valor único)"})
            
    # Check high correlation (only numeric)
    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty and len(numeric_df.columns) > 1:
        corr_matrix = numeric_df.corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        high_corr = [column for column in upper.columns if any(upper[column] > 0.85)]
        for col in high_corr:
            issues.append({"severity": "medium", "column": col, "issue": "Alta correlación detectada (>0.85) con otra variable"})
            
    # Check categorical high cardinality
    cat_cols = df.select_dtypes(include=['object', 'category', 'string']).columns
    for col in cat_cols:
        unique_ratio = df[col].nunique() / rows
        if unique_ratio > 0.8 and rows > 100:
            issues.append({"severity": "low", "column": col, "issue": "Alta cardinalidad en variable categórica (posible ID)"})

    session.add_log("Skill: detect_issues ejecutada.")
    return {"result": issues}

@register_skill(
    "recommend_transformations",
    description="Sugiere transformaciones basadas en el profiling y los issues detectados."
)
def recommend_transformations(session: AnalysisSession, profile: dict = None, issues: list = None) -> dict:
    if not session.has_data():
        return {"error": "No hay datos en la sesión."}
        
    # Si no se pasan, los ejecutamos temporalmente (o leemos de sesión en un futuro)
    if not profile or not issues:
        profile_res = profile_dataset(session)
        issues_res = detect_issues(session)
        profile = profile_res.get("result", {})
        issues = issues_res.get("result", [])

    recommendations = []
    
    for issue in issues:
        col = issue.get("column")
        if "nulos" in issue.get("issue").lower():
            col_info = profile.get("columns_info", {}).get(col, {})
            if col_info.get("type") in ["object", "category"]:
                recommendations.append({"column": col, "recommendation": "Imputar con la moda o añadir categoría 'Desconocido'", "reason": issue["issue"]})
            else:
                recommendations.append({"column": col, "recommendation": "Imputar con la mediana", "reason": issue["issue"]})
        if "constante" in issue.get("issue").lower():
            recommendations.append({"column": col, "recommendation": "Eliminar columna", "reason": "No aporta varianza al modelo"})
        if "alta correlación" in issue.get("issue").lower():
            recommendations.append({"column": col, "recommendation": "Eliminar variable colineal o aplicar PCA", "reason": "Evitar multicolinealidad"})

    # Checks from profile
    cols_info = profile.get("columns_info", {})
    for col, info in cols_info.items():
        if info.get("skewness") and abs(info.get("skewness")) > 2:
             recommendations.append({"column": col, "recommendation": "Aplicar transformación logarítmica", "reason": f"Alta asimetría detectada (Skewness = {info.get('skewness'):.2f})"})
             
    session.add_log("Skill: recommend_transformations ejecutada.")
    return {"result": recommendations}

@register_skill(
    "recommend_models",
    description="Sugiere algoritmos según las características del dataset y el objetivo (heurístico)."
)
def recommend_models(session: AnalysisSession, target_col: str = None) -> dict:
    if not session.has_data():
        return {"error": "No hay datos en la sesión."}
        
    df = session.current_df
    rows = len(df)
    
    if target_col and target_col not in df.columns:
        return {"error": f"Columna objetivo '{target_col}' no encontrada en el dataset."}
        
    recommendations = []
    
    if not target_col:
        # Clustering
        recommendations.append({"task": "Segmentación / Clustering", "models": ["K-Means", "DBSCAN", "Hierarchical Clustering"], "reason": "No se especificó variable objetivo."})
    else:
        # Clasificación vs Regresión
        target_type = str(df[target_col].dtype)
        unique_target = df[target_col].nunique()
        
        is_classification = target_type in ['object', 'category', 'bool'] or unique_target < 20
        
        if is_classification:
            recommendations.append({"task": "Clasificación", "models": ["Random Forest Classifier", "XGBoost Classifier", "Logistic Regression", "LightGBM"], "reason": f"Variable objetivo '{target_col}' detectada como categórica ({unique_target} clases)."})
        else:
            recommendations.append({"task": "Regresión", "models": ["Random Forest Regressor", "XGBoost Regressor", "Linear Regression", "LightGBM"], "reason": f"Variable objetivo '{target_col}' detectada como continua."})
            
    session.add_log("Skill: recommend_models ejecutada.")
    return {"result": recommendations}

@register_skill(
    "generate_business_insights",
    description="Genera conclusiones de negocio basadas en los datos usando reglas estadísticas."
)
def generate_business_insights(session: AnalysisSession) -> dict:
    if not session.has_data():
        return {"error": "No hay datos en la sesión."}
        
    df = session.current_df
    insights = []
    
    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        # Detectar columnas con mucha varianza (coeficiente de variación)
        for col in numeric_df.columns:
            mean = numeric_df[col].mean()
            if mean != 0:
                cv = numeric_df[col].std() / mean
                if abs(cv) > 1.5:
                    insights.append(f"La variable '{col}' muestra una variabilidad extrema respecto a su media (Coeficiente de variación alto). Se sugiere investigar la causa de estos picos o caídas abruptas.")
                    
        # Correlaciones extremas pero no totales
        if len(numeric_df.columns) > 1:
            corr_matrix = numeric_df.corr().abs()
            upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
            for col in upper.columns:
                for idx in upper.index:
                    val = upper.loc[idx, col]
                    if pd.notna(val) and 0.7 < val < 0.99:
                        insights.append(f"Existe una fuerte relación lineal ({val*100:.1f}%) entre '{col}' y '{idx}'. Esta relación puede ser clave para la toma de decisiones predictivas.")

    session.add_log("Skill: generate_business_insights ejecutada.")
    return {"result": insights if insights else ["No se detectaron insights heurísticos obvios en esta muestra."]}

@register_skill(
    "auto_analyze",
    description="Pipeline completo de análisis: profile, issues, transformaciones, modelos e insights."
)
def auto_analyze(session: AnalysisSession, target_col: str = None) -> dict:
    if not session.has_data():
        return {"error": "No hay datos en la sesión."}

    profile = profile_dataset(session).get("result", {})
    issues = detect_issues(session).get("result", [])
    transformations = recommend_transformations(session, profile=profile, issues=issues).get("result", [])
    models = recommend_models(session, target_col=target_col).get("result", [])
    insights = generate_business_insights(session).get("result", [])
    
    report = {
        "diagnostico_dataset": profile,
        "problemas_detectados": issues,
        "transformaciones_recomendadas": transformations,
        "modelos_sugeridos": models,
        "conclusiones_negocio": insights
    }
    
    session.add_log("Skill: auto_analyze completó el pipeline de Análisis Inteligente.")
    return {"result": report}
