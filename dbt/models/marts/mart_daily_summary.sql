-- Mart: resumen diario por ciudad.
-- Materializado como TABLE — se recalcula en cada dbt run.
-- Base del dashboard: Resumen Ejecutivo y Análisis por Ciudad.

WITH base AS (
    SELECT * FROM {{ ref('stg_weather') }}
),

daily AS (
    SELECT
        date,
        city_name,
        country,
        country_code,
        region,
        latitude,
        longitude,

        -- KPIs de temperatura
        temperature_max,
        temperature_min,
        temperature_mean,
        temperature_range,
        temperature_category,

        -- KPIs de lluvia
        precipitation_sum,
        precipitation_hours,
        precipitation_category,

        -- Viento y humedad
        wind_speed_max,
        humidity_mean,
        uv_index_max,

        -- Descripción del clima
        weather_description,

        -- Métricas calculadas
        CASE
            WHEN precipitation_sum > 20  THEN TRUE
            ELSE FALSE
        END AS heavy_rain_day,

        CASE
            WHEN temperature_max > 35 THEN TRUE
            ELSE FALSE
        END AS heat_alert_day,

        CASE
            WHEN wind_speed_max > 60 THEN TRUE
            ELSE FALSE
        END AS wind_alert_day

    FROM base
)

SELECT * FROM daily
