"""Funciones compartidas por todas las páginas de la app."""
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import streamlit as st

DATOS = Path(__file__).parent / "data"
FECHA_FUTURO = "2024-02-01"          # el "mañana": sin datos reales
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
VERDE, ROJO = "#2d6a6a", "#b03a3a"
PALETA = ["#2d6a6a", "#d98c3a", "#b03a3a", "#4a7fb5", "#7b5ea7", "#8a8a8a", "#c9b037"]
COLORES_BADGE = ["green", "orange", "red", "blue", "violet", "gray", "yellow"]


# ---------- API ----------
def api_url() -> str:
    """La dirección de la API vive en st.secrets (no en el código)."""
    try:
        return str(st.secrets["API_URL"]).rstrip("/")
    except Exception:
        return "http://localhost:8000"


@st.cache_data(ttl=3600, show_spinner=False)
def _pedir(url: str, params: tuple):
    """Una sola llamada a la API por consulta (se guarda 1 hora)."""
    r = requests.get(url, params=dict(params), timeout=90)   # 90 s: Render tarda en despertar
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=60, show_spinner=False)
def api_en_linea(url: str) -> bool:
    try:
        return requests.get(url + "/", timeout=5).ok
    except requests.RequestException:
        return False


def cargar(ruta: str, **params):
    """Pide datos a la API. Si falla, explica con un mensaje claro y detiene la página."""
    estado = st.status("Conectando con la API...", expanded=False)
    try:
        datos = _pedir(api_url() + ruta, tuple(sorted(params.items())))
        estado.update(label="API conectada", state="complete")
        return datos
    except requests.HTTPError as e:
        estado.update(label="La API respondió con un error", state="error")
        detalle = ""
        try:
            detalle = e.response.json().get("detail", "")
        except Exception:
            pass
        st.error(f"La API respondió con un error ({e.response.status_code}). {detalle}",
                 icon=":material/error:")
    except requests.RequestException:
        estado.update(label="Sin conexión con la API", state="error")
        st.error(f"No se pudo conectar con la API en {api_url()}. "
                 "Si está en Render, puede estar despertando: espera un minuto y recarga.",
                 icon=":material/cloud_off:")
    st.stop()


# ---------- Archivos locales (los genera el notebook) ----------
@st.cache_data
def _leer_csv(nombre):
    return pd.read_csv(DATOS / nombre)


@st.cache_data
def _leer_json(nombre):
    return json.loads((DATOS / nombre).read_text(encoding="utf-8"))


def _aviso_falta(nombre):
    st.error(f"Falta el archivo app/data/{nombre}. Corran preparacion.ipynb y copien la carpeta app/data.",
             icon=":material/folder_off:")
    st.stop()


def leer_csv(nombre):
    try:
        return _leer_csv(nombre)
    except FileNotFoundError:
        _aviso_falta(nombre)


def leer_json(nombre):
    try:
        return _leer_json(nombre)
    except FileNotFoundError:
        _aviso_falta(nombre)


# ---------- Utilidades ----------
def etiqueta_fecha(f: str) -> str:
    d = date.fromisoformat(f)
    return f"{DIAS[d.weekday()]} {d.day}" + (" (mañana)" if f == FECHA_FUTURO else "")


def selector_zona_fecha(info: dict):
    """Zona + fecha. Se recuerdan al cambiar de página (session_state) y en el link (query_params)."""
    zonas = {int(z["id"]): f'{z["nombre"]} ({z["distrito"]})' for z in info["zonas"]}
    ids = list(zonas)
    try:
        zona_def = st.session_state.get("zona_id") or int(st.query_params.get("zona", ids[0]))
    except (TypeError, ValueError):
        zona_def = ids[0]
    if zona_def not in ids:
        zona_def = ids[0]
    zona_id = st.selectbox("Zona", ids, index=ids.index(zona_def), format_func=zonas.get)

    fechas = info["fechas"]
    fecha_def = st.session_state.get("fecha") or st.query_params.get("fecha", fechas[0])
    if fecha_def not in fechas:
        fecha_def = fechas[0]
    fecha = st.segmented_control("Fecha", fechas, default=fecha_def,
                                 format_func=etiqueta_fecha, selection_mode="single") or fecha_def

    st.session_state["zona_id"], st.session_state["fecha"] = zona_id, fecha
    st.query_params["zona"], st.query_params["fecha"] = str(zona_id), fecha
    return zona_id, fecha, zonas[zona_id]


def a_dataframe(datos: dict) -> pd.DataFrame:
    """Convierte la respuesta de /pronostico en una tabla: hora, real, hace_una_semana, p10..p90."""
    filas = []
    for h in datos["horas"]:
        fila = {"hora": h["hora"], "real": h.get("real"), "hace_una_semana": h.get("hace_una_semana")}
        fila.update(h["cuantiles"])
        filas.append(fila)
    df = pd.DataFrame(filas)
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def columnas_cuantiles(df: pd.DataFrame):
    cols = sorted([c for c in df.columns if c.startswith("p") and c[1:].isdigit()], key=lambda c: int(c[1:]))
    return cols, np.array([int(c[1:]) / 100 for c in cols])


def costo(enviados, real, costo_ocioso, costo_perdido) -> float:
    enviados, real = np.asarray(enviados, float), np.asarray(real, float)
    return float((np.maximum(enviados - real, 0) * costo_ocioso +
                  np.maximum(real - enviados, 0) * costo_perdido).sum())
