import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from comun import cargar_csv, cargar_metricas, estilo_figura

st.title("Segmentación de zonas")
st.caption("K-Means agrupa las zonas por cómo se usan los taxis: a qué hora, qué tan lejos, cuánto se paga. "
           "PCA las resume en dos ejes para poder dibujarlas.")

seg = cargar_csv("zonas_segmentadas.csv")
sil = cargar_csv("silueta.csv")
met = cargar_metricas()
HORAS = [f"h{h:02d}" for h in range(24)]

grupos = sorted(seg["nombre_grupo"].unique())
BADGES = ["blue", "orange", "red", "green", "violet", "yellow", "gray"]
HEX = ["#2F6DB5", "#E08A00", "#C0392B", "#2E8B57", "#7D5BA6", "#C9A400", "#7A8794"]
badge = {g: BADGES[i % len(BADGES)] for i, g in enumerate(grupos)}
color = {g: HEX[i % len(HEX)] for i, g in enumerate(grupos)}

elegidos = st.pills("Grupos", grupos, selection_mode="multi", default=grupos)
if not elegidos:
    st.info("Elige al menos un grupo para ver las zonas.", icon=":material/touch_app:")
    st.stop()
f = seg[seg["nombre_grupo"].isin(elegidos)]

# ---- tarjetas por grupo
n = 0
for i in range(0, len(elegidos), 4):
    cols = st.columns(4)
    for col, g in zip(cols, elegidos[i:i + 4]):
        n += 1
        sub = seg[seg["nombre_grupo"] == g]
        with col.container(border=True, key=f"tarjeta_{n}"):
            st.badge(g, color=badge[g])
            st.metric("Zonas", len(sub))
            st.caption(f"{sub['viajes_dia'].mean():,.0f} viajes al día · {sub['dist_mediana'].median():.1f} millas · "
                       f"{sub['pct_22_5'].mean():.0%} de noche")

# ---- dispersión PCA con selección
izq, der = st.columns([3, 2])
with izq:
    fig = px.scatter(f, x="pc1", y="pc2", color="nombre_grupo", size="viajes_dia", size_max=26,
                     custom_data=["zona_id"], hover_name="zona", color_discrete_map=color,
                     hover_data={"distrito": True, "viajes_dia": ":.0f", "pc1": False, "pc2": False,
                                 "nombre_grupo": False},
                     labels={"pc1": "Componente 1", "pc2": "Componente 2", "nombre_grupo": "Grupo",
                             "viajes_dia": "Viajes al día", "distrito": "Distrito"})
    fig.update_traces(marker=dict(opacity=0.75, line=dict(width=0)))
    evento = st.plotly_chart(estilo_figura(fig, 460), on_select="rerun",
                             selection_mode=("points", "box", "lasso"), key="seg_scatter")
    st.caption(f"PCA conserva {met['varianza_pca']:.0%} de la variación. "
               "Selecciona zonas en el gráfico (clic, caja o lazo) para compararlas.")

ids_sel = []
for p in evento.selection.points:
    cd = p.get("customdata")
    if cd:
        ids_sel.append(int(cd[0]))
ids_sel = list(dict.fromkeys(ids_sel))
ver = f[f["zona_id"].isin(ids_sel)] if ids_sel else f.nlargest(5, "viajes_dia")

with der:
    perfil = go.Figure()
    for _, z in ver.head(8).iterrows():
        perfil.add_trace(go.Scatter(x=list(range(24)), y=z[HORAS].astype(float), name=z["zona"], mode="lines"))
    perfil.update_layout(title=dict(text="Perfil horario de las zonas " + ("elegidas" if ids_sel else "con más viajes"),
                                    font=dict(size=14)),
                         xaxis=dict(title="Hora del día", tickmode="linear", dtick=4),
                         yaxis=dict(title="Proporción de viajes", tickformat=".0%"))
    st.plotly_chart(estilo_figura(perfil, 400))
    st.caption("Prueba: selecciona zonas de grupos distintos y compara a qué hora llega cada pico.")

# ---- tabla de detalle
st.subheader("Detalle por zona")
tabla = ver.sort_values("viajes_dia", ascending=False).copy()
tabla["pct_noche"] = tabla["pct_22_5"] * 100
tabla["perfil"] = tabla[HORAS].values.tolist()
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
    },
)

with st.expander("¿Qué distingue a cada grupo?", icon=":material/category:"):
    for g in grupos:
        st.badge(g, color=badge[g])
        st.write(seg.loc[seg["nombre_grupo"] == g, "descripcion"].iloc[0])

with st.expander(f"¿Por qué {met['k']} grupos?", icon=":material/science:"):
    barras = px.bar(sil, x="k", y="silueta", labels={"k": "Número de grupos (k)", "silueta": "Coeficiente de silueta"})
    barras.update_traces(marker_color=["#1B3A57" if k == met["k"] else "#B9C4D0" for k in sil["k"]])
    barras.update_xaxes(dtick=1)
    st.plotly_chart(estilo_figura(barras, 300))
    st.write(f"Se probó k de 2 a 7 y se eligió **k = {met['k']}** (silueta {met['silueta_k']:.2f}). "
             "Una silueta más alta significa grupos más compactos y mejor separados entre sí.")
