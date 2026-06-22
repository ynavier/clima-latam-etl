"""
Configuración del pipeline cargada desde variables de entorno.
Falla al inicio si faltan variables críticas — mejor que fallar a mitad de una carga.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class PipelineConfig:
    """Configuración inmutable del pipeline."""

    project_id: str
    environment: str

    bq_dataset_raw: str
    bq_dataset_clean: str
    bq_dataset_mart: str

    max_retries: int
    api_request_timeout: int

    cities_file: Path
    quality_rules_file: Path

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Crea la configuración desde variables de entorno. Falla si faltan variables críticas."""
        project_id = os.getenv("GCP_PROJECT_ID", "")
        if not project_id:
            raise ValueError(
                "GCP_PROJECT_ID no está definido.\n"
                "Copia .env.example como .env y completa el valor."
            )

        base_dir = Path(__file__).parent.parent.parent.parent

        return cls(
            project_id=project_id,
            environment=os.getenv("ENVIRONMENT", "local"),
            bq_dataset_raw=os.getenv("BQ_DATASET_RAW", "weather_raw"),
            bq_dataset_clean=os.getenv("BQ_DATASET_CLEAN", "weather_clean"),
            bq_dataset_mart=os.getenv("BQ_DATASET_MART", "weather_mart"),
            max_retries=int(os.getenv("PIPELINE_MAX_RETRIES", "3")),
            api_request_timeout=int(os.getenv("API_REQUEST_TIMEOUT", "30")),
            cities_file=base_dir / "config" / "cities_latam.yaml",
            quality_rules_file=base_dir / "config" / "quality_rules.yaml",
        )
