import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from comun import (AMARILLO, AZUL, ROJO, a_dataframe, cargar_info, estilo_figura, fecha_larga,
                   llamar_api, selector_zona_fecha, FECHA_FUTURA)

st.title("¿Cuántos taxis enviar?")
st.caption("El pronóstico no es la decisión. La cantidad correcta depende de qué cuesta más: "
           "un taxi esperando sin pasajero o un pasajero que no encuentra taxi.")

info = cargar_info()
zona_id, fecha, zona_txt = selector_zona_fecha(info)
datos = llamar_api("/pronostico", {"zona_id": zona_id, "fecha": fecha})
df = a_dataframe(datos)
futuro = fecha == FECHA_FUTURA or df["real"].isna().all()
cuantiles = info["cuantiles"]                                   # ["p10", ..., "p90"]
valores = np.array([int(c[1:]) / 100 for c in cuantiles])


def costo(enviados, real, c_ocioso, c_perdido):
    return float((np.maximum(enviados - real, 0) * c_ocioso + np.maximum(real - enviados, 0) * c_perdido).sum())


@st.fragment      # mover un control solo recalcula esta parte, no toda la página
def panel():
    c1, c2 = st.columns(2)
    with c1:
        c_ocioso = st.slider("Costo de un taxi sin pasajero durante una hora (USD)", 1, 100, 10,
                             help="Combustible y horas de conductor desperdiciadas.")
    with c2:
        c_perdido = st.slider("Costo de un pasajero que no encontró taxi (USD)", 1, 200, 40,
                              help="El viaje perdido y el cliente que se va a la competencia.")

    q_opt = c_perdido / (c_perdido + c_ocioso)
    j = int(np.argmin(np.abs(valores - q_opt)))
    col, q_usado = cuantiles[j], valores[j]
    razon = c_perdido / c_ocioso

    if q_opt > 0.5:
        st.markdown(f"Perder un pasajero cuesta **{razon:.1f} veces** lo que cuesta un taxi ocioso. "
                    f"Conviene enviar **más** que el pronóstico central: la regla óptima es cubrir el "
                    f"**cuantil {q_opt:.0%}** de la demanda.")
    elif q_opt < 0.5:
        st.markdown(f"Un taxi ocioso cuesta **{1 / razon:.1f} veces** lo que cuesta perder un pasajero. "
                    f"Conviene enviar **menos** que el pronóstico central: la regla óptima es cubrir el "
                    f"**cuantil {q_opt:.0%}** de la demanda.")
    else:
        st.markdown("Ambos errores cuestan lo mismo: lo mejor es enviar el pronóstico central (cuantil 50%).")
    st.latex(rf"\text{{cuantil óptimo}} = \frac{{C_{{perdido}}}}{{C_{{perdido}} + C_{{ocioso}}}} "
             rf"= \frac{{{c_perdido}}}{{{c_perdido} + {c_ocioso}}} = {q_opt:.2f}")
    if abs(q_usado - q_opt) > 0.05:
        st.caption(f"La API entrega cuantiles de {valores.min():.0%} a {valores.max():.0%} de 10 en 10; "
                   f"se usa el más cercano ({col}).")

    rec = df[col]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["hora"], y=rec, name=f"Taxis recomendados ({col})", marker_color=AZUL))
    fig.add_trace(go.Scatter(x=df["hora"], y=df["p50"], name="Pronóstico central (p50)",
                             line=dict(color=AMARILLO, width=3)))
    if not futuro:
        fig.add_trace(go.Scatter(x=df["hora"], y=df["real"], name="Demanda real", mode="markers",
                                 marker=dict(color=ROJO, size=8)))
    fig.update_layout(title=dict(text=f"{zona_txt} · {fecha_larga(fecha)}", font=dict(size=15)),
                      xaxis=dict(title="Hora del día", tickmode="linear", dtick=2),
                      yaxis=dict(title="Taxis / viajes", rangemode="tozero"))
    st.plotly_chart(estilo_figura(fig, 430))

    if futuro:
        st.info("Para el 1 de febrero no hay viajes reales, así que no se puede calcular el costo. "
                "Sí puedes descargar el plan de taxis.", icon=":material/schedule:")
    elif df["semana"].isna().any():
        st.warning("Faltan datos de “hace una semana” para este día; no se puede comparar esa regla.")
    else:
        st.markdown("**Si este día se hubiera decidido así, el costo habría sido:**")
        real = df["real"]
        c_rec = costo(rec, real, c_ocioso, c_perdido)
        c_p50 = costo(df["p50"], real, c_ocioso, c_perdido)
        c_sem = costo(df["semana"], real, c_ocioso, c_perdido)

        def cambio(x):
            return f"{(x / c_rec - 1) * 100:+.0f}% vs. la recomendación" if c_rec > 0 else None

        k1, k2, k3 = st.columns(3)
        k1.metric(f"Recomendación ({col})", f"${c_rec:,.0f}", border=True)
        k2.metric("Enviar el pronóstico central (p50)", f"${c_p50:,.0f}", delta=cambio(c_p50),
                  delta_color="inverse", border=True)
        k3.metric("Enviar lo de hace una semana", f"${c_sem:,.0f}", delta=cambio(c_sem),
                  delta_color="inverse", border=True)
        st.caption("El costo se calcula con la cantidad exacta del cuantil; el plan descargable la redondea hacia arriba.")

    plan = {"hora": df["hora"].astype(int), "taxis_recomendados": np.ceil(rec).astype(int),
            "pronostico_p50": df["p50"].round(1)}
    if not futuro:
        plan["demanda_real"] = df["real"].astype(int)
    csv = pd.DataFrame(plan).to_csv(index=False).encode("utf-8")
    st.download_button("Descargar plan de taxis por hora", csv, file_name=f"plan_taxis_{zona_id}_{fecha}.csv",
                       mime="text/csv", icon=":material/download:")


panel()

with st.expander("¿Por qué no enviar simplemente el pronóstico central?", icon=":material/lightbulb:"):
    st.markdown(
        "El pronóstico central (mediana) se queda corto la mitad de las veces. Si quedarse corto sale más caro "
        "que pasarse, esa mitad de las veces pesa más en el costo total. Por eso el modelo entrega **varios "
        "cuantiles**: permiten elegir cuánto margen de seguridad pagar según lo que cuesta cada error. "
        "Es el problema del vendedor de periódicos, el mismo razonamiento del umbral por costo en clasificación.\n\n"
        "Supuesto simplificador: un taxi atiende un viaje por hora."
    )
