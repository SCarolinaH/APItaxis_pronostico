# Taxis NYC: una app para quien toma decisiones

Pronóstico de demanda con incertidumbre, segmentación de zonas y una recomendación de cuántos taxis enviar.
Proyecto de AIMLF1 · Módulo 2 (actividad en parejas).

## Links

- **App (Streamlit):** _pegar aquí_
- **API (Render):** _pegar aquí_ (documentación en `/docs`)
- **Repositorio:** _pegar aquí_

## Integrantes

- _Nombre 1_
- _Nombre 2_
- - _Nombre 2_

## Cómo está organizado

```
taxis-nyc/
├── preparacion.ipynb          # datos, modelos y métricas (Colab)
├── api/                       # FastAPI + modelo (se publica en Render)
│   ├── main.py
│   ├── modelo_pronostico.ubj
│   ├── config_modelo.json
│   ├── demanda.parquet
│   ├── zonas.csv
│   └── requirements.txt
└── app/                       # Streamlit (se publica en Streamlit Community Cloud)
    ├── streamlit_app.py       # entrada: st.navigation
    ├── comun.py               # conexión con la API y utilidades
    ├── paginas/               # pronóstico, decisión, segmentación, ficha, monitoreo
    ├── data/                  # CSV y JSON generados por el notebook
    ├── .streamlit/config.toml # tema de colores
    └── requirements.txt
```

La app **nunca carga el modelo**: le pide el pronóstico a la API (`/info`, `/pronostico`).

## Cómo correr el proyecto en tu computadora

1. Ejecuta el notebook completo (sección 8) para generar los archivos de `api/` y `app/data/`.
2. API:
   ```bash
   cd api
   pip install -r requirements.txt
   uvicorn main:app --reload        # http://localhost:8000/docs
   ```
3. App (en otra terminal):
   ```bash
   cd app
   pip install -r requirements.txt
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   streamlit run streamlit_app.py
   ```

## Funciones avanzadas de Streamlit usadas

`st.navigation` / `st.Page`, `@st.fragment`, `@st.dialog`, `st.plotly_chart(on_select="rerun")`,
`st.column_config`, `@st.cache_data`, `st.secrets`, `st.query_params`, `st.status`, `st.toast`,
`st.pills`, `st.segmented_control`, `st.badge`, `st.popover`, `st.metric(chart_data=...)`, tema en `config.toml`.

## Nota

En Render (plan gratuito) la API se duerme tras 15 minutos sin uso y tarda cerca de un minuto en despertar.
