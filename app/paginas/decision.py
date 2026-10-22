import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import VERDE, ROJO, a_dataframe, cargar, columnas_cuantiles, costo, selector_zona_fecha

st.title("¿Cuántos taxis enviar?")
st.caption("El pronóstico no es la decisión. La cantidad correcta depende de qué cuesta más: "
           "un taxi esperando sin pasajero o un pasajero que no encuentra taxi.")

info = cargar("/info")
zona_id, fecha, zona_txt = selector_zona_fecha(info)
df = a_dataframe(cargar("/pronostico", zona_id=zona_id, fecha=fecha))


@st.fragment
def panel(df, zona_txt, fecha):
    """Mover un control solo actualiza este bloque, no toda la página."""
    c1, c2 = st.columns(2)
    c_ocioso = c1.slider("Costo de un taxi sin pasajero durante una hora (USD)", 1, 100, 10)
    c_perdido = c2.slider("Costo de un pasajero que no encontró taxi (USD)", 1, 200, 40)

    q = c_perdido / (c_perdido + c_ocioso)
    cols_q, niveles = columnas_cuantiles(df)
    col = cols_q[int(np.argmin(np.abs(niveles - q)))]
    nivel = int(col[1:])

    razon = c_perdido / c_ocioso
    st.markdown(f"Perder un pasajero cuesta **{razon:.1f} veces** lo que cuesta un taxi ocioso. "
                f"La regla óptima es cubrir el **cuantil {q:.0%}** de la demanda.")
    st.latex(rf"\text{{cuantil óptimo}}=\frac{{C_{{\text{{perdido}}}}}}{{C_{{\text{{perdido}}}}+C_{{\text{{ocioso}}}}}}"
             rf"=\frac{{{c_perdido}}}{{{c_perdido}+{c_ocioso}}}={q:.2f}")
    if abs(nivel / 100 - q) > 0.051:
        st.caption(f"La API entrega cuantiles de 10 en 10 (del 10% al 90%); se usa el más cercano: p{nivel}.")
    if q > 0.5:
        st.success(f"En lenguaje simple: quedarse corto sale más caro que pasarse, así que conviene enviar "
                   f"**más taxis que el pronóstico central** (los que cubren el {nivel}% de los casos).")
    elif q < 0.5:
        st.success(f"En lenguaje simple: un taxi parado sale más caro que perder un pasajero, así que conviene enviar "
                   f"**menos taxis que el pronóstico central** (los que cubren el {nivel}% de los casos).")
    else:
        st.success("En lenguaje simple: ambos errores cuestan igual, así que conviene enviar el pronóstico central.")

    enviados = df[col].round()
    tiene_real = df["real"].notna().all()

    fig = go.Figure()
    fig.add_bar(x=df["hora"], y=enviados, name=f"Taxis recomendados (p{nivel})", marker_color=VERDE)
    fig.add_trace(go.Scatter(x=df["hora"], y=df["p50"], mode="lines", name="Pronóstico central (p50)",
                             line=dict(color="#d98c3a", width=3)))
    if tiene_real:
        fig.add_trace(go.Scatter(x=df["hora"], y=df["real"], mode="markers", name="Demanda real",
                                 marker=dict(color=ROJO, size=8)))
    fig.update_layout(title=f"{zona_txt} · {fecha}", xaxis_title="Hora", yaxis_title="Taxis / viajes",
                      legend=dict(orientation="h", y=-0.2), margin=dict(t=50, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig)

    if tiene_real:
        st.markdown("**Si este día se hubiera decidido así, el costo habría sido:**")
        real = df["real"]
        c_rec = costo(enviados, real, c_ocioso, c_perdido)
        c_cen = costo(df["p50"].round(), real, c_ocioso, c_perdido)
        c_sem = costo(df["hace_una_semana"].round(), real, c_ocioso, c_perdido)

        def delta(c):
            return f"{(c / c_rec - 1):+.0%} vs. la recomendación" if c_rec > 0 else None

        m1, m2, m3 = st.columns(3)
        m1.metric(f"Recomendación (p{nivel})", f"${c_rec:,.0f}", border=True)
        m2.metric("Enviar el pronóstico central (p50)", f"${c_cen:,.0f}", border=True,
                  delta=delta(c_cen), delta_color="inverse")
        m3.metric("Enviar lo de hace una semana", f"${c_sem:,.0f}", border=True,
                  delta=delta(c_sem), delta_color="inverse")
    else:
        st.info("Este día es un pronóstico a futuro: no hay demanda real para comparar costos. "
                "Elige un día del 25 al 31 de enero para ver cuánto habría costado cada regla.",
                icon=":material/schedule:")

    plan = pd.DataFrame({"hora": df["hora"].astype(int), "taxis_recomendados": enviados.astype(int),
                         "pronostico_central_p50": df["p50"].round().astype(int), "cuantil_usado": f"p{nivel}"})
    st.download_button("Descargar plan de taxis por hora", plan.to_csv(index=False).encode("utf-8"),
                       file_name=f"plan_taxis_zona{zona_id}_{fecha}.csv", mime="text/csv",
                       icon=":material/download:")


panel(df, zona_txt, fecha)

with st.expander("¿Por qué no enviar simplemente el pronóstico central?", icon=":material/lightbulb:"):
    st.markdown(
        "El pronóstico central (mediana) se queda corto la mitad de las veces. Si quedarse corto cuesta más que pasarse, "
        "esa mitad pesa más en el costo total. Por eso se elige el cuantil que equilibra los dos errores. "
        "Es el problema del *vendedor de periódicos*: cuántos periódicos comprar cuando sobrar y faltar cuestan distinto."
    )
