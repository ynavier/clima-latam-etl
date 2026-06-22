"""
Entry point del módulo de carga.
Lee el CSV limpio y lo carga a BigQuery.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.pipeline.utils.config import PipelineConfig
from src.pipeline.utils.logger import get_logger
from .bq_loader import BigQueryLoader

logger = get_logger(__name__)


def run(config: PipelineConfig, clean_file: Path) -> dict:
    """Ejecuta la carga a BigQuery."""
    start = datetime.now(timezone.utc)
    logger.info("=== INICIO: Módulo de Carga ===")

    df = pd.read_csv(clean_file, encoding="utf-8")
    logger.info(f"Filas a cargar: {len(df)}")

    loader = BigQueryLoader(
        project_id=config.project_id,
        dataset_id=config.bq_dataset_clean,
    )

    result = loader.run(df)

    duration = (datetime.now(timezone.utc) - start).total_seconds()
    logger.info(f"=== FIN: Carga completada en {duration:.1f}s ===")

    return result


def main() -> None:
    config = PipelineConfig.from_env()
    data_dir = config.cities_file.parent.parent / "data"
    today = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    clean_file = data_dir / "clean" / today / "weather_clean.csv"

    if not clean_file.exists():
        logger.error(f"Archivo limpio no encontrado: {clean_file}")
        sys.exit(1)

    run(config, clean_file)


if __name__ == "__main__":
    main()
