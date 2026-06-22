"""
Carga de datos a BigQuery.
Compatible con BigQuery Sandbox (sin billing) y BigQuery de pago.
"""
from pathlib import Path
from typing import Any

import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from src.pipeline.utils.logger import get_logger

logger = get_logger(__name__)

# Schema de la tabla principal en BigQuery
WEATHER_SCHEMA = [
    bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
    bigquery.SchemaField("city_name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("country", "STRING"),
    bigquery.SchemaField("country_code", "STRING"),
    bigquery.SchemaField("region", "STRING"),
    bigquery.SchemaField("latitude", "FLOAT64"),
    bigquery.SchemaField("longitude", "FLOAT64"),
    bigquery.SchemaField("timezone", "STRING"),
    bigquery.SchemaField("temperature_max", "FLOAT64"),
    bigquery.SchemaField("temperature_min", "FLOAT64"),
    bigquery.SchemaField("temperature_mean", "FLOAT64"),
    bigquery.SchemaField("temperature_range", "FLOAT64"),
    bigquery.SchemaField("precipitation_sum", "FLOAT64"),
    bigquery.SchemaField("precipitation_hours", "FLOAT64"),
    bigquery.SchemaField("precipitation_category", "STRING"),
    bigquery.SchemaField("wind_speed_max", "FLOAT64"),
    bigquery.SchemaField("wind_direction", "FLOAT64"),
    bigquery.SchemaField("humidity_max", "FLOAT64"),
    bigquery.SchemaField("humidity_min", "FLOAT64"),
    bigquery.SchemaField("humidity_mean", "FLOAT64"),
    bigquery.SchemaField("uv_index_max", "FLOAT64"),
    bigquery.SchemaField("weather_code", "INT64"),
    bigquery.SchemaField("weather_description", "STRING"),
    bigquery.SchemaField("temperature_category", "STRING"),
    bigquery.SchemaField("sunrise", "STRING"),
    bigquery.SchemaField("sunset", "STRING"),
    bigquery.SchemaField("loaded_at", "TIMESTAMP"),
]


class BigQueryLoader:
    """Maneja todas las operaciones de carga a BigQuery."""

    def __init__(self, project_id: str, dataset_id: str) -> None:
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = f"{project_id}.{dataset_id}.fact_weather"

    def ensure_dataset_exists(self) -> None:
        """Crea el dataset si no existe."""
        dataset_ref = bigquery.Dataset(f"{self.project_id}.{self.dataset_id}")
        dataset_ref.location = "US"
        try:
            self.client.get_dataset(dataset_ref)
        except NotFound:
            self.client.create_dataset(dataset_ref)
            logger.info(f"Dataset creado: {self.dataset_id}")

    def ensure_table_exists(self) -> None:
        """
        Crea la tabla con particionado por fecha si no existe.
        Particionamos por 'date' porque la mayoría de queries filtran por fecha.
        Esto reduce significativamente el costo y la latencia de las queries.
        """
        try:
            self.client.get_table(self.table_id)
        except NotFound:
            table = bigquery.Table(self.table_id, schema=WEATHER_SCHEMA)

            # Particionado por día en el campo 'date'
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="date",
            )

            # Clustering: ordena físicamente los datos por estas columnas
            # Acelera queries que filtran por country_code o city_name
            table.clustering_fields = ["country_code", "city_name"]

            self.client.create_table(table)
            logger.info(f"Tabla creada con particionado: {self.table_id}")

    def load_dataframe(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Carga el DataFrame a BigQuery.

        Usamos WRITE_TRUNCATE con el patrón de partición para hacer upsert seguro:
        solo sobreescribimos las particiones del día actual, no toda la tabla.
        """
        from datetime import datetime, timezone

        df = df.copy()
        df["loaded_at"] = datetime.now(timezone.utc)
        df["date"] = pd.to_datetime(df["date"])

        job_config = bigquery.LoadJobConfig(
            schema=WEATHER_SCHEMA,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
        )

        job = self.client.load_table_from_dataframe(
            df, self.table_id, job_config=job_config
        )
        job.result()  # Espera a que termine

        table = self.client.get_table(self.table_id)
        logger.info(
            f"Carga exitosa — {job.output_rows} filas cargadas. "
            f"Total en tabla: {table.num_rows}"
        )

        return {
            "rows_loaded": job.output_rows,
            "table_total_rows": table.num_rows,
            "job_id": job.job_id,
        }

    def run(self, df: pd.DataFrame) -> dict[str, Any]:
        """Orquesta la carga completa: dataset → tabla → datos."""
        self.ensure_dataset_exists()
        self.ensure_table_exists()
        return self.load_dataframe(df)
