from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from .models import AnalysisSession


class SessionRepository(ABC):
    @abstractmethod
    def get_session(self, session_id: str) -> AnalysisSession | None:
        """Retrieves a session metadata by ID."""
        pass

    @abstractmethod
    def save_session(self, session: AnalysisSession, session_id: str) -> None:
        """Saves session metadata."""
        pass


class DataRepository(ABC):
    @abstractmethod
    def save_dataframe(self, session_id: str, df: pd.DataFrame) -> None:
        """Persists the dataframe for a given session."""
        pass

    @abstractmethod
    def load_dataframe(self, session_id: str) -> pd.DataFrame | None:
        """Loads the dataframe for a given session."""
        pass


class FileIOProvider(ABC):
    @abstractmethod
    def load_file(self, file_obj: Any, delimiter: str = ",") -> tuple[pd.DataFrame | None, str]:
        """Loads a file into a DataFrame."""
        pass

    @abstractmethod
    def export_file(self, df: pd.DataFrame | None, format_type: str) -> tuple[str | None, str]:
        """Exports a DataFrame to file format."""
        pass


class PlotterProvider(ABC):
    @abstractmethod
    def plot_correlation_heatmap(self, df: pd.DataFrame | None) -> Any:
        pass

    @abstractmethod
    def plot_distribution(self, df: pd.DataFrame | None, column: str | None) -> Any:
        pass

    @abstractmethod
    def plot_regression(self, df: pd.DataFrame | None, x_col: str | None, y_col: str | None) -> Any:
        pass

    @abstractmethod
    def plot_clusters(self, df: pd.DataFrame | None, x_col: str | None, y_col: str | None) -> Any:
        pass
