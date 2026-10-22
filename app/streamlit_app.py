"""Punto de entrada: define las páginas y la barra lateral."""
import streamlit as st

from comun import api_en_linea, api_url

st.set_page_config(page_title="Taxis NYC", page_icon=":material/local_taxi:", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #eef3f8; }

[data-testid="stMetric"],
[data-testid="stMetricContainer"] {
       border-color: #2d6a6a !important;
}


[data-testid="stSidebar"] { background-color: #dde8f1; }
[data-testid="stHeader"] { background: transparent; }
</style>
""", unsafe_allow_html=True)

paginas = {
    "Planificar": [
        st.Page("paginas/pronostico.py", title="Pronóstico", icon=":material/insights:", default=True),
        st.Page("paginas/decision.py", title="Decisión", icon=":material/tune:"),
    ],
    "Entender": [
        st.Page("paginas/segmentacion.py", title="Segmentación de zonas", icon=":material/bubble_chart:"),
        st.Page("paginas/ficha.py", title="Ficha del modelo", icon=":material/description:"),
    ],
    "Extra": [
        st.Page("paginas/monitoreo.py", title="Monitoreo", icon=":material/monitor_heart:"),
    ],
}
pagina = st.navigation(paginas)

with st.sidebar:
    st.markdown("### :material/local_taxi: Taxis NYC")
    st.caption("Demanda de taxis amarillos, enero de 2024 (NYC TLC).")
    if api_en_linea():
        st.badge("API en línea", icon=":material/cloud_done:", color="green")
    else:
        st.badge("API sin respuesta", icon=":material/cloud_off:", color="red")
    with st.popover("Configurar API", icon=":material/settings:"):
        st.code(api_url(), language=None)
        st.caption("La dirección se define en `st.secrets['API_URL']`.")

pagina.run()
