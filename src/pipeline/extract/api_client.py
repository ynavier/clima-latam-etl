"""
Cliente HTTP para la API de Open-Meteo.
Documentación: https://open-meteo.com/en/docs

Open-Meteo es gratuita, sin API key, sin rate limiting estricto.
Usamos httpx con async para pedir las 100 ciudades en paralelo
en lugar de secuencialmente (100x más rápido).
"""
import asyncio
from datetime import date, timedelta
from typing import Any

import httpx

from src.pipeline.utils.logger import get_logger

logger = get_logger(__name__)

# URL base de Open-Meteo
BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Variables que pedimos por ciudad
# Documentación: https://open-meteo.com/en/docs#weathervariables
DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "precipitation_hours",
    "wind_speed_10m_max",
    "wind_direction_10m_dominant",
    "relative_humidity_2m_max",
    "relative_humidity_2m_min",
    "uv_index_max",
    "weather_code",
    "sunrise",
    "sunset",
]


def build_request_params(
    latitude: float,
    longitude: float,
    timezone: str,
    days_back: int = 7,
) -> dict[str, Any]:
    """
    Construye los parámetros de la request para una ciudad.

    Args:
        latitude: Latitud de la ciudad
        longitude: Longitud de la ciudad
        timezone: Zona horaria (ej: 'America/Lima')
        days_back: Cuántos días hacia atrás pedir (default: 7)

    Returns:
        Diccionario de parámetros para la URL
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": timezone,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }


async def fetch_city_weather(
    client: httpx.AsyncClient,
    city: dict[str, Any],
    days_back: int = 7,
    max_retries: int = 3,
) -> dict[str, Any] | None:
    """
    Pide datos climáticos de una ciudad a Open-Meteo.

    Implementa retry con backoff exponencial:
    - Intento 1: inmediato
    - Intento 2: espera 2 segundos
    - Intento 3: espera 4 segundos

    Args:
        client: Cliente HTTP compartido (más eficiente que crear uno por request)
        city: Diccionario con datos de la ciudad del YAML
        days_back: Días hacia atrás a solicitar
        max_retries: Intentos máximos antes de considerar fallida

    Returns:
        Respuesta JSON de la API, o None si fallaron todos los intentos
    """
    params = build_request_params(
        latitude=city["latitude"],
        longitude=city["longitude"],
        timezone=city["timezone"],
        days_back=days_back,
    )

    for attempt in range(1, max_retries + 1):
        try:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()

            data = response.json()

            # Open-Meteo retorna error en el cuerpo JSON a veces
            if "error" in data:
                raise ValueError(f"API error: {data.get('reason', 'unknown')}")

            logger.debug(f"OK: {city['name']} ({city['country_code']})")
            return {**data, "_city_meta": city}

        except httpx.TimeoutException:
            logger.warning(
                f"Timeout en {city['name']} — intento {attempt}/{max_retries}"
            )
        except httpx.HTTPStatusError as e:
            logger.warning(
                f"HTTP {e.response.status_code} en {city['name']} — "
                f"intento {attempt}/{max_retries}"
            )
        except Exception as e:
            logger.warning(
                f"Error inesperado en {city['name']}: {e} — "
                f"intento {attempt}/{max_retries}"
            )

        if attempt < max_retries:
            wait = 2 ** (attempt - 1)  # 1s, 2s, 4s
            await asyncio.sleep(wait)

    logger.error(f"Fallaron todos los intentos para {city['name']}")
    return None


async def fetch_all_cities(
    cities: list[dict[str, Any]],
    days_back: int = 7,
    max_retries: int = 3,
    timeout: int = 30,
    concurrency: int = 20,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Pide datos de todas las ciudades en paralelo con límite de concurrencia.

    Por qué limitamos la concurrencia a 20:
    - Evitamos abrumar la API (aunque Open-Meteo no tiene rate limit estricto)
    - Controlamos el uso de memoria
    - 20 requests simultáneas es más que suficiente para ser rápidos

    Args:
        cities: Lista de ciudades del YAML
        days_back: Días hacia atrás
        max_retries: Intentos por ciudad
        timeout: Timeout en segundos por request
        concurrency: Máximo de requests simultáneas

    Returns:
        Tuple de (resultados_exitosos, nombres_fallidos)
    """
    logger.info(f"Iniciando extracción de {len(cities)} ciudades...")

    semaphore = asyncio.Semaphore(concurrency)

    async def fetch_with_semaphore(city: dict[str, Any]) -> dict[str, Any] | None:
        async with semaphore:
            return await fetch_city_weather(
                client=client,
                city=city,
                days_back=days_back,
                max_retries=max_retries,
            )

    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [fetch_with_semaphore(city) for city in cities]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    successful = [r for r in results if r is not None]
    failed = [
        cities[i]["name"]
        for i, r in enumerate(results)
        if r is None
    ]

    logger.info(
        f"Extracción completa — "
        f"exitosas: {len(successful)}, "
        f"fallidas: {len(failed)}"
    )

    if failed:
        logger.warning(f"Ciudades fallidas: {failed}")

    return successful, failed
