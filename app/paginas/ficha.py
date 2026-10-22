import pandas as pd
import plotly.express as px
import streamlit as st

from utils import VERDE, leer_json

m = leer_json("metricas.json")
por_grupo = pd.DataFrame(m["por_grupo"])

st.title("Ficha del modelo")
st.caption("Qué hace el modelo, qué tan bien lo hace y en qué no se debe confiar. Una ficha (model card) es un "
           "documento estándar para que cualquier persona entienda un modelo antes de usarlo.")

with st.container(border=True):
    st.subheader(":material/target: Para qué sirve")
    st.markdown(f"Pronostica cuántos viajes en taxi amarillo empezarán **cada hora** en **{m['zonas_pronosticadas']} zonas** "
                "de Nueva York, con un rango de incertidumbre (cuantiles del 10% al 90%). Está pensado para "
                "**planificar la flota** con un día de anticipación.")
    b1, b2, b3 = st.columns(3)
    b1.badge("XGBoost con 9 cuantiles", icon=":material/model_training:", color="blue")
    b2.badge("Datos: NYC TLC, enero 2024", icon=":material/database:", color="gray")
    b3.badge("Horizonte: 24 horas", icon=":material/schedule:", color="green")

st.subheader(":material/query_stats: Qué tan bien funciona")
st.caption(f"Evaluado del 25 al 31 de enero ({m['horas_zona_prueba']:,} horas-zona que el modelo nunca vio).")

mejora = 1 - m["mae_modelo"] / m["mae_semana"]
k1, k2, k3 = st.columns(3)
k1.metric("Error del modelo", f"{m['mae_modelo']:.1f} viajes/hora", border=True,
          delta=f"{-mejora:+.0%} vs. «igual que hace una semana»", delta_color="inverse")
k2.metric("Cobertura del rango 10%–90%", f"{m['cobertura_80']:.0%}", border=True,
          delta="objetivo: 80%", delta_color="off", delta_arrow="off")
k3.metric("Zonas agrupadas", m["zonas_segmentadas"], border=True,
          delta=f"{m['k']} grupos (K-Means)", delta_color="off", delta_arrow="off")

g1, g2 = st.columns(2)
reglas = pd.DataFrame({"Método": ["Igual que ayer", "Igual que hace una semana", "Modelo (mediana)"],
                       "Error (viajes por hora)": [m["mae_ayer"], m["mae_semana"], m["mae_modelo"]]})
with g1:
    f1 = px.bar(reglas, x="Error (viajes por hora)", y="Método", orientation="h", title="Error frente a reglas simples")
    f1.update_traces(marker_color=VERDE)
    f1.update_layout(margin=dict(t=50, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(f1)
with g2:
    f2 = px.bar(por_grupo.sort_values("mae_modelo"), x="mae_modelo", y="nombre_grupo", orientation="h",
                title="Error según el tipo de zona", labels={"mae_modelo": "Error (viajes por hora)", "nombre_grupo": ""})
    f2.update_traces(marker_color="#c97b3d")
    f2.update_layout(margin=dict(t=50, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(f2)

# Conclusiones escritas a partir de los números (no a mano)
if mejora > 0.02:
    st.write(f"El modelo le gana a «igual que hace una semana» por {mejora:.0%}.")
elif mejora < -0.02:
    st.write(f"El modelo **pierde** contra «igual que hace una semana» por {-mejora:.0%}.")
else:
    st.write("El modelo prácticamente **empata** con «igual que hace una semana».")
st.write("Su valor principal está en el **rango de incertidumbre**, que las reglas simples no dan.")

peor = por_grupo.sort_values("mae_modelo").iloc[-1]
mejor = por_grupo.sort_values("mae_modelo").iloc[0]
st.write(f"Donde más se equivoca: **{peor['nombre_grupo']}** ({peor['mae_modelo']:.1f} viajes por hora). "
         f"Donde menos: **{mejor['nombre_grupo']}** ({mejor['mae_modelo']:.1f}).")
dif = m["cobertura_80"] - 0.80
if abs(dif) <= 0.05:
    st.write(f"El rango del 80% acierta **{m['cobertura_80']:.0%}**: es una cobertura cercana a lo prometido.")
elif dif < 0:
    st.write(f"El rango del 80% acierta solo **{m['cobertura_80']:.0%}**: el modelo está **demasiado seguro** de sí mismo.")
else:
    st.write(f"El rango del 80% acierta **{m['cobertura_80']:.0%}**: es **más ancho de lo necesario**.")

with st.container(border=True):
    st.subheader(":material/warning: Limitaciones")
    st.markdown(
        "- Entrenado con **un solo mes de invierno**: no conoce el verano, las vacaciones ni eventos como el maratón.\n"
        "- Solo usa la historia de la propia demanda y el calendario: **no sabe de clima, conciertos ni cierres de calles**.\n"
        f"- Solo {m['zonas_pronosticadas']} de las 265 zonas de la ciudad tienen pronóstico (las de al menos 3,000 viajes al mes).\n"
        f"- El rango del 80% acierta {m['cobertura_80']:.0%} en promedio, pero varía por zona: de "
        f"{m['cobertura_zona_min']:.0%} a {m['cobertura_zona_max']:.0%}.")

with st.container(border=True):
    st.subheader(":material/block: Usos no recomendados")
    st.markdown(
        "- Decidir **qué conductores trabajan** o evaluar su desempeño con este pronóstico.\n"
        "- Recortar el servicio en zonas periféricas porque «el modelo predice poca demanda»: en esos barrios se usan más "
        "los taxis verdes y las apps, que no están en estos datos. Poca demanda de taxi amarillo no significa poca "
        "necesidad de transporte; una mala decisión aquí perjudica a quienes ya tienen menos opciones.\n"
        "- Usarlo más de un día hacia adelante: está entrenado para el día siguiente.")

st.divider()
st.markdown("**¿Te resultó clara esta ficha?**")
voto = st.feedback("stars")
if voto is not None:
    st.toast(f"¡Gracias por tu calificación ({voto + 1} de 5)!", icon=":material/thumb_up:")
