import json
import os

import pandas as pd

from src.core.models import AnalysisSession, OperationLog
from src.core.ports import DataRepository, SessionRepository


class LocalFileSessionRepository(SessionRepository):
    def __init__(self, storage_dir: str = "storage/sessions"):
        if os.environ.get("VERCEL"):
            # Vercel filesystem is read-only except for /tmp
            storage_dir = "/tmp/storage/sessions"

        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_path(self, session_id: str) -> str:
        return os.path.join(self.storage_dir, f"{session_id}.json")

    def get_session(self, session_id: str) -> AnalysisSession | None:
        path = self._get_path(session_id)
        if not os.path.exists(path):
            return None

        with open(path) as f:
            data = json.load(f)

        session = AnalysisSession()
        # Reconstruct logs
        if "logs" in data:
            session.logs = [OperationLog(log["message"]) for log in data["logs"]]

        return session

    def save_session(self, session: AnalysisSession, session_id: str) -> None:
        path = self._get_path(session_id)
        data = {
            "logs": [{"message": log.message} for log in session.logs]
        }
        with open(path, "w") as f:
            json.dump(data, f)

class LocalFileDataRepository(DataRepository):
    def __init__(self, storage_dir: str = "storage/data"):
        if os.environ.get("VERCEL"):
            # Vercel filesystem is read-only except for /tmp
            storage_dir = "/tmp/storage/data"

        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_path(self, session_id: str) -> str:
        return os.path.join(self.storage_dir, f"{session_id}.pkl")

    def save_dataframe(self, session_id: str, df: pd.DataFrame) -> None:
        path = self._get_path(session_id)
        # Use pickle to avoid pyarrow dependency (size limit on Vercel)
        df.to_pickle(path)

    def load_dataframe(self, session_id: str) -> pd.DataFrame | None:
        path = self._get_path(session_id)
        if not os.path.exists(path):
            return None
        return pd.read_pickle(path)
