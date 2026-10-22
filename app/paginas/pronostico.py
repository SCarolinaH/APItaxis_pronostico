import plotly.graph_objects as go
import streamlit as st

from utils import VERDE, ROJO, a_dataframe, cargar, selector_zona_fecha

st.title("Pronóstico de demanda")


@st.dialog("¿Cómo leer este pronóstico?")
def ayuda():
    st.markdown(
        "- La **línea** es el pronóstico central (mediana): la mitad de las veces la demanda real queda arriba y la mitad abajo.\n"
        "- La **banda** va del cuantil 10% al 90%: en unas 8 de cada 10 horas la demanda real debería caer dentro.\n"
        "- Los **puntos** son los viajes que de verdad ocurrieron (no existen para mañana).\n"
        "- Una banda ancha no es un error del modelo: es una hora **difícil de predecir**, y conviene saberlo."
    )


c_txt, c_btn = st.columns([5, 1])
c_txt.caption("Viajes por hora que se esperan en una zona, con su rango de incertidumbre. El modelo vive en la API.")
if c_btn.button("Cómo leerlo", icon=":material/help:"):
    ayuda()

info = cargar("/info")
zona_id, fecha, zona_txt = selector_zona_fecha(info)
datos = cargar("/pronostico", zona_id=zona_id, fecha=fecha)
df = a_dataframe(datos)
tiene_real = df["real"].notna().all()

# ----- métricas -----
p50 = df["p50"]
total, total_sem = p50.sum(), df["hace_una_semana"].sum()
delta = (total / total_sem - 1) if total_sem > 0 else None
hora_pico = int(df.loc[p50.idxmax(), "hora"])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Viajes esperados en el día", f"{total:,.0f}", border=True,
          delta=f"{delta:+.0%} vs. hace una semana" if delta is not None else None,
          chart_data=p50.tolist(), chart_type="area")
m2.metric("Hora pico", f"{hora_pico:02d}:00", border=True,
          delta=f"{p50.max():,.0f} viajes", delta_color="off", delta_arrow="off")
m3.metric("Rango del día (80%)", f"{df['p10'].sum():,.0f} – {df['p90'].sum():,.0f}", border=True,
          help="Suma de los cuantiles 10% y 90% de las 24 horas (aproximado).")
if tiene_real:
    mae = (df["real"] - p50).abs().mean()
    m4.metric("Error promedio por hora", f"{mae:.1f} viajes", border=True,
              delta=f"{df['real'].sum():,.0f} viajes reales", delta_color="off", delta_arrow="off")
else:
    m4.metric("Viajes reales", "Pendiente", border=True,
              delta="pronóstico a futuro", delta_color="off", delta_arrow="off")
    st.info("El 1 de febrero es «mañana»: todavía no hay datos reales, solo pronóstico.", icon=":material/schedule:")

# ----- gráfico con banda de incertidumbre -----
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["hora"], y=df["p90"], mode="lines", line=dict(width=0),
                         showlegend=False, hoverinfo="skip"))
fig.add_trace(go.Scatter(x=df["hora"], y=df["p10"], mode="lines", line=dict(width=0), fill="tonexty",
                         fillcolor="rgba(45,106,106,0.20)", name="Rango 10%–90%"))
fig.add_trace(go.Scatter(x=df["hora"], y=df["hace_una_semana"], mode="lines",
                         line=dict(dash="dot", color="#666"), name="Hace una semana"))
fig.add_trace(go.Scatter(x=df["hora"], y=p50, mode="lines", line=dict(color=VERDE, width=3),
                         name="Pronóstico (mediana)"))
if tiene_real:
    fig.add_trace(go.Scatter(x=df["hora"], y=df["real"], mode="markers", marker=dict(color=ROJO, size=8),
                             name="Real"))
fig.update_layout(title=f"{zona_txt} · {fecha}", xaxis_title="Hora del día", yaxis_title="Viajes",
                  legend=dict(orientation="h", y=-0.2), margin=dict(t=50, b=10),
                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
fig.update_xaxes(dtick=2)
st.plotly_chart(fig)

with st.expander("Ver la tabla por hora", icon=":material/table:"):
    tabla = df.rename(columns={"hora": "Hora", "real": "Real", "hace_una_semana": "Hace una semana"})
    st.dataframe(tabla[["Hora", "Real", "Hace una semana", "p10", "p50", "p90"]], hide_index=True,
                 column_config={"p50": st.column_config.ProgressColumn(
                     "p50 (central)", min_value=0, max_value=float(df["p50"].max()) or 1, format="%.0f"),
                     "p10": st.column_config.NumberColumn(format="%.0f"),
                     "p90": st.column_config.NumberColumn(format="%.0f")})
