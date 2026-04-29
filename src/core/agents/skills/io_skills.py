"""
io_skills.py — Super-Skill de I/O
Skills: load_file, export_file
Delega en: FileSystemAdapter
"""
from src.adapters.fs.file_io import FileSystemAdapter
from src.core.agents.base import register_skill
from src.core.domain_services import StatisticalAnalyzer
from src.core.models import AnalysisSession


@register_skill("load_file", description="Carga un archivo (CSV/Excel) en la sesión actual")
def load_file(session: AnalysisSession, file_obj, delimiter: str = ",") -> dict:
    df, error = FileSystemAdapter.load_file(file_obj, delimiter)

    if error:
        return {"error": error}

    session.current_df = df
    session.add_log(f"Skill: load_file cargó archivo con {df.shape[0]} filas y {df.shape[1]} columnas")

    return {
        "columns": df.columns.tolist(),
        "numeric_columns": StatisticalAnalyzer.get_numeric_columns(df),
        "preview": df.head(10).fillna("").to_dict(orient="records"),
        "shape": list(df.shape),
    }


@register_skill("export_file", description="Exporta el DataFrame de la sesión a CSV o Excel")
def export_file(session: AnalysisSession, format_type: str = "CSV") -> dict:
    if not session.has_data():
        return {"error": "No hay datos en la sesión para exportar."}

    file_path, error = FileSystemAdapter.export_file(session.current_df, format_type)

    if error:
        return {"error": error}

    session.add_log(f"Skill: export_file exportó a {format_type} → {file_path}")
    return {"file_path": file_path}
