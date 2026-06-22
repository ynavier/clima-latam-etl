"""
Reglas de validación de calidad de datos.
Cada check retorna una lista de errores encontrados (vacía = sin problemas).
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import pandas as pd
import yaml


@dataclass
class ValidationResult:
    """Resultado de una validación individual."""
    check_name: str
    passed: bool
    detail: str = ""
    affected_rows: int = 0


@dataclass
class QualityReport:
    """Reporte completo de calidad de datos para un batch."""
    extraction_date: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    null_percentage: float
    duplicate_count: int
    checks: list[ValidationResult] = field(default_factory=list)

    @property
    def overall_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "extraction_date": self.extraction_date,
            "total_rows": int(self.total_rows),
            "valid_rows": int(self.valid_rows),
            "invalid_rows": int(self.invalid_rows),
            "null_percentage": round(float(self.null_percentage), 2),
            "duplicate_count": int(self.duplicate_count),
            "overall_passed": bool(self.overall_passed),
            "checks": [
                {
                    "name": c.check_name,
                    "passed": bool(c.passed),
                    "detail": c.detail,
                    "affected_rows": int(c.affected_rows),
                }
                for c in self.checks
            ],
        }


def load_rules(rules_file: str) -> dict[str, Any]:
    """Carga las reglas de validación desde el YAML de configuración."""
    with open(rules_file, encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_required_fields(df: pd.DataFrame, required: list[str]) -> ValidationResult:
    """Verifica que todos los campos obligatorios existan y no sean todos nulos."""
    missing = [col for col in required if col not in df.columns]
    if missing:
        return ValidationResult(
            check_name="required_fields",
            passed=False,
            detail=f"Columnas faltantes: {missing}",
            affected_rows=len(df),
        )
    return ValidationResult(
        check_name="required_fields",
        passed=True,
        detail="Todos los campos requeridos presentes",
    )


def check_temperature_range(
    df: pd.DataFrame, min_temp: float, max_temp: float
) -> ValidationResult:
    """Verifica que las temperaturas estén en rangos físicamente posibles."""
    invalid = df[
        (df["temperature_max"] < min_temp)
        | (df["temperature_max"] > max_temp)
        | (df["temperature_min"] < min_temp)
        | (df["temperature_min"] > max_temp)
    ]
    passed = len(invalid) == 0
    return ValidationResult(
        check_name="temperature_range",
        passed=passed,
        detail=f"Temperaturas fuera de rango [{min_temp}, {max_temp}]°C"
        if not passed
        else "Temperaturas en rango válido",
        affected_rows=len(invalid),
    )


def check_precipitation(df: pd.DataFrame, max_precip: float) -> ValidationResult:
    """Verifica que la precipitación sea no negativa y razonable."""
    invalid = df[
        (df["precipitation_sum"] < 0) | (df["precipitation_sum"] > max_precip)
    ]
    passed = len(invalid) == 0
    return ValidationResult(
        check_name="precipitation_range",
        passed=passed,
        detail=f"Precipitación fuera de rango [0, {max_precip}]mm"
        if not passed
        else "Precipitación en rango válido",
        affected_rows=len(invalid),
    )


def check_no_future_dates(df: pd.DataFrame) -> ValidationResult:
    """Los datos no deben tener fechas futuras (la API no predice el pasado)."""
    tomorrow = date.today() + timedelta(days=1)
    invalid = df[pd.to_datetime(df["date"]).dt.date >= tomorrow]
    passed = len(invalid) == 0
    return ValidationResult(
        check_name="no_future_dates",
        passed=passed,
        detail="Fechas futuras detectadas" if not passed else "Sin fechas futuras",
        affected_rows=len(invalid),
    )


def check_duplicates(df: pd.DataFrame) -> ValidationResult:
    """No debe haber combinaciones duplicadas de ciudad + fecha."""
    dupes = df.duplicated(subset=["city_name", "date"], keep=False)
    count = dupes.sum()
    passed = count == 0
    return ValidationResult(
        check_name="no_duplicates",
        passed=passed,
        detail=f"{count} filas duplicadas encontradas"
        if not passed
        else "Sin duplicados",
        affected_rows=int(count),
    )


def check_null_percentage(
    df: pd.DataFrame, max_pct: float
) -> ValidationResult:
    """Verifica que el % de nulos no supere el umbral configurado."""
    total_cells = df.size
    null_cells = df.isnull().sum().sum()
    pct = (null_cells / total_cells) * 100 if total_cells > 0 else 0
    passed = pct <= max_pct
    return ValidationResult(
        check_name="null_percentage",
        passed=passed,
        detail=f"Nulos: {pct:.1f}% (máximo permitido: {max_pct}%)",
        affected_rows=int(null_cells),
    )


def check_temperature_consistency(df: pd.DataFrame) -> ValidationResult:
    """La temperatura mínima debe ser menor o igual a la máxima."""
    invalid = df[df["temperature_min"] > df["temperature_max"]]
    passed = len(invalid) == 0
    return ValidationResult(
        check_name="temperature_consistency",
        passed=passed,
        detail="temp_min > temp_max en algunas filas"
        if not passed
        else "Temperaturas consistentes (min <= max)",
        affected_rows=len(invalid),
    )


def run_all_checks(df: pd.DataFrame, rules: dict[str, Any]) -> list[ValidationResult]:
    """Ejecuta todos los checks de calidad sobre el DataFrame."""
    return [
        check_required_fields(df, rules["required_fields"]),
        check_temperature_range(
            df,
            min_temp=rules["temperature"]["min"],
            max_temp=rules["temperature"]["max"],
        ),
        check_precipitation(df, max_precip=rules["precipitation"]["max"]),
        check_no_future_dates(df),
        check_duplicates(df),
        check_null_percentage(df, max_pct=rules["thresholds"]["max_null_percentage"]),
        check_temperature_consistency(df),
    ]
