"""
Entry point del módulo de extracción.
Orquesta la lectura de ciudades y la llamada a la API.
"""
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.pipeline.utils.config import PipelineConfig
from src.pipeline.utils.logger import get_logger
from .api_client import fetch_all_cities

logger = get_logger(__name__)


def load_cities(cities_file: Path) -> list[dict[str, Any]]:
    """Carga la lista de ciudades desde el archivo YAML."""
    with open(cities_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    cities = data["cities"]
    logger.info(f"Cargadas {len(cities)} ciudades desde {cities_file.name}")
    return cities


def save_raw_data(
    results: list[dict[str, Any]],
    failed: list[str],
    output_dir: Path,
) -> Path:
    """
    Guarda los datos crudos en formato JSON con estructura de partición por fecha.
    Patrón: raw/YYYY/MM/DD/weather_raw.json

    Así mantenemos historial completo y podemos reprocesar días anteriores.
    """
    now = datetime.now(timezone.utc)
    partition_dir = output_dir / "raw" / now.strftime("%Y/%m/%d")
    partition_dir.mkdir(parents=True, exist_ok=True)

    output_file = partition_dir / "weather_raw.json"

    payload = {
        "extraction_timestamp": now.isoformat(),
        "total_cities_requested": len(results) + len(failed),
        "total_cities_successful": len(results),
        "total_cities_failed": len(failed),
        "failed_cities": failed,
        "data": results,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info(f"Datos crudos guardados en: {output_file}")
    return output_file


async def run(config: PipelineConfig, output_dir: Path | None = None) -> Path:
    """
    Ejecuta el paso de extracción completo.

    Args:
        config: Configuración del pipeline
        output_dir: Directorio de salida (por defecto: data/ en la raíz)

    Returns:
        Path al archivo JSON generado
    """
    start = datetime.now(timezone.utc)
    logger.info("=== INICIO: Módulo de Extracción ===")

    cities = load_cities(config.cities_file)

    results, failed = await fetch_all_cities(
        cities=cities,
        days_back=7,
        max_retries=config.max_retries,
        timeout=config.api_request_timeout,
    )

    if not results:
        raise RuntimeError("No se obtuvo ningún resultado de la API. Abortando.")

    if output_dir is None:
        output_dir = config.cities_file.parent.parent / "data"

    output_file = save_raw_data(results, failed, output_dir)

    duration = (datetime.now(timezone.utc) - start).total_seconds()
    logger.info(f"=== FIN: Extracción completada en {duration:.1f}s ===")

    return output_file


def main() -> None:
    """Entry point para ejecución directa: python -m src.pipeline.extract.main"""
    config = PipelineConfig.from_env()
    try:
        asyncio.run(run(config))
    except Exception as e:
        logger.error(f"Error crítico en extracción: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
