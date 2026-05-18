import io
import pandas as pd


def dataframe_to_split_json(df: pd.DataFrame) -> str:
    return df.to_json(orient="split")


def dataframe_from_split_json(df_json: str) -> pd.DataFrame:
    if not df_json:
        raise ValueError("Missing df_json payload")
    try:
        return pd.read_json(io.StringIO(df_json), orient="split")
    except ValueError as exc:
        raise ValueError("Invalid df_json payload") from exc
