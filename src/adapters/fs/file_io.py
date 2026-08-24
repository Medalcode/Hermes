import io
import os
from pathlib import Path

import pandas as pd

from src.core.ports import FileIOProvider


class FileSystemAdapter(FileIOProvider):
    """
    Driven Adapter for File I/O.
    Shields the Core from file format details and path handling.
    """

    @staticmethod
    def load_file(file_obj, delimiter: str = ",") -> tuple[pd.DataFrame, str]:
        """
        Loads a file (CSV or Excel) into a DataFrame.
        Accepts a file path (str/Path) or a file-like object (BytesIO, etc.).
        Returns (DataFrame, ErrorMessage).
        """
        if file_obj is None:
            return None, "Error: Debe subir un archivo."

        has_read = hasattr(file_obj, "read")
        if has_read:
            raw = file_obj.read()
            if isinstance(raw, bytes):
                file_obj = io.BytesIO(raw)

        name = getattr(file_obj, "name", "")
        path = Path(name) if name else Path("file.csv")

        try:
            df = None
            is_bytes = isinstance(file_obj, io.BytesIO) or has_read
            is_csv = path.suffix.lower() == ".csv" or (
                is_bytes and path.suffix.lower() != ".xls" and path.suffix.lower() != ".xlsx"
            )

            if is_csv:
                try:
                    df = pd.read_csv(file_obj, delimiter=delimiter, encoding="utf-8")
                except UnicodeDecodeError:
                    file_obj.seek(0)
                    df = pd.read_csv(file_obj, delimiter=delimiter, encoding="ISO-8859-1")

                if df.shape[1] == 1:
                    return None, "Error: CSV de una sola columna. Verifique el delimitador."

            elif path.suffix.lower() in [".xls", ".xlsx"]:
                df = pd.read_excel(file_obj)
            else:
                return None, "Error: Formato no soportado (use CSV o Excel)."

            df.replace([float("inf"), float("-inf")], float("nan"), inplace=True)
            return df, ""

        except Exception as e:
            return None, f"Error de lectura: {str(e)}"

    @staticmethod
    def export_file(df: pd.DataFrame | None, format_type: str) -> tuple[str | None, str]:
        """
        Saves DataFrame to disk.
        Returns (file_path, error_message).
        """

        if df is None:
            return None, "No hay datos para exportar."

        try:
            target_dir = "/tmp" if os.environ.get("VERCEL") else "."
            if format_type == "CSV":
                filename = os.path.join(target_dir, "datos_procesados.csv")
                df.to_csv(filename, index=False)
                return filename, ""
            elif format_type == "Excel":
                filename = os.path.join(target_dir, "datos_procesados.xlsx")
                df.to_excel(filename, index=False)
                return filename, ""
            else:
                return None, "Formato desconocido."
        except Exception as e:
            return None, str(e)

    @staticmethod
    def save_report(logs: str, filename: str = "reporte_analisis.txt") -> str:
        with open(filename, "w") as f:
            f.write(logs)
        return filename
