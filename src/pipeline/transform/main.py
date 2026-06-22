"""
Entry point del módulo de transformación.
Toma el DataFrame validado y produce un CSV limpio listo para cargar.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.pipeline.utils.config import PipelineConfig
from src.pipeline.utils.logger import get_logger
from .cleaner import clean

logger = get_logger(__name__)


def run(config: PipelineConfig, df: pd.DataFrame, output_dir: Path) -> Path:
    """
    Ejecuta el módulo de transformación.

    Args:
        config: Configuración del pipeline
        df: DataFrame validado del paso anterior
        output_dir: Directorio donde guardar el resultado

    Returns:
        Path al archivo CSV limpio generado
    """
    start = datetime.now(timezone.utc)
    logger.info("=== INICIO: Módulo de Transformación ===")

    df_clean = clean(df)

    # Guardar con partición por fecha
    today = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    clean_dir = output_dir / "clean" / today
    clean_dir.mkdir(parents=True, exist_ok=True)

    output_file = clean_dir / "weather_clean.csv"
    df_clean.to_csv(output_file, index=False, encoding="utf-8")

    duration = (datetime.now(timezone.utc) - start).total_seconds()
    logger.info(f"CSV limpio guardado: {output_file} ({len(df_clean)} filas)")
    logger.info(f"=== FIN: Transformación completada en {duration:.1f}s ===")

    return output_file


def main() -> None:
    """Entry point para ejecución directa."""
    from src.pipeline.validate.main import flatten_raw_data

    config = PipelineConfig.from_env()
    data_dir = config.cities_file.parent.parent / "data"
    today = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    raw_file = data_dir / "raw" / today / "weather_raw.json"

    if not raw_file.exists():
        logger.error(f"Archivo crudo no encontrado: {raw_file}")
        sys.exit(1)

    df = flatten_raw_data(raw_file)
    run(config, df, data_dir)


if __name__ == "__main__":
    main()
