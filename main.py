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
votiPercPlot = vt.votiPerc.with_columns(logELETTORI=pl.col("ELETTORI").log())
scatter1 = px.scatter(votiPercPlot, x="logELETTORI", y=partitoPop, trendline="ols", trendline_color_override='red')
st.plotly_chart(scatter1)

# scatter_alt = alt.Chart(votiPercPlot, height=460, width=720).mark_circle(size=60).encode(
#     x="logELETTORI:Q",
#     y=f"FRATELLI D'ITALIA:Q",
# )
# st.write(scatter_alt)

# per ricavare R^2, p-value e coeff. angolare sviluppiamo un vero e proprio modello lineare, in modo da replicare
# dei risultati che sarebbero facilmente ottenibili in R
logEl = sm.add_constant(votiPercPlot["logELETTORI"].to_list())
voteShare = votiPercPlot[partitoPop].to_list()
model = sm.OLS(voteShare, logEl).fit()
st.write(f"R^2: {model.rsquared:.3f}")
st.write(f"p-value della variabile esplicativa logElettori: {model.pvalues[1]}")
st.write(f"Coefficiente angolare: {model.params[1]:.3f}")

st.write("Per i partiti maggiori, la correlazione è significativa per tutti tranne Forza Italia, con p-values che "
         "permettono di rifiutare l'ipotesi nulla di incorrelazione tra media e percentuali di voto senza dubbio.")
st.write("Inoltre, notiamo che la correlazione è positiva per i partiti di centro e centrosinistra, in particolare "
         "per PD e M5S, ma anche per AVS, AZ, SUE, mentre è negativa per i partiti di centrodestra, ovvero Lega e FdI. "
         "La non significatività per FI è del tutto particolare.")

st.write("### Scatterplot percentuale di elettori maschi - share di voto")
scatter2 = px.scatter((vt.votiPerc
                       .with_columns(M_PERC=pl.col("ELETTORI_M")/pl.col("ELETTORI"))),
                      x="M_PERC", y=partitoPop, trendline="ols", trendline_color_override='red', marginal_x="violin")
st.plotly_chart(scatter2)

# st.write("----------------------------")
# glm_model = smf.glm(formula="FRATELLI D'ITALIA ~ M_PERC", data=vt.votiPerc, family=sm.families.Binomial())
# glm_results = glm_model.fit()
# st.write(glm_results.summary())


st.write("### Test di normalità")
partitoDistr = st.selectbox("Partito", vt.partiti, key="distr")

hist_data = vt.votiPerc[partitoDistr].drop_nulls().to_list()
distr = ff.create_distplot([hist_data], ["Densità"], curve_type="normal")
st.plotly_chart(distr)
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

