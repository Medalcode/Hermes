from fastapi import FastAPI, UploadFile, File, Form, Request, Depends, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
import pandas as pd
import io
import json
from typing import List, Optional

# Core & Adapters
from src.core.models import AnalysisSession
from src.core.domain_services import StatisticalAnalyzer, DataCleaner, DataScaler, Clusterer
from src.adapters.fs.file_io import FileSystemAdapter
from src.adapters.visualization.plotter import PlottingAdapter
from src.adapters.api.dependencies import get_analysis_session, save_analysis_session, get_session_id, in_vercel_runtime
from src.adapters.api.dataframe_json import dataframe_to_split_json, dataframe_from_split_json

app = FastAPI(title="Myna API")

# Mount Static & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def _get_request_df(session: AnalysisSession, df_json: Optional[str]):
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
        "shape": df.shape,
    }

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, response: Response):
    # Ensure session cookie is set on load
    # We call get_session_id manually or just let the first API call handle it, 
    # but for checking "existing" state in UI, we might need it.
    # Ideally, frontend manages this, but we'll set it here to be safe.
    from src.adapters.api.dependencies import get_session_id
    await get_session_id(request, response)
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...), 
    delimiter: str = Form(","),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id)
):
    contents = await file.read()
    file_obj = io.BytesIO(contents)
    file_obj.name = file.filename
    
    df, error = FileSystemAdapter.load_file(file_obj, delimiter)
    
    if error:
        return JSONResponse(status_code=400, content={"error": error})
        
    session.current_df = df
    session.add_log(f"API: Uploaded {file.filename}")
    
    # Persist State
    save_analysis_session(session_id, session)
    
    cols = df.columns.tolist()
    num_cols = StatisticalAnalyzer.get_numeric_columns(df)
    preview = df.head(10).fillna("").to_dict(orient="records")
    
    return {
        "message": "Carga exitosa", 
        "columns": cols, 
        "numeric_columns": num_cols,
        "preview": preview,
        "shape": df.shape,
        "df_json": dataframe_to_split_json(df)
    }

@app.post("/api/clean/nulls")
async def clean_nulls(
    cols: List[str] = Form(...), 
    method: str = Form(...),
    df_json: Optional[str] = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id)
):
    current_df, error_response = _get_request_df(session, df_json)
    if error_response:
        return error_response
    if current_df is None:
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    
    df_new, count = DataCleaner.handle_nulls(current_df, cols, method)
    session.current_df = df_new
    session.add_log(f"API: Nulls cleaned with {method} on {cols}")
    
    save_analysis_session(session_id, session)
    
    return {
        "message": f"Se trataron {count} valores.",
        "preview": df_new.head(10).fillna("").to_dict(orient="records"),
        **_build_df_response(df_new),
    }

@app.post("/api/clean/scale")
async def scale_data(
    cols: List[str] = Form(...), 
    method: str = Form(...),
    df_json: Optional[str] = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id)
):
    current_df, error_response = _get_request_df(session, df_json)
    if error_response:
        return error_response
    if current_df is None:
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    
    df_new = DataScaler.apply_scaling(current_df, cols, method)
    session.current_df = df_new
    session.add_log(f"API: Scaled {cols} with {method}")
    
    save_analysis_session(session_id, session)
    
    return {
        "message": f"Escalado completado.",
        "preview": df_new.head(10).fillna("").to_dict(orient="records"),
        **_build_df_response(df_new),
    }

@app.get("/api/stats")
async def get_stats(response: Response, session: AnalysisSession = Depends(get_analysis_session)):
    if in_vercel_runtime():
        return JSONResponse(status_code=400, content={"error": "This operation requires session data in the request body"})
    if not session.has_data():
        return JSONResponse(status_code=400, content={"error": "No dataframe"})

    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Wed, 31 Dec 2026 23:59:59 GMT"
    response.headers["Link"] = '</api/stats>; rel="successor-version"'
    
    analyzer = StatisticalAnalyzer()
    desc = analyzer.calculate_descriptive_stats(session.current_df)
    corr = analyzer.calculate_correlation_matrix(session.current_df)
    
    return {
        "descriptive": desc.to_markdown() if not desc.empty else "No data",
        "correlation": corr.to_json(orient="split") if corr is not None else None
    }


@app.post("/api/stats")
async def post_stats(
    df_json: Optional[str] = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
):
    current_df, error_response = _get_request_df(session, df_json)
    if error_response:
        return error_response
    if current_df is None:
        return JSONResponse(status_code=400, content={"error": "No dataframe"})

    analyzer = StatisticalAnalyzer()
    desc = analyzer.calculate_descriptive_stats(current_df)
    corr = analyzer.calculate_correlation_matrix(current_df)

    return {
        "descriptive": desc.to_markdown() if not desc.empty else "No data",
        "correlation": corr.to_json(orient="split") if corr is not None else None,
        **_build_df_response(current_df),
    }

@app.post("/api/cluster")
async def run_cluster(
    cols: List[str] = Form(...), 
    k: int = Form(...),
    df_json: Optional[str] = Form(None),
    session: AnalysisSession = Depends(get_analysis_session),
    session_id: str = Depends(get_session_id)
):
    current_df, error_response = _get_request_df(session, df_json)
    if error_response:
        return error_response
    if current_df is None:
        return JSONResponse(status_code=400, content={"error": "No dataframe"})
    
    df_new, msg = Clusterer.kmeans(current_df, cols, k)
    session.current_df = df_new
    
    save_analysis_session(session_id, session)
    
    return {
        "message": msg,
        "preview": df_new.head(10).fillna("").to_dict(orient="records"),
        **_build_df_response(df_new),
    }

@app.post("/api/plot")
async def get_plot(
    type: str = Form(...), 
    x: str = Form(None), 
    y: str = Form(None), 
    col: str = Form(None),
    df_json: Optional[str] = Form(None),
    session: AnalysisSession = Depends(get_analysis_session)
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
