import io
from typing import Any

import pandas as pd
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
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
from src.adapters.repositories.job_repository import get_job_repository
from src.core.agents.base import AgentManager
from src.core.domain_services import StatisticalAnalyzer
from src.core.models import AnalysisSession

app = FastAPI(title="Myna API")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/") and path not in ["/healthz", "/readyz"]:
        try:
            await verify_api_key(request)
        except HTTPException:
            return JSONResponse(status_code=401, content={"error": "Invalid or missing API key"})
    return await call_next(request)


@app.get("/healthz", summary="Liveness probe")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", summary="Readiness probe")
def readyz(agent_manager: AgentManager = Depends(get_agent_manager)) -> dict[str, Any]:
    skills = agent_manager.list_skills()
    if not skills:
        raise HTTPException(status_code=503, detail="AgentManager has no registered skills")
    return {"status": "ready", "registered_skills_count": len(skills)}


def _run_background_job(job_id: str, skill_id: str, session: AnalysisSession, **params) -> None:
    job_repo = get_job_repository()
    job_repo.update_status(job_id, "running")
    try:
        agent_manager = get_agent_manager()
        res = agent_manager.execute_skill(skill_id, session, **params)
        job_repo.update_status(job_id, "completed", result=res.changes)
    except Exception as e:
        job_repo.update_status(job_id, "failed", error=str(e))


@app.post("/api/jobs/execute", status_code=202, summary="Enqueue async skill execution")
async def execute_job_async(
    background_tasks: BackgroundTasks,
    skill_id: str = Form(...),
    df_json: str | None = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    agent_manager: AgentManager = Depends(get_agent_manager),
) -> Response:

    if skill_id not in agent_manager.list_skills():
        return JSONResponse(
            status_code=400, content={"error": f"Skill '{skill_id}' no encontrada."}
        )

    df, err_resp = _get_request_df(session, df_json)
    if err_resp:
        return err_resp
    session.current_df = df

    job_repo = get_job_repository()
    job_id = job_repo.create_job(skill_id, {"session_has_data": session.has_data()})
    background_tasks.add_task(_run_background_job, job_id, skill_id, session)

    return JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "status": "pending",
            "message": "Trabajo encolado exitosamente.",
        },
    )


@app.get("/api/jobs/{job_id}", summary="Check async job status")
def get_job_status(job_id: str) -> JSONResponse:
    job_repo = get_job_repository()
    job = job_repo.get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"error": "Trabajo no encontrado."})
    return JSONResponse(status_code=200, content=job)


def _get_request_df(
    session: AnalysisSession, df_json: str | None
) -> tuple[pd.DataFrame | None, JSONResponse | None]:

    if in_vercel_runtime():
        if not df_json:
            return None, JSONResponse(
                status_code=400, content={"error": "Session dataframe payload is required"}
            )
        try:
            return dataframe_from_split_json(df_json), None
        except ValueError:
            return None, JSONResponse(
                status_code=400, content={"error": "Invalid session dataframe payload"}
            )
    if df_json:
        try:
            return dataframe_from_split_json(df_json), None
        except ValueError:
            return None, JSONResponse(
                status_code=400, content={"error": "Invalid session dataframe payload"}
            )
    return session.current_df, None


def _prepare_session_dataframe(session: AnalysisSession, df_json: str | None):
    current_df, error_response = _get_request_df(session, df_json)
    if error_response:
        return None, error_response
    if current_df is None:
        return None, JSONResponse(status_code=400, content={"error": "No dataframe"})
    session.current_df = current_df
    return current_df, None


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
    result = agent_manager.execute_skill(
        "load_file", session, file_obj=file_obj, delimiter=delimiter
    )
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
    _, err = _prepare_session_dataframe(session, df_json)
    if err:
        return err
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
    _, err = _prepare_session_dataframe(session, df_json)
    if err:
        return err
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
    _, err = _prepare_session_dataframe(session, df_json)
    if err:
        return err
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
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    _, err = _prepare_session_dataframe(session, df_json)
    if err:
        return err
    result = agent_manager.execute_skill(
        "handle_outliers", session, column=column, treatment=treatment
    )
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
    save_analysis_session(session_id, session)
    count = result.changes.get("count", 0)
    detail = result.changes.get("detail", "")
    return {
        "message": f"{count} outliers: {detail}",
        "count": int(count),
        "preview": result.changes.get("preview", []),
        **_build_df_response(session.current_df),
    }


@app.get("/api/stats")
async def get_stats(
    response: Response,
    session: AnalysisSession = Depends(get_analysis_session),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    if in_vercel_runtime():
        return JSONResponse(
            status_code=400, content={"error": "Use POST /api/stats in Vercel mode"}
        )
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
    _, err = _prepare_session_dataframe(session, df_json)
    if err:
        return err
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
    _, err = _prepare_session_dataframe(session, df_json)
    if err:
        return err
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
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    _, err = _prepare_session_dataframe(session, df_json)
    if err:
        return err
    result = agent_manager.execute_skill("plot", session, type=type, x=x, y=y, col=col)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
    return result.changes.get("figure_json", {})


@app.post("/api/export")
async def export_data(
    format_type: str = Form("CSV"),
    df_json: str | None = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    _session_id: str = Depends(get_session_id),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    _, err = _prepare_session_dataframe(session, df_json)
    if err:
        return err
    result = agent_manager.execute_skill("export_file", session, format_type=format_type)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})
    return {"file_path": result.changes.get("file_path", "")}


@app.post("/api/auto-analyze")
async def auto_analyze_endpoint(
    df_json: str | None = Form(None),
    target_col: str | None = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    _, err = _prepare_session_dataframe(session, df_json)
    if err:
        return err
    result = agent_manager.execute_skill("auto_analyze", session, target_col=target_col)
    if result.changes.get("error"):
        return JSONResponse(status_code=400, content={"error": result.changes["error"]})

    save_analysis_session(session_id, session)
    return {
        "report": result.changes.get("result", {}),
        **_build_df_response(session.current_df),
    }
