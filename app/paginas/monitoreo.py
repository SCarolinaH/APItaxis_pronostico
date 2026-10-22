import plotly.graph_objects as go
import streamlit as st

from utils import VERDE, ROJO, leer_csv, leer_json

st.title("Monitoreo del error")
st.caption("Error del modelo día a día en la semana de prueba. Si pasa el límite, hay que revisar o reentrenar.")

mon = leer_csv("monitoreo.csv")
limite = leer_json("metricas.json")["limite_monitoreo"]

fuera = mon[mon["mae_modelo"] > limite]
if fuera.empty:
    st.success(f"Todos los días están dentro del límite ({limite} viajes por hora).", icon=":material/check_circle:")
else:
    st.warning(f"{len(fuera)} día(s) superan el límite de {limite} viajes por hora: "
               + ", ".join(fuera["dia"].astype(str)), icon=":material/notification_important:")

colores = [ROJO if v > limite else VERDE for v in mon["mae_modelo"]]
fig = go.Figure()
fig.add_bar(x=mon["dia"].astype(str), y=mon["mae_modelo"], marker_color=colores, name="Error del modelo")
fig.add_trace(go.Scatter(x=mon["dia"].astype(str), y=mon["mae_semana"], mode="lines+markers",
                         name="«Igual que hace una semana»", line=dict(dash="dot", color="#666")))
fig.add_hline(y=limite, line_dash="dash", line_color=ROJO, annotation_text="Límite")
fig.update_layout(yaxis_title="Error (viajes por hora)", legend=dict(orientation="h", y=-0.2),
                  margin=dict(t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig)
st.dataframe(mon, hide_index=True, column_config={
    "dia": "Día", "mae_modelo": st.column_config.NumberColumn("Error del modelo", format="%.2f"),
    "mae_semana": st.column_config.NumberColumn("Error «hace una semana»", format="%.2f"),
    "cobertura": st.column_config.ProgressColumn("Cobertura 10–90%", min_value=0, max_value=1, format="percent"),
    "alerta": st.column_config.CheckboxColumn("Alerta")})
