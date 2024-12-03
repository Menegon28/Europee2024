import polars as pl
import statsmodels.api as sm
import altair as alt
import streamlit as st
import math
import voti_tidy as vt

votiModel = vt.votiPerc.with_columns(
    logELETTORI=pl.col("ELETTORI").log(),
    M_PERC=pl.col("ELETTORI_M") / pl.col("ELETTORI") * 100
)

def prediction(reg: str, elett: int, m_perc: float, affl: float):
    if reg == "ITALIA":
        voti_pred = votiModel
    else:
        voti_pred = votiModel.filter(pl.col("REGIONE") == reg)

    pred = []
    for i in range(len(vt.partitiPlot)):
        partito = vt.partiti[i]
        vote_share = voti_pred.get_column(partito).to_list()
        espl = sm.add_constant(voti_pred.select(["logELETTORI", "M_PERC", "AFFLUENZA"]))
        mod_compl = sm.OLS(vote_share, espl).fit()
        beta = mod_compl.params

        pred.append(round(beta[0] + beta[1] * math.log(elett) + beta[2] * m_perc + beta[3] * affl, 2))
    pred.append(100-sum(pred))
    pred_df = pl.DataFrame(
        {
            "PARTITO" : vt.partitiPlot + ["ALTRI"],
            "PREVISIONE" : pred
        }
    )

    pie = (
        alt.Chart(pred_df)
        .mark_arc()
        .encode(
            alt.Theta("PREVISIONE"),
            alt.Color("PARTITO", scale=alt.Scale(domain=vt.partitiPlot+["ALTRI"], range=vt.colors+["gray"]))
        )
    )
    return pie



def make_model_graph(var: str, log: bool, size: bool, title: str, partito: str):
    intercept = sm.add_constant(votiModel.get_column(f"log{var}" if log else var).to_list())
    vote_share = votiModel.get_column(partito).to_list()
    model = sm.OLS(vote_share, intercept).fit()

    plot_prev = votiModel.with_columns(
        prev=model.predict(intercept)
    )

    base = (
        alt.Chart(plot_prev)
        .mark_circle()
        .encode(
            alt.X(var, scale=alt.Scale(type='log') if log else alt.Scale(type="linear",zero=False),
                  axis=alt.Axis(title=title)),
            # altair ha bisogno di escapare le quotes altrimenti panica (closed issue 888), dunque sostiamo direttamente qua
            alt.Y(partito.replace("'", "\\'"), axis=alt.Axis(title=f"% di {partito.title()}")),
            alt.Size("ELETTORI") if size else alt.Size(),
            alt.Tooltip("COMUNE")
        )
    )

    trend = (
        alt.Chart(plot_prev)
        .mark_line(color="red")
        .encode(
            alt.X(var, scale=alt.Scale(type="log")) if log else alt.X(var),
            alt.Y("prev")
        )
    )

    st.altair_chart(base + trend, use_container_width=True)
    st.latex(
        rf"""
        R^2: {model.rsquared:.3f} \quad
        p\text{{-value dell'esplicativa: }} {model.pvalues[1]:.2e} \quad
        \text{{coeff. angolare: }} {model.params[1]:.2f} 
        """
    )


