import plotly.graph_objects as go
import streamlit as st

from comun import AMARILLO, AZUL, GRIS, ROJO, cargar_csv, cargar_metricas, estilo_figura

st.title("Monitoreo día a día")
st.caption("¿El modelo se mantiene estable durante la semana de prueba? Esta página mide su error cada día "
           "y avisa cuando pasa un límite.")

mon = cargar_csv("monitoreo.csv")
met = cargar_metricas()

limite = st.slider("Límite de alerta (error promedio, viajes por hora)", 1.0, float(max(mon["mae_modelo"].max() * 1.5, 5)),
                   float(met["limite_monitoreo"]), 0.1,
                   help="Valor definido en el notebook; puedes moverlo para ver cuántos días se activarían.")
mon["alerta"] = mon["mae_modelo"] > limite
n_alerta = int(mon["alerta"].sum())

m1, m2, m3 = st.columns(3)
m1.metric("Días evaluados", len(mon), border=True)
m2.metric("Días en alerta", n_alerta, border=True, delta="error sobre el límite" if n_alerta else "todo dentro del límite",
          delta_color="inverse" if n_alerta else "off", delta_arrow="off")
peor = mon.loc[mon["mae_modelo"].idxmax()]
m3.metric("Peor día", str(peor["dia"]), delta=f"{peor['mae_modelo']:.1f} viajes/hora", delta_color="off",
          delta_arrow="off", border=True)

if n_alerta:
    dias = ", ".join(mon.loc[mon["alerta"], "dia"].astype(str))
    st.warning(f"El error superó el límite de {limite:.1f} viajes por hora en: {dias}. "
               "Conviene revisar si ese día tuvo algo especial (clima, evento, feriado).", icon=":material/notification_important:")
else:
    st.success(f"Todos los días quedaron por debajo del límite de {limite:.1f} viajes por hora.", icon=":material/check_circle:")

fig = go.Figure()
fig.add_trace(go.Scatter(x=mon["dia"], y=mon["mae_semana"], name="Hace una semana", mode="lines+markers",
                         line=dict(color=GRIS, dash="dot")))
fig.add_trace(go.Scatter(x=mon["dia"], y=mon["mae_modelo"], name="Modelo", mode="lines+markers",
                         line=dict(color=AZUL, width=3),
                         marker=dict(size=9, color=[ROJO if a else AZUL for a in mon["alerta"]])))
fig.add_hline(y=limite, line=dict(color=ROJO, dash="dash"), annotation_text="Límite de alerta",
              annotation_position="top left")
fig.update_layout(title=dict(text="Error promedio por día", font=dict(size=15)),
                  xaxis=dict(title="Día", type="category"), yaxis=dict(title="Viajes por hora", rangemode="tozero"))
st.plotly_chart(estilo_figura(fig, 400))

st.dataframe(
    mon[["dia", "mae_modelo", "mae_semana", "cobertura", "alerta"]], hide_index=True,
    column_config={
        "dia": "Día",
        "mae_modelo": st.column_config.NumberColumn("Error del modelo", format="%.1f"),
        "mae_semana": st.column_config.NumberColumn("Error de hace una semana", format="%.1f"),
        "cobertura": st.column_config.ProgressColumn("Cobertura del rango 80%", min_value=0, max_value=1, format="percent"),
        "alerta": st.column_config.CheckboxColumn("En alerta"),
    },
)

with st.expander("¿Cómo se definió el límite?", icon=":material/help:"):
    st.write("En el notebook, el límite se fijó en 25% por encima del error promedio de toda la semana de prueba "
             f"({met['mae_modelo']:.1f} viajes por hora). Un día en alerta no significa que el modelo esté roto: "
             "es una señal para mirar con más cuidado ese día.")
