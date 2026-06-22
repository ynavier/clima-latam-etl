"""
Entry point del módulo de validación.
Lee los datos crudos, ejecuta los checks y genera el quality_report.json.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.pipeline.utils.config import PipelineConfig
from src.pipeline.utils.logger import get_logger
from .rules import QualityReport, load_rules, run_all_checks

logger = get_logger(__name__)


def flatten_raw_data(raw_file: Path) -> pd.DataFrame:
    """
    Convierte el JSON crudo de Open-Meteo a un DataFrame tabular.

    Open-Meteo devuelve arrays paralelos por variable:
    {
        "daily": {
            "time": ["2024-01-01", "2024-01-02", ...],
            "temperature_2m_max": [28.1, 27.5, ...],
            ...
        }
    }
    Necesitamos convertir esto a filas: una fila por ciudad por día.
    """
    with open(raw_file, encoding="utf-8") as f:
        raw = json.load(f)

    rows = []
    for city_data in raw["data"]:
        meta = city_data["_city_meta"]
        daily = city_data.get("daily", {})

        if not daily or "time" not in daily:
            logger.warning(f"Sin datos diarios para {meta['name']}")
            continue

        dates = daily["time"]
        for i, date_str in enumerate(dates):
            rows.append({
                "date": date_str,
                "city_name": meta["name"],
                "country": meta["country"],
                "country_code": meta["country_code"],
                "region": meta["region"],
                "latitude": meta["latitude"],
                "longitude": meta["longitude"],
                "timezone": meta["timezone"],
                "temperature_max": _safe_get(daily, "temperature_2m_max", i),
                "temperature_min": _safe_get(daily, "temperature_2m_min", i),
                "temperature_mean": _safe_get(daily, "temperature_2m_mean", i),
                "precipitation_sum": _safe_get(daily, "precipitation_sum", i),
                "precipitation_hours": _safe_get(daily, "precipitation_hours", i),
                "wind_speed_max": _safe_get(daily, "wind_speed_10m_max", i),
                "wind_direction": _safe_get(daily, "wind_direction_10m_dominant", i),
                "humidity_max": _safe_get(daily, "relative_humidity_2m_max", i),
                "humidity_min": _safe_get(daily, "relative_humidity_2m_min", i),
                "uv_index_max": _safe_get(daily, "uv_index_max", i),
                "weather_code": _safe_get(daily, "weather_code", i),
                "sunrise": _safe_get(daily, "sunrise", i),
                "sunset": _safe_get(daily, "sunset", i),
            })

    df = pd.DataFrame(rows)
    logger.info(f"DataFrame construido: {len(df)} filas, {len(df.columns)} columnas")
    return df


def _safe_get(data: dict, key: str, index: int) -> object:
    """Obtiene un valor de un array de forma segura, retorna None si no existe."""
    values = data.get(key)
    if values is None or index >= len(values):
        return None
    return values[index]


def run(config: PipelineConfig, raw_file: Path, output_dir: Path) -> tuple[pd.DataFrame, QualityReport]:
    """
    Ejecuta el módulo de validación completo.

    Returns:
        Tuple de (DataFrame validado, reporte de calidad)
    """
    start = datetime.now(timezone.utc)
    logger.info("=== INICIO: Módulo de Validación ===")

    df = flatten_raw_data(raw_file)
    rules = load_rules(str(config.quality_rules_file))
    checks = run_all_checks(df, rules)

    # Calcular métricas del reporte
    null_pct = (df.isnull().sum().sum() / df.size * 100) if df.size > 0 else 0
    dupe_count = int(df.duplicated(subset=["city_name", "date"]).sum())

    # Filas inválidas = filas afectadas por algún check fallido
    invalid_rows = max(c.affected_rows for c in checks if not c.passed) if any(not c.passed for c in checks) else 0

    report = QualityReport(
        extraction_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        total_rows=len(df),
        valid_rows=len(df) - invalid_rows,
        invalid_rows=invalid_rows,
        null_percentage=null_pct,
        duplicate_count=dupe_count,
        checks=checks,
    )

    # Guardar reporte
    report_dir = output_dir / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"quality_report_{report.extraction_date}.json"

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

    # Log de resultados
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        logger.info(f"  [{status}] {check.check_name}: {check.detail}")

    if report.overall_passed:
        logger.info(f"Calidad OK — {report.valid_rows}/{report.total_rows} filas válidas")
    else:
        logger.warning(f"Calidad con alertas — {report.invalid_rows} filas con problemas")

    duration = (datetime.now(timezone.utc) - start).total_seconds()
    logger.info(f"=== FIN: Validación completada en {duration:.1f}s ===")

    return df, report


def main() -> None:
    config = PipelineConfig.from_env()
    data_dir = config.cities_file.parent.parent / "data"
    today = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    raw_file = data_dir / "raw" / today / "weather_raw.json"

    if not raw_file.exists():
        logger.error(f"Archivo crudo no encontrado: {raw_file}")
        sys.exit(1)

    run(config, raw_file, data_dir)


if __name__ == "__main__":
    main()
