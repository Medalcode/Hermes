import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.core.ports import PlotterProvider


class PlottingAdapter(PlotterProvider):
    """
    Driven Adapter for Visualization using Plotly.
    Generates interactive Figure objects.
    """

    @staticmethod
    def plot_correlation_heatmap(df: pd.DataFrame) -> go.Figure | None:
        if df is None:
            return None
        df_numeric = df.select_dtypes(include=np.number)
        if df_numeric.empty:
            return None

        try:
            corr = df_numeric.corr()
            fig = px.imshow(
                corr,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="RdBu_r",
                title="Mapa de Calor de Correlaciones",
            )
            return fig
        except Exception:
            return None

    @staticmethod
    def plot_distribution(df: pd.DataFrame | None, column: str | None = None) -> go.Figure | None:
        if df is None or not column or column not in df.columns:
            return None

        try:
            fig = px.histogram(
                df, x=column, marginal="box", title=f"Distribución: {column}", hover_data=df.columns
            )
            return fig
        except Exception:
            return None

    @staticmethod
    def plot_regression(
        df: pd.DataFrame | None, x_col: str | None = None, y_col: str | None = None
    ) -> go.Figure | None:
        if (
            df is None
            or not x_col
            or not y_col
            or x_col not in df.columns
            or y_col not in df.columns
        ):
            return None

        try:
            try:
                fig = px.scatter(
                    df,
                    x=x_col,
                    y=y_col,
                    trendline="ols",
                    title=f"Regresión: {x_col} vs {y_col}",
                    hover_data=df.columns,
                )
            except Exception:
                fig = px.scatter(
                    df,
                    x=x_col,
                    y=y_col,
                    title=f"Regresión: {x_col} vs {y_col}",
                    hover_data=df.columns,
                )
            return fig
        except Exception:
            return None

    @staticmethod
    def plot_clusters(
        df: pd.DataFrame | None, x_col: str | None = None, y_col: str | None = None
    ) -> go.Figure | None:
        if (
            df is None
            or not x_col
            or not y_col
            or x_col not in df.columns
            or y_col not in df.columns
        ):
            return None

        try:
            color_col = "Cluster" if "Cluster" in df.columns else None
            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                color=color_col,
                title=f"Clusters: {x_col} vs {y_col}",
                hover_data=df.columns,
            )
            return fig
        except Exception:
            return None
