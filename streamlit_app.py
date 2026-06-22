"""Minimal diagnostic app for Streamlit Cloud."""
import traceback
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Clima LATAM — Diagnostico", layout="wide")

DATA_DIR = Path(__file__).parent / "data"

st.title("Clima LATAM")
st.write(f"DATA_DIR: `{DATA_DIR}`")
st.write(f"Existe: `{DATA_DIR.exists()}`")

try:
    files = sorted(DATA_DIR.glob("clean/**/*.csv"))
    st.write(f"CSV encontrados: `{len(files)}`")
    for f in files:
        st.write(f"  - `{f}`")

    if files:
        df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
        df["date"] = pd.to_datetime(df["date"])
        st.success(f"Datos cargados: {len(df):,} filas, {df['city_name'].nunique()} ciudades")
        st.dataframe(df.head(10))
    else:
        st.error("No se encontraron archivos CSV")

except Exception:
    st.error("Error:")
    st.code(traceback.format_exc())
