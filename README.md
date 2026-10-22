# Taxis NYC · Pronóstico, segmentación y decisión

Actividad AIMLT1 · Módulo 4 (KODIGO).

## Links
- **App (Streamlit Cloud):** _pegar link_
- **API (Render):** _pegar link_ (documentación en `/docs`)
- **Repositorio:** _pegar link_

## Integrantes
- _Nombre 1_
- _Nombre 2_

## Estructura
```
preparacion.ipynb   datos, modelos y métricas (genera api/ y app/data/)
api/                FastAPI + modelo (se publica en Render, Root Directory: api)
app/                Streamlit (se publica en Streamlit Cloud, main file: app/streamlit_app.py)
```

## Cómo correr el proyecto
1. Abrir `preparacion.ipynb` en Colab y correrlo completo; copiar a `api/` y `app/data/` los archivos que genera.
2. API: `cd api && pip install -r requirements.txt && uvicorn main:app --reload` → http://localhost:8000/docs
3. App: `cd app && pip install -r requirements.txt`, copiar `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml`
   (con `API_URL`) y correr `streamlit run streamlit_app.py`.

## Funciones avanzadas de Streamlit usadas
st.navigation/st.Page, @st.fragment, @st.dialog, plotly on_select, st.column_config, @st.cache_data, st.secrets,
st.query_params, st.status, st.pills, st.segmented_control, st.badge, st.popover, st.metric con chart_data, tema en config.toml.
