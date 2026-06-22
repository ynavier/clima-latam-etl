"""Tests unitarios para el módulo de limpieza."""
from datetime import date, timedelta

import pandas as pd
import pytest

from src.pipeline.transform.cleaner import (
    add_derived_columns,
    add_weather_description,
    clean,
    clean_types,
    fill_missing_values,
)


def make_raw_df() -> pd.DataFrame:
    """DataFrame base que simula la salida del módulo de validación."""
    return pd.DataFrame({
        "date": ["2024-01-15", "2024-01-16"],
        "city_name": ["Lima", "Bogotá"],
        "country": ["Perú", "Colombia"],
        "country_code": ["PE", "CO"],
        "region": ["Costa", "Andina"],
        "latitude": [-12.04, 4.71],
        "longitude": [-77.04, -74.07],
        "timezone": ["America/Lima", "America/Bogota"],
        "temperature_max": [25.5, 18.3],
        "temperature_min": [15.2, 10.1],
        "temperature_mean": [None, 14.2],   # Nulo para probar imputación
        "precipitation_sum": [None, 5.2],   # Nulo para probar fillna
        "precipitation_hours": [0.0, 2.0],
        "wind_speed_max": [15.0, 20.0],
        "wind_direction": [180.0, 90.0],
        "humidity_max": [80.0, 70.0],
        "humidity_min": [60.0, 55.0],
        "uv_index_max": [7.0, 4.0],
        "weather_code": [0, 61],
        "sunrise": ["2024-01-15T06:00", "2024-01-16T06:05"],
        "sunset": ["2024-01-15T18:30", "2024-01-16T18:25"],
    })


class TestCleanTypes:
    def test_date_conversion(self):
        df = make_raw_df()
        result = clean_types(df)
        assert result["date"].dtype == "object"  # date objects

    def test_numeric_columns(self):
        df = make_raw_df()
        result = clean_types(df)
        assert pd.api.types.is_float_dtype(result["temperature_max"])

    def test_weather_code_integer(self):
        df = make_raw_df()
        result = clean_types(df)
        assert result["weather_code"].dtype.name == "Int64"


class TestFillMissingValues:
    def test_temperature_mean_imputed(self):
        """Temperatura media calculada desde max y min cuando es nula."""
        df = clean_types(make_raw_df())
        result = fill_missing_values(df)
        expected = (25.5 + 15.2) / 2
        assert abs(result.loc[0, "temperature_mean"] - expected) < 0.01

    def test_precipitation_filled_with_zero(self):
        """Precipitación nula se rellena con 0 (sin lluvia)."""
        df = clean_types(make_raw_df())
        result = fill_missing_values(df)
        assert result.loc[0, "precipitation_sum"] == 0.0


class TestWeatherDescription:
    def test_known_code(self):
        df = clean_types(make_raw_df())
        df = fill_missing_values(df)
        result = add_weather_description(df)
        assert result.loc[0, "weather_description"] == "Despejado"  # código 0
        assert result.loc[1, "weather_description"] == "Lluvia leve"  # código 61

    def test_unknown_code(self):
        df = clean_types(make_raw_df())
        df.loc[0, "weather_code"] = 999  # código inexistente
        result = add_weather_description(df)
        assert result.loc[0, "weather_description"] == "Desconocido"


class TestDerivedColumns:
    def test_temperature_range(self):
        df = clean_types(make_raw_df())
        df = fill_missing_values(df)
        result = add_derived_columns(df)
        expected = round(25.5 - 15.2, 1)
        assert result.loc[0, "temperature_range"] == expected

    def test_humidity_mean(self):
        df = clean_types(make_raw_df())
        df = fill_missing_values(df)
        result = add_derived_columns(df)
        expected = round((80.0 + 60.0) / 2, 1)
        assert result.loc[0, "humidity_mean"] == expected

    def test_precipitation_category(self):
        df = clean_types(make_raw_df())
        df = fill_missing_values(df)
        result = add_derived_columns(df)
        assert result.loc[0, "precipitation_category"] == "Sin lluvia"
        assert result.loc[1, "precipitation_category"] == "Moderada"  # 5.2mm cae en (5.0, 20.0]


class TestCleanPipeline:
    def test_full_pipeline_runs(self):
        """El pipeline completo no debe lanzar excepciones."""
        df = make_raw_df()
        result = clean(df)
        assert len(result) == 2
        assert "weather_description" in result.columns
        assert "temperature_range" in result.columns
        assert "precipitation_category" in result.columns

    def test_no_rows_lost(self):
        """El limpiador no debe eliminar filas, solo transformarlas."""
        df = make_raw_df()
        result = clean(df)
        assert len(result) == len(df)
