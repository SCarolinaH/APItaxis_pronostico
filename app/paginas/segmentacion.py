import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import COLORES_BADGE, PALETA, leer_csv, leer_json

st.title("Segmentación de zonas")
st.caption("K-Means agrupa las zonas por cómo se usan los taxis: a qué hora, qué tan lejos, cuánto se paga. "
           "PCA las resume en dos ejes para poder dibujarlas.")

seg = leer_csv("zonas_segmentadas.csv")
grupos = sorted(seg["nombre_grupo"].unique())
color_hex = {g: PALETA[i % len(PALETA)] for i, g in enumerate(grupos)}
color_badge = {g: COLORES_BADGE[i % len(COLORES_BADGE)] for i, g in enumerate(grupos)}

sel_grupos = st.pills("Grupos", grupos, selection_mode="multi", default=grupos)
if not sel_grupos:
    st.warning("Elige al menos un grupo.")
    st.stop()
d = seg[seg["nombre_grupo"].isin(sel_grupos)].copy()

# ----- tarjetas por grupo -----
for i in range(0, len(sel_grupos), 4):
    cols = st.columns(4)
    for col, g in zip(cols, sel_grupos[i:i + 4]):
        sub = d[d["nombre_grupo"] == g]
        with col.container(border=True):
            st.badge(g, color=color_badge[g])
            st.metric("Zonas", len(sub))
            st.caption(f"{sub['viajes_dia'].mean():,.0f} viajes al día · {sub['dist_mediana'].median():.1f} millas · "
                       f"{sub['pct_22_5'].mean():.0%} de noche")
            st.caption(sub["descripcion"].iloc[0])

# ----- mapa PCA con selección -----
izq, der = st.columns([3, 2])
with izq:
    fig = px.scatter(d, x="pc1", y="pc2", color="nombre_grupo", size="viajes_dia", size_max=28,
                     color_discrete_map=color_hex, custom_data=["zona_id"], hover_name="zona",
                     hover_data={"distrito": True, "viajes_dia": ":.0f", "pc1": False, "pc2": False},
                     labels={"pc1": "Componente 1", "pc2": "Componente 2", "nombre_grupo": "Grupo"})
    fig.update_layout(margin=dict(t=10, b=10), legend=dict(orientation="h", y=-0.2),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    evento = st.plotly_chart(fig, on_select="rerun", selection_mode=("points", "box", "lasso"), key="mapa_zonas")
    st.caption(":material/touch_app: Selecciona zonas en el gráfico (clic, caja o lazo) para compararlas.")

sel_ids = []
if evento and evento.selection and evento.selection.points:
    sel_ids = [int(p["customdata"][0]) for p in evento.selection.points]
detalle = d[d["zona_id"].isin(sel_ids)] if sel_ids else d.nlargest(3, "viajes_dia")

# ----- perfil horario de las zonas seleccionadas -----
with der:
    hcols = [f"h{h:02d}" for h in range(24)]
    fig2 = go.Figure()
    for _, fila in detalle.head(6).iterrows():
        fig2.add_trace(go.Scatter(x=list(range(24)), y=fila[hcols].astype(float), mode="lines", name=fila["zona"]))
    fig2.update_layout(title="Perfil horario" + (" de las zonas elegidas" if sel_ids else " de las 3 zonas con más viajes"),
                       xaxis_title="Hora del día", yaxis_title="Proporción de viajes",
                       legend=dict(orientation="h", y=-0.35), margin=dict(t=50, b=10),
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2)
    st.caption("Prueba: selecciona zonas de vida nocturna y compáralas con zonas de oficina. ¿A qué hora llega cada pico?")

# ----- detalle por zona -----
st.subheader("Detalle por zona")
tabla = detalle.copy() if sel_ids else d.copy()
tabla["pct_noche"] = tabla["pct_22_5"] * 100
tabla["perfil"] = tabla[hcols].values.tolist()
tabla = tabla.sort_values("viajes_dia", ascending=False)
st.dataframe(
    tabla[["zona", "distrito", "nombre_grupo", "viajes_dia", "dist_mediana", "pct_noche", "propina_mediana", "perfil"]],
    hide_index=True,
    column_config={
        "zona": "Zona", "distrito": "Distrito", "nombre_grupo": "Grupo",
        "viajes_dia": st.column_config.NumberColumn("Viajes al día", format="%.0f"),
        "dist_mediana": st.column_config.NumberColumn("Distancia mediana", format="%.1f mi"),
        "pct_noche": st.column_config.ProgressColumn("Viajes de noche", min_value=0, max_value=100, format="%.1f%%"),
        "propina_mediana": st.column_config.NumberColumn("Propina mediana", format="$%.2f"),
        "perfil": st.column_config.LineChartColumn("Perfil de 0 a 23 h"),
    })

# ----- justificar k -----
m = leer_json("metricas.json")
with st.expander(f"¿Por qué {m['k']} grupos?", icon=":material/science:"):
    sil = leer_csv("silueta.csv")
    fig3 = px.line(sil, x="k", y="silueta", markers=True,
                   labels={"k": "Número de grupos (k)", "silueta": "Coeficiente de silueta"})
    fig3.add_vline(x=m["k"], line_dash="dot", line_color="#b03a3a")
    fig3.update_layout(margin=dict(t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig3)
    st.markdown(f"Se probó k = 2 a 7. Con **k = {m['k']}** el coeficiente de silueta es **{m['silueta_k']:.2f}** "
                f"(más alto = grupos más separados). Las variables se escalaron con `StandardScaler` y el PCA de dos "
                f"componentes conserva **{m['varianza_pca']:.0%}** de la variación.")
