import plotly.graph_objects as go
import streamlit as st

from comun import (AMARILLO, AZUL, BANDA, ROJO, a_dataframe, cargar_info, estilo_figura,
                   fecha_larga, llamar_api, selector_zona_fecha, FECHA_FUTURA)


@st.dialog("¿Cómo leer este pronóstico?")
def ayuda():
    st.markdown(
        "- La **línea** es el pronóstico central (mediana): la mitad de las veces la demanda real "
        "queda arriba y la otra mitad abajo.\n"
        "- La **banda** va del cuantil 10% al 90%: en cerca de 8 de cada 10 horas la demanda real cae dentro.\n"
        "- Los **puntos** son los viajes que de verdad ocurrieron (no existen para mañana).\n"
        "- Una banda ancha no es un error del modelo: es una hora **difícil de predecir**, y conviene saberlo."
    )


izq, der = st.columns([5, 1], vertical_alignment="bottom")
with izq:
    st.title("Pronóstico de demanda")
    st.caption("Viajes por hora que se esperan en una zona, con su rango de incertidumbre. "
               "El modelo vive en la API.")
with der:
    if st.button("Cómo leerlo", icon=":material/help:"):
        ayuda()

info = cargar_info()
zona_id, fecha, zona_txt = selector_zona_fecha(info)
datos = llamar_api("/pronostico", {"zona_id": zona_id, "fecha": fecha})
df = a_dataframe(datos)
futuro = fecha == FECHA_FUTURA or df["real"].isna().all()

# ---- métricas
total, semana = df["p50"].sum(), df["semana"].sum()
delta = f"{(total / semana - 1) * 100:+.0f}% vs. hace una semana" if semana > 0 else None
pico = df["p50"].idxmax()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Viajes esperados en el día", f"{total:,.0f}", delta=delta, delta_color="off",
          chart_data=df["p50"].round().tolist(), chart_type="area", border=True)
m2.metric("Hora pico", f"{int(df.loc[pico, 'hora'])}:00", delta=f"{df.loc[pico, 'p50']:,.0f} viajes",
          delta_color="off", delta_arrow="off", border=True)
m3.metric("Rango del día (80%)", f"{df['p10'].sum():,.0f} – {df['p90'].sum():,.0f}", border=True,
          help="Suma de los cuantiles 10% y 90% hora por hora. Es una aproximación del rango del día.")
if futuro:
    m4.metric("Viajes reales", "Pendiente", delta="pronóstico a futuro", delta_color="off",
              delta_arrow="off", border=True)
else:
    mae = (df["real"] - df["p50"]).abs().mean()
    m4.metric("Error promedio por hora", f"{mae:.1f} viajes", delta=f"{df['real'].sum():,.0f} viajes reales",
              delta_color="off", delta_arrow="off", border=True)

# ---- gráfico con banda de incertidumbre
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["hora"], y=df["p90"], line=dict(width=0), hoverinfo="skip", showlegend=False))
fig.add_trace(go.Scatter(x=df["hora"], y=df["p10"], line=dict(width=0), fill="tonexty",
                         fillcolor=BANDA, name="Rango 10%–90%", hoverinfo="skip"))
fig.add_trace(go.Scatter(x=df["hora"], y=df["semana"], name="Hace una semana",
                         line=dict(color="#8A96A3", width=1.5, dash="dot")))
fig.add_trace(go.Scatter(x=df["hora"], y=df["p50"], name="Pronóstico (mediana)",
                         line=dict(color=AZUL, width=3)))
if not futuro:
    fig.add_trace(go.Scatter(x=df["hora"], y=df["real"], name="Real", mode="markers",
                             marker=dict(color=ROJO, size=8)))
sufijo = " (pronóstico a futuro)" if futuro else ""
fig.update_layout(title=dict(text=f"{zona_txt} · {fecha_larga(fecha)}{sufijo}", font=dict(size=15)),
                  xaxis=dict(title="Hora del día", tickmode="linear", dtick=2),
                  yaxis=dict(title="Viajes", rangemode="tozero"))
st.plotly_chart(estilo_figura(fig, 460))

if futuro:
    st.info("El 1 de febrero es “mañana”: todavía no hay viajes reales, por eso solo se ve el pronóstico.",
            icon=":material/schedule:")

with st.expander("Ver la tabla por hora", icon=":material/table:"):
    st.dataframe(
        df[["hora", "p10", "p50", "p90", "real", "semana"]],
        hide_index=True,
        column_config={
            "hora": st.column_config.NumberColumn("Hora", format="%d:00"),
            "p10": st.column_config.NumberColumn("Mínimo probable (p10)", format="%.0f"),
            "p50": st.column_config.ProgressColumn("Pronóstico (p50)", min_value=0,
                                                   max_value=float(df["p90"].max()), format="%.0f"),
            "p90": st.column_config.NumberColumn("Máximo probable (p90)", format="%.0f"),
            "real": st.column_config.NumberColumn("Real", format="%.0f"),
            "semana": st.column_config.NumberColumn("Hace una semana", format="%.0f"),
        },
    )
