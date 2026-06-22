-- Mart: estadísticas agregadas por ciudad (últimos 30 días).
-- Alimenta la página de comparativa entre ciudades del dashboard.

WITH base AS (
    SELECT * FROM {{ ref('stg_weather') }}
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
),

city_stats AS (
    SELECT
        city_name,
        country,
        country_code,
        region,
        latitude,
        longitude,

        -- Temperatura promedio del período
        ROUND(AVG(temperature_mean), 1)  AS avg_temperature,
        ROUND(MAX(temperature_max), 1)   AS max_temperature,
        ROUND(MIN(temperature_min), 1)   AS min_temperature,

        -- Precipitación total y días de lluvia
        ROUND(SUM(precipitation_sum), 1)  AS total_precipitation,
        COUNTIF(precipitation_sum > 0)    AS rainy_days,
        COUNT(*)                          AS total_days,

        -- Viento
        ROUND(AVG(wind_speed_max), 1)    AS avg_wind_speed,
        ROUND(MAX(wind_speed_max), 1)    AS max_wind_speed,

        -- Humedad
        ROUND(AVG(humidity_mean), 1)     AS avg_humidity,

        -- UV
        ROUND(AVG(uv_index_max), 1)      AS avg_uv_index,

        -- Alertas
        COUNTIF(heavy_rain_day)          AS heavy_rain_days,
        COUNTIF(heat_alert_day)          AS heat_alert_days,

        -- Clima más frecuente
        APPROX_TOP_COUNT(weather_description, 1)[OFFSET(0)].value AS most_common_weather

    FROM {{ ref('mart_daily_summary') }}
    GROUP BY
        city_name, country, country_code, region, latitude, longitude
)

SELECT
    *,
    ROUND(rainy_days / NULLIF(total_days, 0) * 100, 1) AS rain_percentage
FROM city_stats
ORDER BY avg_temperature DESC
