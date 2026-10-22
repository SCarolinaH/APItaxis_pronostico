"""Funciones compartidas por todas las páginas: conexión con la API, selectores y datos locales."""
import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

DATA = Path(__file__).parent / "data"
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
FECHA_FUTURA = "2024-02-01"          # el "mañana": no tiene datos reales

AZUL = "#1B3A57"
AMARILLO = "#E0A100"
ROJO = "#B83A2E"
GRIS = "#8A96A3"
BANDA = "rgba(27, 58, 87, 0.16)"


# ---------------------------------------------------------------- API
def api_url() -> str:
    """La dirección de la API vive en st.secrets, no en el código."""
    try:
        url = st.secrets["API_URL"]
    except Exception:
        url = "http://localhost:8000"
    return str(url).rstrip("/")


@st.cache_data(ttl=3600, show_spinner=False)
def _pedir(ruta: str, params: dict | None = None):
    """Un solo lugar donde se llama a la API; el caché evita repetir la llamada en cada clic."""
    r = requests.get(f"{api_url()}{ruta}", params=params, timeout=90)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=30, show_spinner=False)
def api_en_linea() -> bool:
    try:
        return requests.get(f"{api_url()}/", timeout=5).ok
    except requests.RequestException:
        return False


def llamar_api(ruta: str, params: dict | None = None):
    """Pide datos a la API. Si falla, explica qué pasó en lenguaje claro y detiene la página."""
    try:
        with st.status("Conectando con la API...", expanded=False) as estado:
            datos = _pedir(ruta, params)
            estado.update(label="API conectada", state="complete")
        return datos
    except requests.HTTPError as e:
        detalle = "La API respondió con un error."
        try:
            detalle = e.response.json().get("detail", detalle)
        except Exception:
            pass
        st.error(f"{detalle} (código {e.response.status_code if e.response is not None else '?'})",
                 icon=":material/error:")
    except requests.RequestException as e:
        st.error(
            f"No se pudo conectar con la API en {api_url()}. "
            "Si está en Render, puede estar despertando: espera un minuto y vuelve a intentar.",
            icon=":material/cloud_off:",
        )
        st.caption(f"Detalle técnico: {type(e).__name__}")
    if st.button("Reintentar", icon=":material/refresh:"):
        st.rerun()
    st.stop()


def cargar_info() -> dict:
    return llamar_api("/info")


def a_dataframe(datos: dict) -> pd.DataFrame:
    """Convierte la respuesta de /pronostico en una tabla con una fila por hora."""
    filas = []
    for h in datos["horas"]:
        fila = {"hora": h["hora"], "real": h["real"], "semana": h["hace_una_semana"]}
        fila.update(h["cuantiles"])
        filas.append(fila)
    df = pd.DataFrame(filas)
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


# ---------------------------------------------------------------- fechas
def etiqueta_fecha(iso: str) -> str:
    d = date.fromisoformat(iso)
    texto = f"{DIAS[d.weekday()]} {d.day}"
    return texto + " (mañana)" if iso == FECHA_FUTURA else texto


def fecha_larga(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]}"


# ---------------------------------------------------------------- selector con memoria
def selector_zona_fecha(info: dict):
    """Zona + fecha. Se recuerdan al cambiar de página (session_state) y en el link (query_params)."""
    zonas = {z["id"]: f'{z["nombre"]} ({z["distrito"]})' for z in info["zonas"]}
    ids = list(zonas)
    fechas = info["fechas"]

    if "zona_id" not in st.session_state:
        z = st.query_params.get("zona", "")
        por_defecto = 161 if 161 in zonas else ids[0]
        st.session_state["zona_id"] = int(z) if z.isdigit() and int(z) in zonas else por_defecto
    if "fecha" not in st.session_state:
        f = st.query_params.get("fecha", "")
        st.session_state["fecha"] = f if f in fechas else fechas[0]

    zona_id = st.selectbox("Zona", ids, index=ids.index(st.session_state["zona_id"]),
                           format_func=zonas.get, key="w_zona")
    elegida = st.segmented_control("Fecha", fechas, default=st.session_state["fecha"],
                                   format_func=etiqueta_fecha, key="w_fecha")
    fecha = elegida or st.session_state["fecha"]      # None si la persona deselecciona

    st.session_state["zona_id"], st.session_state["fecha"] = zona_id, fecha
    st.query_params["zona"], st.query_params["fecha"] = str(zona_id), fecha
    return zona_id, fecha, zonas[zona_id]


# ---------------------------------------------------------------- datos locales (del notebook)
def _falta(nombre: str):
    st.error(f"Falta el archivo app/data/{nombre}. Se genera en el notebook (sección 8) y debe subirse al repositorio.",
             icon=":material/folder_off:")
    st.stop()


@st.cache_data(show_spinner=False)
def _csv(nombre: str) -> pd.DataFrame:
    return pd.read_csv(DATA / nombre)


@st.cache_data(show_spinner=False)
def _json(nombre: str) -> dict:
    return json.loads((DATA / nombre).read_text(encoding="utf-8"))


def cargar_csv(nombre: str) -> pd.DataFrame:
    if not (DATA / nombre).exists():
        _falta(nombre)
    return _csv(nombre)


def cargar_metricas() -> dict:
    if not (DATA / "metricas.json").exists():
        _falta("metricas.json")
    return _json("metricas.json")


def estilo_figura(fig, alto=420):
    fig.update_layout(
        height=alto, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="top", y=-0.18, x=0),
        font=dict(size=13),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(138,150,163,0.25)", zeroline=False)
    return fig
