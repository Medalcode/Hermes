import os
import uuid

from fastapi import Depends, HTTPException, Request, Response, status

# --- Registro de Super-Skills ---
# La importación de cada módulo activa los decoradores @register_skill,
# que pueblan el registro global _SKILL_REGISTRY en base.py.
# Añadir aquí cualquier nuevo módulo de skills.
import src.core.agents.skills.io_skills as io_skills
import src.core.agents.skills.visualization_skills as visualization_skills
from src.adapters.fs.file_io import FileSystemAdapter
from src.adapters.repositories.local_storage import (
    LocalFileDataRepository,
    LocalFileSessionRepository,
)
from src.adapters.visualization.plotter import PlottingAdapter
from src.core.agents.base import AgentManager
from src.core.models import AnalysisSession

# Enlazar adaptadores concretos a los puertos esperados por las skills (Inversión de dependencias)
io_skills.set_file_io_provider(FileSystemAdapter())
visualization_skills.set_plotter_provider(PlottingAdapter())

# Singleton instances (in a real app, use a proper DI container)
session_repo = LocalFileSessionRepository()
data_repo = LocalFileDataRepository()
# Agent manager singleton (registro inicial de skills se realiza por decorador)
agent_manager = AgentManager()


def in_vercel_runtime() -> bool:
    return bool(os.environ.get("VERCEL"))


async def get_session_id(request: Request, response: Response):
    if in_vercel_runtime():
        return "vercel-stateless"
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(key="session_id", value=session_id)
    return session_id


async def get_analysis_session(session_id: str = Depends(get_session_id)) -> AnalysisSession:
    if in_vercel_runtime():
        return AnalysisSession()
    # Load metadata
    session = session_repo.get_session(session_id)
    if not session:
        session = AnalysisSession()

    # Load heavy data
    df = data_repo.load_dataframe(session_id)
    if df is not None:
        session.current_df = df

    return session


def save_analysis_session(session_id: str, session: AnalysisSession):
    if in_vercel_runtime():
        return
    session_repo.save_session(session, session_id)
    if session.current_df is not None:
        data_repo.save_dataframe(session_id, session.current_df)


def get_agent_manager():
    return agent_manager


async def verify_api_key(request: Request):
    api_key = os.environ.get("MYNA_API_KEY")
    if api_key:
        provided = request.headers.get("X-API-Key") or request.headers.get(
            "Authorization", ""
        ).removeprefix("Bearer ")
        if not provided or provided != api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key. Provide via X-API-Key header.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return True
