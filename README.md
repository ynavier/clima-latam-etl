# Clima LATAM — Pipeline ETL End-to-End

Sistema de monitoreo climatico para America Latina que extrae, valida, transforma y visualiza datos de 100 ciudades usando una arquitectura ETL profesional sobre Google Cloud Platform.

**Demo en vivo:** [climalatam.streamlit.app](https://climalatam.streamlit.app)

---

## Arquitectura

```
Open-Meteo API (100 ciudades · sin costo · sin API key)
        ↓  httpx async · retry con backoff exponencial
    Extract  →  data/raw/YYYY/MM/DD/weather_raw.json       Bronze
        ↓
    Validate →  quality_report.json · 7 checks de calidad
        ↓
    Transform → data/clean/YYYY/MM/DD/weather_clean.csv    Silver
        ↓
    Load      → BigQuery · particionado por fecha · clustering por ciudad
        ↓
    dbt       → mart_daily_summary · mart_city_stats        Gold
        ↓
    Dashboard → Streamlit · globo terraqueo 3D · GSAP · Plotly
```

---

## Tecnologias

| Capa | Herramienta | Uso |
|---|---|---|
| Extraccion | Python + httpx | 100 ciudades en paralelo con async |
| Validacion | Reglas propias | 7 checks: nulos, rangos, duplicados, fechas |
| Transformacion | pandas | Limpieza, normalizacion, columnas derivadas |
| Almacenamiento | Google BigQuery | DW particionado + clustering |
| Transformacion SQL | dbt | Modelos staging y marts analiticos |
| Dashboard | Streamlit + Plotly | 3 tabs, globo 3D, glassmorphism, GSAP |
| CI/CD | GitHub Actions | Lint + tests en cada push |

---

## Dashboard

El dashboard tiene 3 secciones:

**Monitor Global**
- Globo terraqueo 3D interactivo con temperatura por pais (choropleth)
- Panel de navegacion para hacer fly-to a cualquier ciudad
- Condiciones actuales con gauges animados en Canvas
- Lista de ciudades mas calurosas del dia
- Lluvia acumulada por pais (ultimos 30 dias)

**Analisis por Ciudad**
- Selector de ciudad y rango de fechas
- Tendencia de temperatura (max / media / min)
- Precipitacion diaria y viento
- Panel de condiciones con indicadores UV, humedad y lluvia

**Pipeline / Calidad**
- Estado de cada check de calidad (PASS / FAIL)
- Metricas: total de registros, % validos, % nulos
- Historial de ejecuciones
- Arquitectura del pipeline

---

## Estructura del proyecto

```
clima-latam-etl/
├── src/
│   ├── pipeline/
│   │   ├── extract/        # Cliente API Open-Meteo
│   │   ├── validate/       # Reglas de calidad de datos
│   │   ├── transform/      # Limpieza y enriquecimiento
│   │   ├── load/           # Carga a BigQuery
│   │   └── utils/          # Config, logger
│   └── dashboard/
│       └── app.py          # Dashboard Streamlit
├── dbt/
│   └── models/
│       ├── staging/        # Vistas de staging
│       └── marts/          # Tablas analiticas
├── config/
│   ├── cities_latam.yaml   # 100 ciudades con coordenadas
│   └── quality_rules.yaml  # Reglas de validacion
├── tests/
│   └── unit/               # 25 tests unitarios
├── .github/workflows/      # CI con GitHub Actions
├── streamlit_app.py        # Entry point para deploy
└── requirements.txt
```

---

## Ejecutar localmente

```bash
# 1. Clonar el repositorio
git clone https://github.com/ynavier/clima-latam-etl.git
cd clima-latam-etl

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Autenticarse con Google (para BigQuery Sandbox)
gcloud auth application-default login

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu GCP_PROJECT_ID

# 5. Ejecutar el pipeline
python -m src.pipeline.extract.main
python -m src.pipeline.validate.main
python -m src.pipeline.transform.main

# 6. Abrir el dashboard
streamlit run streamlit_app.py
```

---

## Calidad de datos

El modulo de validacion ejecuta 7 checks automaticos antes de cargar a BigQuery:

| Check | Descripcion |
|---|---|
| required_fields | Todos los campos obligatorios presentes |
| temperature_range | Temperaturas entre -80°C y 60°C |
| precipitation_range | Precipitacion entre 0 y 500 mm |
| no_future_dates | Sin fechas posteriores a hoy |
| no_duplicates | Sin combinaciones ciudad + fecha duplicadas |
| null_percentage | Maximo 10% de valores nulos |
| temperature_consistency | temp_min <= temp_max siempre |

Genera un `quality_report.json` con metricas detalladas por ejecucion.

---

## Tests

```bash
# Ejecutar los 25 tests unitarios
pytest tests/ -v --cov=src
```

Cobertura de los modulos de validacion y transformacion.

---

## Variables de entorno

```bash
GCP_PROJECT_ID=tu-project-id
ENVIRONMENT=local
BQ_DATASET_RAW=weather_raw
BQ_DATASET_CLEAN=weather_clean
BQ_DATASET_MART=weather_mart
```

---

## Ciudades monitoreadas

100 ciudades de 22 paises de America Latina incluyendo:
Mexico, Guatemala, El Salvador, Honduras, Nicaragua, Costa Rica, Panama,
Colombia, Venezuela, Ecuador, Peru, Bolivia, Chile, Argentina, Paraguay,
Uruguay, Brasil, Cuba, Rep. Dominicana, Puerto Rico, Haiti, Jamaica.

---

## Autor

**Yoriel Vidal** · [LinkedIn](https://linkedin.com/in/yoriel-vidal) · [Portafolio](https://ynavier.github.io)
