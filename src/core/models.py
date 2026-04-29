from dataclasses import dataclass, field

import pandas as pd


@dataclass
class OperationLog:
    """Represents a single log entry for an operation."""
    message: str

    def __str__(self):
        return self.message

@dataclass
class AnalysisSession:
    """
    Holds the state of the current user session.
    Replaces global variables 'estado_df' and 'entradas_log'.
    """
    current_df: pd.DataFrame | None = None
    logs: list[OperationLog] = field(default_factory=list)

    def add_log(self, message: str):
        self.logs.append(OperationLog(message))

    def clear_logs(self):
        self.logs = []

    def get_logs_as_string(self) -> str:
        return "\n".join([str(log) for log in self.logs])

    def has_data(self) -> bool:
        return self.current_df is not None
