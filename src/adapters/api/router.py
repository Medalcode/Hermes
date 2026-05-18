from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import io
import json
from typing import List, Optional

from src.core.models import AnalysisSession
from src.adapters.visualization.plotter import PlottingAdapter
from src.adapters.api.dependencies import (
    get_analysis_session,
    save_analysis_session,
    get_session_id,
    get_agent_manager,
)
from src.core.agents.base import AgentManager

app = FastAPI(title="Myna API")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Myna API is running"}


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    delimiter: str = Form(","),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    contents = await file.read()
    file_obj = io.BytesIO(contents)
    file_obj.name = file.filename
    result = agent_manager.execute_skill("load_file", session, file_obj=file_obj, delimiter=delimiter)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
    save_analysis_session(session_id, session)
    return {
        "message": "Carga exitosa",
        "columns": result.changes.get("columns", []),
        "numeric_columns": result.changes.get("numeric_columns", []),
        "preview": result.changes.get("preview", []),
        "shape": result.changes.get("shape", [0, 0]),
    }


@app.post("/api/clean/nulls")
async def clean_nulls(
    cols: List[str] = Form(...),
    method: str = Form(...),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    if not session.has_data():
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    result = agent_manager.execute_skill("clean_nulls", session, columns=cols, method=method)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
    save_analysis_session(session_id, session)
    return {"message": f"Se trataron {result.changes.get('affected_count', 0)} valores.", "preview": result.changes.get("preview", [])}


@app.post("/api/clean/scale")
async def scale_data(
    cols: List[str] = Form(...),
    method: str = Form(...),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    if not session.has_data():
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    result = agent_manager.execute_skill("scale_columns", session, columns=cols, method=method)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
    save_analysis_session(session_id, session)
    return {"message": "Escalado completado.", "preview": result.changes.get("preview", [])}


@app.post("/api/clean/dedup")
async def drop_duplicates(
    subset: Optional[str] = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    if not session.has_data():
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    cols = [c.strip() for c in subset.split(",")] if subset else None
    result = agent_manager.execute_skill("drop_duplicates", session, subset=cols)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
    save_analysis_session(session_id, session)
    return {"message": f"Se eliminaron {result.changes.get('affected_count', 0)} duplicados.", "preview": result.changes.get("preview", [])}


@app.post("/api/outliers")
async def handle_outliers(
    column: str = Form(...),
    treatment: str = Form(...),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
):
    if not session.has_data():
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    from src.core.domain_services import OutlierManager
    df_new, count, detail = OutlierManager.detect_and_treat(session.current_df, column, treatment)
    session.current_df = df_new
    session.add_log(f"API: Outliers treated on '{column}' with {treatment}")
    save_analysis_session(session_id, session)
    return {
        "message": f"{count} outliers: {detail}",
        "count": int(count),
        "preview": df_new.head(10).fillna("").to_dict(orient="records"),
    }


@app.get("/api/stats")
async def get_stats(
    session: AnalysisSession = Depends(get_analysis_session),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    if not session.has_data():
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    desc_result = agent_manager.execute_skill("compute_stats", session, stat_type="descriptive")
    corr_result = agent_manager.execute_skill("compute_stats", session, stat_type="correlation")
    return {
        "descriptive": desc_result.changes.get("result", {}),
        "correlation": corr_result.changes.get("result", {}),
    }


@app.post("/api/cluster")
async def run_cluster(
    cols: List[str] = Form(...),
    k: int = Form(...),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    if not session.has_data():
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    result = agent_manager.execute_skill("kmeans_cluster", session, columns=cols, k=k)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
    save_analysis_session(session_id, session)
    return {"message": result.changes.get("message", "Clustering completado."), "preview": result.changes.get("preview", [])}


@app.post("/api/plot")
async def get_plot(
    type: str = Form(...),
    x: str = Form(None),
    y: str = Form(None),
    col: str = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
):
    if not session.has_data():
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    fig = None
    if type == "correlation":
        fig = PlottingAdapter.plot_correlation_heatmap(session.current_df)
    elif type == "distribution":
        fig = PlottingAdapter.plot_distribution(session.current_df, col)
    elif type == "regression":
        fig = PlottingAdapter.plot_regression(session.current_df, x, y)
    elif type == "cluster":
        fig = PlottingAdapter.plot_clusters(session.current_df, x, y)
    if fig:
        return json.loads(fig.to_json())
    return {"error": "Could not generate plot"}


@app.post("/api/export")
async def export_data(
    format_type: str = Form("CSV"),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    if not session.has_data():
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    result = agent_manager.execute_skill("export_file", session, format_type=format_type)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
    return {"file_path": result.changes.get("file_path", "")}
