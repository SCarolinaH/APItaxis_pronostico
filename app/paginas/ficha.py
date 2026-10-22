import plotly.graph_objects as go
import streamlit as st

from comun import AMARILLO, AZUL, GRIS, cargar_metricas, estilo_figura

met = cargar_metricas()
mm, ms, ma, cob = met["mae_modelo"], met["mae_semana"], met["mae_ayer"], met["cobertura_80"]

st.title("Ficha del modelo")
st.caption("Qué hace el modelo, qué tan bien lo hace y en qué no se debe confiar. Una ficha (model card) es un "
           "documento estándar para que cualquier persona entienda un modelo antes de usarlo.")

with st.container(border=True):
    st.subheader(":material/target: Para qué sirve")
    st.markdown(f"Pronostica cuántos viajes en taxi amarillo empezarán **cada hora** en "
                f"**{met['zonas_pronosticadas']} zonas** de Nueva York, con un rango de incertidumbre "
                f"(cuantiles del 10% al 90%). Está pensado para **planificar la flota** con un día de anticipación.")
    st.badge("XGBoost con 9 cuantiles", color="blue")
    st.badge("Datos: NYC TLC, enero 2024", color="gray")
    st.badge("Horizonte: 24 horas", color="green")

st.subheader(":material/analytics: Qué tan bien funciona")
st.caption(f"Evaluado en la última semana de enero ({met['horas_zona_prueba']:,} horas-zona que el modelo nunca vio).")

m1, m2, m3 = st.columns(3)
m1.metric("Error del modelo", f"{mm:.1f} viajes/hora", border=True,
          delta=f"{(mm / ms - 1) * 100:+.0f}% vs. “igual que hace una semana”", delta_color="inverse")
m2.metric("Cobertura del rango 10%–90%", f"{cob:.0%}", border=True,
          delta=f"objetivo: 80% ({(cob - 0.8) * 100:+.0f} pts)", delta_color="off", delta_arrow="off")
m3.metric("Zonas agrupadas", met["zonas_segmentadas"], border=True,
          delta=f"{met['k']} grupos (K-Means)", delta_color="off", delta_arrow="off")

izq, der = st.columns(2)
with izq:
    reglas = go.Figure(go.Bar(
        x=[ma, ms, mm], y=["Igual que ayer", "Igual que hace una semana", "Modelo (mediana)"],
        orientation="h", marker_color=[GRIS, GRIS, AZUL], text=[f"{v:.1f}" for v in (ma, ms, mm)],
        textposition="outside"))
    reglas.update_layout(title=dict(text="Error frente a reglas simples", font=dict(size=14)),
                         xaxis=dict(title="Viajes por hora"))
    st.plotly_chart(estilo_figura(reglas, 280))
with der:
    pg = sorted(met["por_grupo"], key=lambda r: r["mae_modelo"], reverse=True)
    nombres = [r["nombre_grupo"] for r in pg]
    grupos = go.Figure()
    grupos.add_trace(go.Bar(y=nombres, x=[r["mae_semana"] for r in pg], orientation="h",
                            name="Hace una semana", marker_color=GRIS))
    grupos.add_trace(go.Bar(y=nombres, x=[r["mae_modelo"] for r in pg], orientation="h",
                            name="Modelo", marker_color=AMARILLO))
    grupos.update_layout(title=dict(text="Error según el tipo de zona", font=dict(size=14)),
                         barmode="group", xaxis=dict(title="Viajes por hora"))
    st.plotly_chart(estilo_figura(grupos, 280))

mejora = (ms - mm) / ms
if mejora > 0.15:
    veredicto = "le gana con claridad a"
elif mejora > 0.02:
    veredicto = "le gana por poco a"
elif mejora >= -0.02:
    veredicto = "prácticamente empata con"
else:
    veredicto = "pierde frente a"
peor = max(met["por_grupo"], key=lambda r: r["mae_modelo"])
st.markdown(f"El modelo {veredicto} “igual que hace una semana” ({mm:.1f} contra {ms:.1f} viajes por hora). "
            f"Su valor principal está en el **rango**, que las reglas simples no dan. "
            f"El error es mayor en el grupo **{peor['nombre_grupo']}** ({peor['mae_modelo']:.1f} viajes por hora).")

fuera = met["zonas_segmentadas"] - met["zonas_pronosticadas"]
with st.container(border=True):
    st.subheader(":material/warning: Limitaciones")
    st.markdown(
        "- Entrenado con **un solo mes de invierno**: no conoce el verano, las vacaciones ni eventos como un maratón.\n"
        "- Solo usa la historia de la propia demanda y el calendario: **no sabe de clima, conciertos ni cierres de calles**.\n"
        f"- Las zonas con menos de 3,000 viajes al mes **no tienen pronóstico** ({fuera} de las {met['zonas_segmentadas']} "
        "que sí se segmentan quedan fuera).\n"
        f"- El rango del 80% acierta {cob:.0%} en promedio, pero **varía por zona**: "
        f"de {met['cobertura_zona_min']:.0%} a {met['cobertura_zona_max']:.0%}."
    )

with st.container(border=True):
    st.subheader(":material/block: Usos no recomendados")
    st.markdown(
        "- Decidir **qué conductores trabajan** o evaluar su desempeño con este pronóstico.\n"
        "- Recortar el servicio en zonas periféricas porque “el modelo predice poca demanda”: en esos barrios se usan "
        "más los taxis verdes y las apps, que no están en estos datos. Poca demanda de taxi amarillo no significa "
        "poca necesidad de transporte.\n"
        "- Usarlo **más de un día hacia adelante**: está entrenado para el día siguiente."
    )


def gracias():
    st.toast("¡Gracias por tu opinión!", icon=":material/thumb_up:")


st.divider()
st.markdown("**¿Te resultó clara esta ficha?**")
st.feedback("stars", key="fb_ficha", on_change=gracias)
