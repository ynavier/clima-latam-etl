-- Modelo staging: limpia y estandariza desde la tabla raw de BigQuery.
-- Materializado como VIEW — no ocupa storage, siempre refleja datos actuales.

WITH source AS (
    SELECT * FROM {{ source('weather_clean', 'fact_weather') }}
),

renamed AS (
    SELECT
        -- Dimensiones
        date,
        city_name,
        country,
        country_code,
        region,
        ROUND(latitude, 4)  AS latitude,
        ROUND(longitude, 4) AS longitude,
        timezone,

        -- Temperatura
        temperature_max,
        temperature_min,
        temperature_mean,
        temperature_range,
        temperature_category,

        -- Precipitación
        COALESCE(precipitation_sum, 0)   AS precipitation_sum,
        COALESCE(precipitation_hours, 0) AS precipitation_hours,
        precipitation_category,

        -- Viento
        wind_speed_max,
        wind_direction,

        -- Humedad
        humidity_max,
        humidity_min,
        humidity_mean,

        -- Índices
        uv_index_max,
        weather_code,
        weather_description,

        -- Metadata
        loaded_at

    FROM source
    WHERE date IS NOT NULL
      AND city_name IS NOT NULL
)

SELECT * FROM renamed
