import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Optional

class PlottingAdapter:
    """
    Driven Adapter for Visualization using Plotly.
    Generates interactive Figure objects.
    """
    
    @staticmethod
    def plot_correlation_heatmap(df: pd.DataFrame) -> Optional[go.Figure]:
        if df is None: return None
        df_numeric = df.select_dtypes(include=np.number)
        if df_numeric.empty: return None
        
        try:
            corr = df_numeric.corr()
            fig = px.imshow(
                corr, 
                text_auto=True, 
                aspect="auto", 
                color_continuous_scale="RdBu_r",
                title="Mapa de Calor de Correlaciones"
            )
            return fig
        except:
            return None

    @staticmethod
    def plot_distribution(df: pd.DataFrame, column: str) -> Optional[go.Figure]:
        if df is None or column not in df.columns: return None
        
        try:
            # Create a histogram with a box plot margin
            fig = px.histogram(
                df, 
                x=column, 
                marginal="box", # Shows boxplot on top
                title=f"Distribución: {column}",
                hover_data=df.columns
            )
            return fig
        except:
            return None

    @staticmethod
    def plot_regression(df: pd.DataFrame, x_col: str, y_col: str) -> Optional[go.Figure]:
        if df is None or x_col not in df.columns or y_col not in df.columns: return None
        
        try:
            fig = px.scatter(
                df, 
                x=x_col, 
                y=y_col, 
                trendline="ols", # Adds regression line
                title=f"Regresión: {x_col} vs {y_col}",
                hover_data=df.columns
            )
            return fig
        except:
            return None

    @staticmethod
    def plot_clusters(df: pd.DataFrame, x_col: str, y_col: str) -> Optional[go.Figure]:
        if df is None or x_col not in df.columns or y_col not in df.columns:
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
        except:
            return None
