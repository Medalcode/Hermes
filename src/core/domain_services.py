# from scipy.stats import skew, kurtosis, shapiro (Removed for Vercel size limit)

import numpy as np
import pandas as pd


class StatisticalAnalyzer:
    """
    Domain service for performing statistical analysis on DataFrames.
    Pure logic, no UI dependencies.
    """

    @staticmethod
    def get_numeric_columns(df: pd.DataFrame) -> list[str]:
        if df is None:
            return []
        return df.select_dtypes(include=np.number).columns.tolist()

    @staticmethod
    def get_categorical_columns(df: pd.DataFrame) -> list[str]:
        if df is None:
            return []
        return df.select_dtypes(include=['object', 'category', 'str']).columns.tolist()

    def calculate_descriptive_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates descriptive statistics including median."""
        df_numeric = df.select_dtypes(include=np.number)
        if df_numeric.empty:
            return pd.DataFrame()

        stats = df_numeric.describe().T
        stats['median'] = df_numeric.median()
        # Reorder and round
        cols = ['count', 'mean', 'median', 'std', 'min', '25%', '50%', '75%', 'max']
        return stats[cols].round(3)

    def calculate_distribution_shape(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates Skewness and Kurtosis (Fisher)."""
        df_numeric = df.select_dtypes(include=np.number)
        if df_numeric.empty:
            return pd.DataFrame()

        return pd.DataFrame({
            'Curtosis (Normal = 0)': df_numeric.kurt(),
            'Asimetría (Skewness)': df_numeric.skew()
        }).round(3)

    def calculate_correlation_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates Pearson correlation matrix."""
        df_numeric = df.select_dtypes(include=np.number)
        if df_numeric.empty:
            return pd.DataFrame()
        return df_numeric.corr(method='pearson')

    def check_normality(self, series: pd.Series) -> tuple[bool, float]:
        """
        Performs approximate normality check (Shapiro removed).
        Returns (is_normal, p_value) - Placeholder
        """
        # Shapiro-Wilk requires scipy, which is too heavy for Vercel free tier (250MB limit).
        # We'll return a dummy value or a heuristic.
        # Heuristic: if skew < 2 and kurt < 2, it's roughly normal-ish.
        try:
            s_val = series.dropna()
            if len(s_val) < 3:
                return False, 0.0

            k = s_val.kurt()
            s = s_val.skew()
            is_normal = abs(k) < 2.0 and abs(s) < 2.0
            return is_normal, 1.0 if is_normal else 0.0
        except:
            return False, 0.0

class DataCleaner:
    """Domain service for handling Missing Values."""

    @staticmethod
    def handle_nulls(df: pd.DataFrame, columns: list[str], method: str) -> tuple[pd.DataFrame, int]:
        """
        Returns (processed_df, affected_rows_count).
        Does NOT mutate input df in-place.
        """
        if df is None:
            return None, 0

        df_clean = df.copy()
        affected_count = 0

        # Initial check
        total_nulls_start = df_clean[columns].isnull().sum().sum()
        if total_nulls_start == 0:
            return df_clean, 0

        if method == "Eliminar filas":
            initial_rows = len(df_clean)
            df_clean = df_clean.dropna(subset=columns)
            affected_count = initial_rows - len(df_clean)
            return df_clean, affected_count

        for col in columns:
            if col not in df_clean.columns:
                continue

            val = None
            is_numeric = pd.api.types.is_numeric_dtype(df_clean[col])

            if is_numeric:
                if method == "Llenar con promedio":
                    val = df_clean[col].mean()
                elif method == "Llenar con mediana (Mejora 5)":
                    val = df_clean[col].median()
                elif method == "Llenar con máximo":
                    val = df_clean[col].max()
                elif method == "Llenar con mínimo":
                    val = df_clean[col].min()
                elif method == "Llenar con cero":
                    val = 0
            else:
                 if method == "Llenar con moda (Categórica)":
                    if not df_clean[col].mode().empty:
                        val = df_clean[col].mode()[0]

            if val is not None:
                n_nulls = df_clean[col].isnull().sum()
                df_clean[col] = df_clean[col].fillna(val)
                affected_count += n_nulls

        return df_clean, affected_count

# from sklearn.preprocessing import MinMaxScaler, StandardScaler (Removed for Vercel)

class DataScaler:
    """Domain service for Normalization and Standardization."""

    @staticmethod
    def apply_scaling(df: pd.DataFrame, columns: list[str], method: str) -> pd.DataFrame:
        if df is None:
            return None

        df_scaled = df.copy()

        for col in columns:
            if col in df_scaled.columns and pd.api.types.is_numeric_dtype(df_scaled[col]):
                series = df_scaled[col]

                if method == "Min-Max":
                    min_val = series.min()
                    max_val = series.max()
                    # Avoid division by zero
                    if max_val - min_val == 0:
                        df_scaled[col] = 0
                    else:
                        df_scaled[col] = (series - min_val) / (max_val - min_val)

                elif method == "Z-Score":
                    mean_val = series.mean()
                    std_val = series.std()
                    if std_val == 0:
                        df_scaled[col] = 0
                    else:
                        df_scaled[col] = (series - mean_val) / std_val

        return df_scaled

class OutlierManager:
    """Domain service for Outlier Detection and Treatment (IQR)."""

    @staticmethod
    def detect_and_treat(df: pd.DataFrame, column: str, treatment: str) -> tuple[pd.DataFrame, int, str]:
        """
        Returns (processed_df, num_outliers_detected, message_detail).
        """
        if df is None or column not in df.columns:
            return df, 0, "Error: Columna no encontrada"

        df_out = df.copy()

        # IQR Calculation
        Q1 = df_out[column].quantile(0.25)
        Q3 = df_out[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers_mask = (df_out[column] < lower_bound) | (df_out[column] > upper_bound)
        num_outliers = outliers_mask.sum()

        if num_outliers == 0:
            return df_out, 0, "No se detectaron outliers."

        if treatment == "Eliminar registros":
            df_out = df_out[~outliers_mask]
            return df_out, num_outliers, "Eliminados."

        elif treatment == "Capping (Winsorización)":
            df_out[column] = np.where(df_out[column] > upper_bound, upper_bound, df_out[column])
            df_out[column] = np.where(df_out[column] < lower_bound, lower_bound, df_out[column])
            return df_out, num_outliers, "Winsorizados."

        else: # Informar
            return df_out, num_outliers, "Solo detectados (sin cambios)."

# from sklearn.cluster import KMeans

class Clusterer:
    """Domain service for Unsupervised Learning (Clustering)."""

    @staticmethod
    def kmeans(df: pd.DataFrame, columns: list[str], k: int) -> tuple[pd.DataFrame, str]:
        if df is None or not columns:
            return df, "Error: Datos o columnas faltantes."

        try:
            df_clustered = df.copy()
            X = df_clustered[columns].dropna().astype(float).values

            if len(X) < k:
                return df, f"Error: No hay suficientes datos para {k} clusters."

            # Simple manual KMeans using numpy
            # Initialize centroids randomly
            np.random.seed(42)
            idx = np.random.choice(len(X), k, replace=False)
            centroids = X[idx]

            clusters = np.zeros(len(X))

            # Simple iterations (max 10 for performance/simplicity)
            for _ in range(10):
                # Distance matrix: (n_samples, k)
                # Compute distance from each point to each centroid
                dists = np.linalg.norm(X[:, np.newaxis] - centroids, axis=2)

                # Assign to nearest centroid
                new_clusters = np.argmin(dists, axis=1)

                if np.array_equal(clusters, new_clusters):
                    break

                clusters = new_clusters

                # Update centroids
                for i in range(k):
                    points = X[clusters == i]
                    if len(points) > 0:
                        centroids[i] = points.mean(axis=0)


            df_clustered.loc[df_clustered[columns].dropna().index, 'Cluster'] = clusters
            df_clustered['Cluster'] = df_clustered['Cluster'].fillna(-1).astype(int)

            return df_clustered, f"Clustering completado (K={k}) - NativeMode."
        except Exception as e:
            return df, f"Error clustering: {str(e)}"


