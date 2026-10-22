"""Punto de entrada: navegación entre páginas."""
import streamlit as st

from utils import api_en_linea, api_url

st.set_page_config(page_title="Taxis NYC", page_icon=":material/local_taxi:", layout="wide")

pagina = st.navigation({
    "Planificar": [
        st.Page("paginas/pronostico.py", title="Pronóstico", icon=":material/insights:", default=True),
        st.Page("paginas/decision.py", title="Decisión", icon=":material/tune:"),
    ],
    "Entender": [
        st.Page("paginas/segmentacion.py", title="Segmentación de zonas", icon=":material/bubble_chart:"),
        st.Page("paginas/ficha.py", title="Ficha del modelo", icon=":material/description:"),
    ],
    "Vigilar": [
        st.Page("paginas/monitoreo.py", title="Monitoreo", icon=":material/monitoring:"),
    ],
})

with st.sidebar:
    st.markdown("### :material/local_taxi: Taxis NYC")
    st.caption("Demanda de taxis amarillos, enero de 2024 (NYC TLC).")
    if api_en_linea(api_url()):
        st.badge("API en línea", icon=":material/cloud_done:", color="green")
    else:
        st.badge("API sin respuesta", icon=":material/cloud_off:", color="red")
    with st.popover("Configurar API", icon=":material/settings:"):
        st.caption("La dirección sale de `st.secrets['API_URL']`.")
        st.code(api_url(), language=None)
        if st.button("Reintentar conexión", icon=":material/refresh:"):
            st.cache_data.clear()
            st.rerun()

pagina.run()
