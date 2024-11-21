import streamlit as st
import polars as pl
import voti_tidy as vt
import coord
import plotly.figure_factory as ff
import plotly.express as px
import statsmodels.api as sm
import statsmodels.formula.api as smf
import altair as alt


st.write("## Analisi iniziale")
st.write("Inizialmente la tabella appare nel formato seguente (riportiamo le prime righe): ")
st.write(vt.get_raw_data().head(4))
st.write("In questo formato i dati non sono _tidy_. Infatti, vogliamo che l'unità statistica sia il singolo comune"
         "e il numero di voti di ogni lista sia ognuno una variabile. Pertanto, effettiamo un pivot sulla colonna"
         " _DESCLISTA_ e apportiamo altre piccole modifiche. In questo modo, il dataframe risulta organizzato come")
st.write(vt.votiAbs.head(4))
st.write("Si osserva che sono presenti 7896 comuni e 15 partiti totali, non tutti presenti in ogni circoscrizione. "
         "Si noti la differenza tra un valone _NULL_, che indica che il partito non era candidato in quel comune "
         "(perché non si è candidato in quella circoscrizione) "
         "e il valore 0 che indica che il partito non ha raccolto voti nel comune indicato (ma era candidato)")

st.write("## Alcune ipotesi di ricerca")
# slider per gli scatterplot
partitoPop = st.selectbox("Partito", vt.partiti_ext, key="scatter")

st.write("### Scatterplot log(numero di elettori) - share di voto")

# aggiungiamo una colonna log(ELETTORI) per usarla come esplicativa di un modello lineare
votiPercPlot = vt.votiPerc.with_columns(
    logELETTORI=pl.col("ELETTORI").log(),
    M_PERC=pl.col("ELETTORI_M")/pl.col("ELETTORI")
)

# creiamo il modello
logEl = sm.add_constant(votiPercPlot["logELETTORI"].to_list())
voteShare = votiPercPlot[partitoPop].to_list()
modelPop = sm.OLS(voteShare, logEl).fit()

votiPercPlot = votiPercPlot.with_columns(
    prev=modelPop.predict(logEl)
)

basePop = (
    alt.Chart(votiPercPlot)
    .mark_circle()
    .encode(
        alt.X("ELETTORI", scale=alt.Scale(type='log'), axis=alt.Axis(title="Numero di elettori")),
        # altair ha bisogno di escapare le quotes altrimenti panica (closed issue 888), dunque sostiamo direttamente qua
        alt.Y(partitoPop.replace("'", "\\'"), axis=alt.Axis(title=f"% di {partitoPop.title()}"))
    )
)

trendPop = (alt.Chart(votiPercPlot)
             .mark_line(color="red")
             .encode(
    alt.X("ELETTORI", scale=alt.Scale(type="log")),
    alt.Y("prev")
)
)

popPlot = (basePop + trendPop)
st.altair_chart(popPlot, use_container_width=True)


st.write(f"R^2: {modelPop.rsquared:.3f}")
st.write(f"p-value della variabile esplicativa logElettori: {modelPop.pvalues[1]}")
st.write(f"Coefficiente angolare: {modelPop.params[1]:.3f}")

st.write("Per i partiti maggiori, la correlazione è significativa per tutti tranne Forza Italia, con p-values che "
         "permettono di rifiutare l'ipotesi nulla di incorrelazione tra media e percentuali di voto senza dubbio.")
st.write("Inoltre, notiamo che la correlazione è positiva per i partiti di centro e centrosinistra, in particolare "
         "per PD e M5S, ma anche per AVS, AZ, SUE, mentre è negativa per i partiti di centrodestra, ovvero Lega e FdI. "
         "La non significatività per FI è del tutto particolare.")

########################
st.write("### Scatterplot percentuale di elettori maschi - share di voto")

# creiamo il modello
MPerc = sm.add_constant(votiPercPlot["M_PERC"].to_list())
modelPop = sm.OLS(voteShare, MPerc).fit()

votiPercPlot = votiPercPlot.with_columns(
    prev=modelPop.predict(MPerc)
)

baseSex = (
    alt.Chart(votiPercPlot)
    .mark_circle()
    .encode(
        alt.X("M_PERC", axis=alt.Axis(title="Percentuale di elettori maschi")).scale(zero=False),
        # altair ha bisogno di escapare le quotes altrimenti panica (closed issue 888), dunque sostiamo direttamente qua
        alt.Y(partitoPop.replace("'", "\\'"), axis=alt.Axis(title=f"% di {partitoPop.title()}")),
        alt.Size("ELETTORI")
    )
)

trendSex = (alt.Chart(votiPercPlot)
            .mark_line(color="red")
            .encode(
    alt.X("M_PERC"),
    alt.Y("prev")
)
)

sexPlot = (baseSex + trendSex)
st.altair_chart(sexPlot, use_container_width=True)



st.write("### Test di normalità")
regioni = sorted(votiPercPlot["REGIONE"].unique().to_list())
partitoDistr = st.selectbox("Partito", ["ITALIA"] + regioni, key="distr")

# hist_data = vt.votiPerc[partitoDistr].drop_nulls().to_list()
# distr = ff.create_distplot([hist_data], ["Densità"], curve_type="normal")
# st.plotly_chart(distr)


partitiPlot = [
        "FRATELLI D'ITALIA",
        "PARTITO DEMOCRATICO",
        "MOVIMENTO 5 STELLE",
        "FORZA ITALIA - NOI MODERATI - PPE",
        "LEGA SALVINI PREMIER",
        "ALLEANZA VERDI E SINISTRA",
        "STATI UNITI D'EUROPA",
        "AZIONE - SIAMO EUROPEI"
    ]
votiPercPlot = (
    votiPercPlot.select(
        ["REGIONE", "COMUNE"] + partitiPlot
    ).unpivot(
        on=partitiPlot,
        index=["REGIONE", "COMUNE"],
        variable_name="LISTA",
        value_name="VOTI"
    ).filter(
        pl.col("LISTA").is_in(partitiPlot)
    )
)

if partitoDistr != "ITALIA":
    votiPercPlot = votiPercPlot.filter(pl.col("REGIONE") == partitoDistr)

distrChart = (
    alt.Chart(votiPercPlot)
    .transform_density(
        density="VOTI",
        groupby=["LISTA"],
        as_=["VOTI", "density"]
    ).mark_area(
        opacity=0.7
    ).encode(
        alt.X("VOTI:Q", title="Percentuale di voto", scale=alt.Scale(domain=[0, 60])),
        alt.Y("density:Q", title="Densità", scale=alt.Scale(domain=[0, 0.3])),
        alt.Row("LISTA:N", title=None, sort=partitiPlot),
        alt.Color("LISTA:N", legend=alt.Legend(orient="none", legendY=650))
    ).properties(
        height=75,
        bounds="flush"
    ).configure_facet(
        spacing=0
    ).configure_view(
        stroke=None
    ).configure_title(
        anchor="end"
    )
)

st.altair_chart(distrChart, use_container_width=True)





st.write("Per i dati così come sono, valutando anche i relativi qqplot in R, rifiutiamo l'ipotesi di "
         "normalità dei dati per quasi tutti i partiti. Ciò è anche dovuto alla presenza di outlier forti rispetto "
         "a media e varianza stimate delle variabili. Inoltre, il supporto qui considerato è l'intervallo [0, 100], "
         "dunque incompatibile con una distribuzione normale per medie vicine ad uno degli estremi. "
         "Si noti a questo proposito che la distribuzione più vicina ad una normale è quella di Fratelli d'Italia: "
         "ciò è dovuto al fatto che la media della variabile è ragionevolmente vicina al centro dell'intervallo.")


st.write("## Mappe dei risultati")
st.write("Dall'interfaccia, selezionare un __partito__ e un __intervallo della percentuale di voti__. "
         "Si ottiene così una mappa che indica tutti i comuni in cui il paritito selezionato ha ottenuto una percentuale "
         "di voti compatibile con l'intervallo selezionato. È anche possibile visualizzare l'elenco di questi comuni in calce.")

# permettiamo all'utente di filtrare il dataframe
partitoMappa = st.selectbox("Partito", vt.partiti_ext, key="mappa")
(minPerc, maxPerc) = st.slider("Seleziona l'intevallo percentuale", 0, 100, value=(0, 100))

votiCoordFilter = (coord.votiCoord
                   .drop(["CIRCOSCRIZIONE", "ELETTORI_M"])
                   .filter(pl.col(partitoMappa) >= minPerc)
                   .filter(pl.col(partitoMappa) <= maxPerc)
                   .sort(["REGIONE", "PROVINCIA", "COMUNE"]))

# preventiamo che venga sollevata una eccezione nel tentativo di creare una mappa da un dataframe vuoto
if votiCoordFilter.is_empty():
    st.write("Nessun comune corrispondente alla descrizione")
else:
    st.map(votiCoordFilter,
           latitude="latitude",
           longitude="longitude")
    st.write("Comuni corrispondenti e percentuale dei voto per partito")
    st.write(votiCoordFilter.drop(["latitude", "longitude"]))

st.write("__Nota metodologica__: Questa mappa è stata realizzata tramite un _inner join_ tra i dati dei risultati "
         "elettorali e di un database contenente i valori di latitudine e longitudine di (quasi) tutti i comuni italiani. "
         "Come è naturale, questo ha comportato una perdita di informazioni dovuta a qualche differenza nei nomi "
         "come indicati nelle due tabelle. Si sono apportate alcune correzioni di base (e.g. accenti, omonimie) "
         "e si è proceduto manualmente per alcuni comuni più grandi. Al momento, circa 700 comuni non sono riportati, "
         "(quasi) tutti al di sotto dei 30 mila elettori totali. Alcuni rari casi di omonimia permangono e potrebbero causare "
         "la visualizzazione di qualche punto anomalo.")

