"""
Limpieza y normalización de datos climáticos.
Convierte el DataFrame crudo a un formato limpio y consistente.
"""
import pandas as pd

from src.pipeline.utils.logger import get_logger

logger = get_logger(__name__)

# Mapeo de códigos WMO a descripciones en español
# Fuente: https://open-meteo.com/en/docs#weathervariables (WMO Code)
WMO_WEATHER_CODES: dict[int, str] = {
    0: "Despejado",
    1: "Mayormente despejado",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Neblina",
    48: "Neblina con escarcha",
    51: "Llovizna leve",
    53: "Llovizna moderada",
    55: "Llovizna intensa",
    61: "Lluvia leve",
    63: "Lluvia moderada",
    65: "Lluvia intensa",
    71: "Nevada leve",
    73: "Nevada moderada",
    75: "Nevada intensa",
    77: "Granizo",
    80: "Chubascos leves",
    81: "Chubascos moderados",
    82: "Chubascos intensos",
    85: "Chubascos de nieve leves",
    86: "Chubascos de nieve intensos",
    95: "Tormenta eléctrica",
    96: "Tormenta con granizo leve",
    99: "Tormenta con granizo intenso",
}


def clean_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte columnas al tipo de dato correcto."""
    df = df.copy()

    df["date"] = pd.to_datetime(df["date"]).dt.date

    numeric_cols = [
        "temperature_max", "temperature_min", "temperature_mean",
        "precipitation_sum", "precipitation_hours",
        "wind_speed_max", "wind_direction",
        "humidity_max", "humidity_min",
        "uv_index_max",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "weather_code" in df.columns:
        df["weather_code"] = pd.to_numeric(df["weather_code"], errors="coerce").astype("Int64")

    return df


def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estrategia de imputación de nulos:
    - Temperatura media: calculada desde max y min si ambas existen
    - Precipitación: 0 si es nulo (sin lluvia, no dato faltante en la mayoría de casos)
    - Resto: se mantienen como NaN (no inventamos datos)
    """
    df = df.copy()

    # Temperatura media calculada si falta
    mask = df["temperature_mean"].isnull()
    df.loc[mask, "temperature_mean"] = (
        (df.loc[mask, "temperature_max"] + df.loc[mask, "temperature_min"]) / 2
    )

    # Precipitación nula = sin lluvia
    df["precipitation_sum"] = df["precipitation_sum"].fillna(0.0)
    df["precipitation_hours"] = df["precipitation_hours"].fillna(0.0)

    return df


def add_weather_description(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega la descripción textual del código WMO."""
    df = df.copy()
    df["weather_description"] = (
        df["weather_code"]
        .map(WMO_WEATHER_CODES)
        .fillna("Desconocido")
    )
    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas derivadas útiles para el análisis."""
    df = df.copy()

    # Amplitud térmica: diferencia entre max y min
    df["temperature_range"] = (df["temperature_max"] - df["temperature_min"]).round(1)

    # Humedad media
    df["humidity_mean"] = ((df["humidity_max"] + df["humidity_min"]) / 2).round(1)

    # Categoría de lluvia
    df["precipitation_category"] = pd.cut(
        df["precipitation_sum"],
        bins=[-0.1, 0.0, 5.0, 20.0, 50.0, float("inf")],
        labels=["Sin lluvia", "Leve", "Moderada", "Fuerte", "Muy fuerte"],
    ).astype(str)

    # Categoría de temperatura (útil para mapas de calor)
    df["temperature_category"] = pd.cut(
        df["temperature_mean"],
        bins=[-float("inf"), 0, 10, 20, 30, float("inf")],
        labels=["Muy frío", "Frío", "Templado", "Cálido", "Muy cálido"],
    ).astype(str)

    return df


def round_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Redondea columnas numéricas a 1 decimal para consistencia."""
    numeric_cols = [
        "temperature_max", "temperature_min", "temperature_mean",
        "precipitation_sum", "wind_speed_max", "uv_index_max",
        "humidity_max", "humidity_min",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].round(1)
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pipeline de limpieza completo.
    Aplica todas las transformaciones en orden.
    """
    original_rows = len(df)

    df = (
        df
        .pipe(clean_types)
        .pipe(fill_missing_values)
        .pipe(add_weather_description)
        .pipe(add_derived_columns)
        .pipe(round_numeric_columns)
    )

    logger.info(
        f"Limpieza completada — "
        f"{len(df)} filas procesadas (de {original_rows})"
    )
    return df
