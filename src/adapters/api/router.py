import io
import json
from typing import Optional

import pandas as pd
from fastapi import Depends, FastAPI, File, Form, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.adapters.api.dataframe_json import dataframe_from_split_json, dataframe_to_split_json
from src.adapters.api.dependencies import (
    get_agent_manager,
    get_analysis_session,
    get_session_id,
    in_vercel_runtime,
    save_analysis_session,
    verify_api_key,
)
from starlette.datastructures import URL
from src.adapters.visualization.plotter import PlottingAdapter
from src.core.agents.base import AgentManager
from src.core.domain_services import StatisticalAnalyzer
from src.core.models import AnalysisSession

app = FastAPI(title="Myna API")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        try:
            await verify_api_key(request)
        except HTTPException:
            return JSONResponse(status_code=401, content={"error": "Invalid or missing API key"})
    return await call_next(request)


def _get_request_df(session: AnalysisSession, df_json: str | None):
    if in_vercel_runtime():
        if not df_json:
            return None, JSONResponse(status_code=400, content={"error": "Session dataframe payload is required"})
        try:
            return dataframe_from_split_json(df_json), None
        except ValueError:
            return None, JSONResponse(status_code=400, content={"error": "Invalid session dataframe payload"})
    if df_json:
        try:
            return dataframe_from_split_json(df_json), None
        except ValueError:
            return None, JSONResponse(status_code=400, content={"error": "Invalid session dataframe payload"})
    return session.current_df, None


def _build_df_response(df: pd.DataFrame):
    return {
        "df_json": dataframe_to_split_json(df),
        "columns": df.columns.tolist(),
        "numeric_columns": StatisticalAnalyzer.get_numeric_columns(df),
        "shape": list(df.shape),
    }


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
    df = session.current_df
    resp = {
        "message": "Carga exitosa",
        "columns": result.changes.get("columns", []),
        "numeric_columns": result.changes.get("numeric_columns", []),
        "preview": result.changes.get("preview", []),
        "shape": result.changes.get("shape", [0, 0]),
    }
    if df is not None:
        resp.update(_build_df_response(df))
    return resp


@app.post("/api/clean/nulls")
async def clean_nulls(
    cols: list[str] = Form(...),
    method: str = Form(...),
    df_json: str | None = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    current_df, error_response = _get_request_df(session, df_json)
    if error_response:
        return error_response
    if current_df is None:
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    session.current_df = current_df
    result = agent_manager.execute_skill("clean_nulls", session, columns=cols, method=method)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
    save_analysis_session(session_id, session)
    return {
        "message": f"Se trataron {result.changes.get('affected_count', 0)} valores.",
        "preview": result.changes.get("preview", []),
        **_build_df_response(session.current_df),
    }


@app.post("/api/clean/scale")
async def scale_data(
    cols: list[str] = Form(...),
    method: str = Form(...),
    df_json: str | None = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    current_df, error_response = _get_request_df(session, df_json)
    if error_response:
        return error_response
    if current_df is None:
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    session.current_df = current_df
    result = agent_manager.execute_skill("scale_columns", session, columns=cols, method=method)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
    save_analysis_session(session_id, session)
    return {
        "message": "Escalado completado.",
        "preview": result.changes.get("preview", []),
        **_build_df_response(session.current_df),
    }


@app.post("/api/clean/dedup")
async def drop_duplicates(
    subset: str | None = Form(None),
    df_json: str | None = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    current_df, error_response = _get_request_df(session, df_json)
    if error_response:
        return error_response
    if current_df is None:
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    session.current_df = current_df
    cols = [c.strip() for c in subset.split(",")] if subset else None
    result = agent_manager.execute_skill("drop_duplicates", session, subset=cols)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
    save_analysis_session(session_id, session)
    return {
        "message": f"Se eliminaron {result.changes.get('affected_count', 0)} duplicados.",
        "preview": result.changes.get("preview", []),
        **_build_df_response(session.current_df),
    }


@app.post("/api/outliers")
async def handle_outliers(
    column: str = Form(...),
    treatment: str = Form(...),
    df_json: str | None = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
):
    current_df, error_response = _get_request_df(session, df_json)
    if error_response:
        return error_response
    if current_df is None:
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    from src.core.domain_services import OutlierManager
    df_new, count, detail = OutlierManager.detect_and_treat(current_df, column, treatment)
    session.current_df = df_new
    session.add_log(f"API: Outliers treated on '{column}' with {treatment}")
    save_analysis_session(session_id, session)
    return {
        "message": f"{count} outliers: {detail}",
        "count": int(count),
        "preview": df_new.head(10).fillna("").to_dict(orient="records"),
        **_build_df_response(df_new),
    }


@app.get("/api/stats")
async def get_stats(
    response: Response,
    session: AnalysisSession = Depends(get_analysis_session),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    if in_vercel_runtime():
        return JSONResponse(status_code=400, content={"error": "Use POST /api/stats in Vercel mode"})
    if not session.has_data():
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Wed, 31 Dec 2026 23:59:59 GMT"
    response.headers["Link"] = '</api/stats>; rel="successor-version"'
    desc_result = agent_manager.execute_skill("compute_stats", session, stat_type="descriptive")
    corr_result = agent_manager.execute_skill("compute_stats", session, stat_type="correlation")
    return {
        "descriptive": desc_result.changes.get("result", {}),
        "correlation": corr_result.changes.get("result", {}),
    }


@app.post("/api/stats")
async def post_stats(
    df_json: str | None = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    current_df, error_response = _get_request_df(session, df_json)
    if error_response:
        return error_response
    if current_df is None:
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    session.current_df = current_df
    desc_result = agent_manager.execute_skill("compute_stats", session, stat_type="descriptive")
    corr_result = agent_manager.execute_skill("compute_stats", session, stat_type="correlation")
    return {
        "descriptive": desc_result.changes.get("result", {}),
        "correlation": corr_result.changes.get("result", {}),
        **_build_df_response(session.current_df),
    }


@app.post("/api/cluster")
async def run_cluster(
    cols: list[str] = Form(...),
    k: int = Form(...),
    df_json: str | None = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    current_df, error_response = _get_request_df(session, df_json)
    if error_response:
        return error_response
    if current_df is None:
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    session.current_df = current_df
    result = agent_manager.execute_skill("kmeans_cluster", session, columns=cols, k=k)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
    save_analysis_session(session_id, session)
    return {
        "message": result.changes.get("message", "Clustering completado."),
        "preview": result.changes.get("preview", []),
        **_build_df_response(session.current_df),
    }


@app.post("/api/plot")
async def get_plot(
    type: str = Form(...),
    x: str = Form(None),
    y: str = Form(None),
    col: str = Form(None),
    df_json: str | None = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
):
    current_df, error_response = _get_request_df(session, df_json)
    if error_response:
        return error_response
    if current_df is None:
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    fig = None
    if type == "correlation":
        fig = PlottingAdapter.plot_correlation_heatmap(current_df)
    elif type == "distribution":
        fig = PlottingAdapter.plot_distribution(current_df, col)
    elif type == "regression":
        fig = PlottingAdapter.plot_regression(current_df, x, y)
    elif type == "cluster":
        fig = PlottingAdapter.plot_clusters(current_df, x, y)
    if fig:
        return json.loads(fig.to_json())
    return {"error": "Could not generate plot"}


@app.post("/api/export")
async def export_data(
    format_type: str = Form("CSV"),
    df_json: str | None = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    current_df, error_response = _get_request_df(session, df_json)
    if error_response:
        return error_response
    if current_df is None:
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    session.current_df = current_df
    result = agent_manager.execute_skill("export_file", session, format_type=format_type)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
    return {"file_path": result.changes.get("file_path", "")}

@app.post("/api/auto-analyze")
async def auto_analyze_endpoint(
    df_json: Optional[str] = Form(None),
    target_col: Optional[str] = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    current_df, error_response = _get_request_df(session, df_json)
    if error_response:
        return error_response
    if current_df is None:
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    session.current_df = current_df
    
    result = agent_manager.execute_skill("auto_analyze", session, target_col=target_col)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
        
    save_analysis_session(session_id, session)
    return {
        "report": result.changes.get("result", {}),
        **_build_df_response(session.current_df),
    }
