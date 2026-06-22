"""Tests unitarios para las reglas de validación."""
from datetime import date, timedelta

import pandas as pd
import pytest

from src.pipeline.validate.rules import (
    check_duplicates,
    check_no_future_dates,
    check_null_percentage,
    check_required_fields,
    check_temperature_consistency,
    check_temperature_range,
)


def make_valid_df() -> pd.DataFrame:
    """DataFrame base con datos completamente válidos."""
    return pd.DataFrame({
        "date": [date.today() - timedelta(days=i) for i in range(3)],
        "city_name": ["Lima", "Bogotá", "Santiago"],
        "country_code": ["PE", "CO", "CL"],
        "latitude": [-12.04, 4.71, -33.45],
        "longitude": [-77.04, -74.07, -70.65],
        "temperature_max": [25.0, 18.0, 22.0],
        "temperature_min": [15.0, 10.0, 12.0],
        "precipitation_sum": [0.0, 5.2, 0.0],
    })


class TestRequiredFields:
    def test_all_fields_present(self):
        df = make_valid_df()
        required = ["date", "city_name", "country_code", "temperature_max", "temperature_min"]
        result = check_required_fields(df, required)
        assert result.passed

    def test_missing_field(self):
        df = make_valid_df().drop(columns=["temperature_max"])
        required = ["date", "city_name", "temperature_max"]
        result = check_required_fields(df, required)
        assert not result.passed
        assert "temperature_max" in result.detail


class TestTemperatureRange:
    def test_valid_temperatures(self):
        df = make_valid_df()
        result = check_temperature_range(df, min_temp=-80, max_temp=60)
        assert result.passed
        assert result.affected_rows == 0

    def test_temperature_too_high(self):
        df = make_valid_df()
        df.loc[0, "temperature_max"] = 65.0  # Fuera de rango
        result = check_temperature_range(df, min_temp=-80, max_temp=60)
        assert not result.passed
        assert result.affected_rows == 1

    def test_temperature_too_low(self):
        df = make_valid_df()
        df.loc[0, "temperature_min"] = -90.0  # Más frío que el récord mundial
        result = check_temperature_range(df, min_temp=-80, max_temp=60)
        assert not result.passed


class TestFutureDates:
    def test_no_future_dates(self):
        df = make_valid_df()
        result = check_no_future_dates(df)
        assert result.passed

    def test_with_future_date(self):
        df = make_valid_df()
        df.loc[0, "date"] = date.today() + timedelta(days=1)
        result = check_no_future_dates(df)
        assert not result.passed
        assert result.affected_rows == 1


class TestDuplicates:
    def test_no_duplicates(self):
        df = make_valid_df()
        result = check_duplicates(df)
        assert result.passed

    def test_with_duplicates(self):
        df = make_valid_df()
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)  # Duplicar primera fila
        result = check_duplicates(df)
        assert not result.passed
        assert result.affected_rows > 0


class TestNullPercentage:
    def test_no_nulls(self):
        df = make_valid_df()
        result = check_null_percentage(df, max_pct=10.0)
        assert result.passed

    def test_too_many_nulls(self):
        df = make_valid_df()
        df["temperature_max"] = None  # 100% nulos en esta columna
        result = check_null_percentage(df, max_pct=5.0)
        assert not result.passed


class TestTemperatureConsistency:
    def test_valid_range(self):
        df = make_valid_df()
        result = check_temperature_consistency(df)
        assert result.passed

    def test_min_greater_than_max(self):
        df = make_valid_df()
        df.loc[0, "temperature_min"] = 30.0
        df.loc[0, "temperature_max"] = 20.0  # min > max → inválido
        result = check_temperature_consistency(df)
        assert not result.passed
        assert result.affected_rows == 1
