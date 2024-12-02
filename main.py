import polars as pl
import streamlit as st
import altair as alt
import statsmodels.api as sm
import statsmodels.formula.api as smf
import voti_tidy as vt
import mappe

# st.write("votiAbs")
# st.dataframe(vt.votiAbs)
# st.write("votiPerc")
# st.dataframe(vt.votiPerc)
# st.html("markdwon.html")
"""
# Europee 2024 in Italia
## Organizzazione del DataFrame
I dati dei risultati di ogni elezione in Italia, a partire dal referendum del 1946 sull'istituzione della Repubblica,
sono disponibili sul sito [Eligendo](https://elezionistorico.interno.gov.it/eligendo/opendata.php),
gestito dal Ministero dell'Interno.
Scaricando i dati, otteniamo inizialmente una tabella che appare nel formato seguente (riportiamo le prime righe):
"""
st.dataframe(vt.get_raw_data().head(4))
# st.write(vt.get_raw_data().glimpse())
"""
In questo formato i dati non sono _tidy_. Infatti, vogliamo che l'unità statistica sia il singolo comune
e il numero di voti di ogni lista sia ognuno una variabile. Pertanto, effettiamo un pivot sulla colonna
_LISTA_ e apportiamo altre piccole modifiche. In questo modo, il dataframe risulta organizzato come
"""
st.dataframe(vt.votiAbs.head(4))
"""
Si osserva che vi sono 7896 comuni e 15 partiti totali, non tutti presenti in ogni circoscrizione.
Si noti la differenza tra un valone _NULL_, che indica che il partito non era candidato in quel comune
(perché non si è candidato in quella circoscrizione)
e il valore 0 che indica che il partito non ha raccolto voti nel comune indicato (ma era candidato).
"""
"""
## Analisi descrittive
Per prima cosa, vediamo cosa i dati ci dicono sui risultati dei singoli partiti. Questi possono essere esplorati
a livello nazionale, di circoscrizione, regionale, provinciale o comunale.
"""
st.write("### Ridgeline plot")
regioni = sorted(vt.votiPerc["REGIONE"].unique().to_list())
partitoDistr = st.selectbox("Ripartizione geografica", ["ITALIA"] + regioni, key="distr")

# usiamo votiPercPlot come dataframe temporaneo, da manipolare di volta in volta per creare i singoli grafici
votiPercPlot = (
    vt.votiPerc.select(
        ["REGIONE", "PROVINCIA", "COMUNE"] + vt.partitiPlot
    ).unpivot(
        on=vt.partitiPlot,
        index=["REGIONE", "PROVINCIA", "COMUNE"],
        variable_name="LISTA",
        value_name="VOTI"
    ).filter(
        pl.col("LISTA").is_in(vt.partitiPlot)
    )
)

# per "ITALIA" teniamo il dataframe intero, altrimenti lo filtriamo secondo quanto chiesto
# usiamo nome diverso per evitare il rischio di riusare un dataframe filtrato più avanti
votiReg = votiPercPlot
if partitoDistr != "ITALIA":
    votiReg = votiPercPlot.filter(pl.col("REGIONE") == partitoDistr)

distrChart = (
    alt.Chart(votiReg)
    .transform_density(
        density="VOTI",
        groupby=["LISTA"],
        as_=["VOTI", "density"]
    ).mark_area(
        opacity=0.7
    ).encode(
        alt.X("VOTI:Q", title="Percentuale di voto", scale=alt.Scale(domain=[0, 60])),
        alt.Y("density:Q", title="Densità", scale=alt.Scale(domain=[0, 0.3])),
        alt.Row("LISTA:N", title=None, sort=vt.partitiPlot),
        alt.Color("LISTA:N", scale=alt.Scale(domain=vt.partitiPlot), legend=alt.Legend(orient="none", legendX=720))
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

### scatterplots a 2 vabiabili
st.write("## Alcune ipotesi di ricerca")
# slider per gli scatterplot
partitoPop = st.selectbox("Partito di cui mostrare i grafici:", vt.partiti_ext, key="scatter")

# aggiungiamo una colonna log(ELETTORI) per usarla come esplicativa di un modello lineare
votiPercPlot = vt.votiPerc.with_columns(
    logELETTORI=pl.col("ELETTORI").log(),
    M_PERC=pl.col("ELETTORI_M") / pl.col("ELETTORI") * 100
)

def make_model_graph(var: str, log: bool, size: bool, title: str):
    intercept = sm.add_constant(votiPercPlot.get_column(f"log{var}" if log else var).to_list())
    vote_share = votiPercPlot.get_column(partitoPop).to_list()
    model = sm.OLS(vote_share, intercept).fit()

    plot_prev = votiPercPlot.with_columns(
        prev=model.predict(intercept)
    )

    base = (
        alt.Chart(plot_prev)
        .mark_circle()
        .encode(
            alt.X(var, scale=alt.Scale(type='log') if log else alt.Scale(type="linear",zero=False),
                  axis=alt.Axis(title=title)),
            # altair ha bisogno di escapare le quotes altrimenti panica (closed issue 888), dunque sostiamo direttamente qua
            alt.Y(partitoPop.replace("'", "\\'"), axis=alt.Axis(title=f"% di {partitoPop.title()}")),
        alt.Size("ELETTORI") if size else alt.Size()
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

st.write("### Scatterplot log(numero di elettori) - share di voto")
make_model_graph("ELETTORI", True, False,f"% di {partitoPop.title()}")
st.write("### Scatterplot percentuale di elettori maschi - share di voto")
make_model_graph("M_PERC", False, True,"Percentuale di elettori maschi")
st.write("### Scatterplot affluenza - share di voto")
make_model_graph("AFFLUENZA", False, True, "Affluenza percentuale")

# da sistemare
"""
Per i partiti maggiori, la correlazione è significativa per tutti tranne Forza Italia, con p-values che 
permettono di rifiutare l'ipotesi nulla di incorrelazione tra media e percentuali di voto senza dubbio.
Inoltre, notiamo che la correlazione è positiva per i partiti di centro e centrosinistra, in particolare 
per PD e M5S, ma anche per AVS, AZ, SUE, mentre è negativa per i partiti di centrodestra, ovvero Lega e FdI. 
La non significatività per FI è del tutto particolare.

Per i dati così come sono, valutando anche i relativi qqplot in R, rifiutiamo l'ipotesi di normalità dei dati per quasi 
tutti i partiti. Ciò è anche dovuto alla presenza di outlier forti rispetto a media e varianza stimate delle variabili. 
Inoltre, il supporto qui considerato è l'intervallo [0, 100], dunque incompatibile con una distribuzione normale per medie 
vicine ad uno degli estremi. Si noti a questo proposito che la distribuzione più vicina ad una normale è quella di 
Fratelli d'Italia: ciò è dovuto al fatto che la media della variabile è ragionevolmente vicina al centro dell'intervallo.
"""

### Mappe
"""
## Mappe dei risultati
Dall'interfaccia, selezionare un __partito__ e un __intervallo della percentuale di voti__. 
Si ottiene così una mappa che indica tutti i comuni in cui il paritito selezionato ha ottenuto una percentuale 
di voti compatibile con l'intervallo selezionato. È anche possibile visualizzare l'elenco di questi comuni in calce.
"""

# permettiamo all'utente di filtrare il dataframe
partitoMappa = st.selectbox("Partito", vt.partiti_ext, key="mappa")
minPerc, maxPerc = st.slider("Seleziona l'intevallo percentuale", 0, 100, value=(0, 100))

votiCoordFilter = (
    mappe.votiCoord
    .drop(["CIRCOSCRIZIONE", "ELETTORI_M"])
    .filter(pl.col(partitoMappa) >= minPerc)
    .filter(pl.col(partitoMappa) <= maxPerc)
    .sort(["REGIONE", "PROVINCIA", "COMUNE"])
)

# preventiamo che venga sollevata una eccezione nel tentativo di creare una mappa da un dataframe vuoto
if votiCoordFilter.is_empty():
    st.write("Nessun comune corrispondente alla descrizione")
else:
    st.map(votiCoordFilter,
           latitude="latitude",
           longitude="longitude")
    st.write("Comuni corrispondenti e percentuale dei voto per partito")
    st.write(votiCoordFilter.drop(["latitude", "longitude"]))

"""
__Nota metodologica__: Questa mappa è stata realizzata tramite un _inner join_ tra i dati dei risultati 
elettorali e di un database contenente i valori di latitudine e longitudine di (quasi) tutti i comuni italiani. 
Come è naturale, questo ha comportato una perdita di informazioni dovuta a qualche differenza nei nomi 
come indicati nelle due tabelle. Si sono apportate alcune correzioni di base (e.g. accenti, omonimie) 
e si è proceduto manualmente per alcuni comuni più grandi. Al momento, circa 700 comuni non sono riportati, 
(quasi) tutti al di sotto dei 30 mila elettori totali. Alcuni rari casi di omonimia permangono e potrebbero causare 
la visualizzazione di qualche punto anomalo.
"""

chLiv = st.selectbox("Livello", ["REGIONE", "PROVINCIA"], key="chLivello")
# il livello comune è tralasciato sia perché supera i 5000 elementi di limite di default di Altair, sia perché il
# mismatch dei nomi tra i due dataframe renderebbe molti comuni non visualizzati
chPart = st.selectbox("Partito", vt.partiti, key="chPartito").replace("'", "\\'")

# per ottenere le percentuali per regione/provincia, dobbiamo tornare ai valori assoluti
# (la percentuale media non è la media delle percentuali dei comuni)
votiAbsGrouped = (
    vt.votiAbs
    .with_columns(
        pl.col(chLiv).str.to_titlecase()
    )
    .group_by(chLiv)
    .sum()
)

votiPercPlot = votiAbsGrouped.select(["REGIONE", "PROVINCIA"])
for partito in vt.partiti:
    votiPercPlot = votiPercPlot.with_columns(
        [(votiAbsGrouped.get_column(partito) / votiAbsGrouped.get_column("VOTI_VALIDI") * 100).round(2).alias(partito)]  # da risolvere la questione round()
    )

# alcune provincie hanno nomi non coincidenti nei due dataframe, modifichiamo per semplicità quelli in votiPercPlot
votiPercPlot = mappe.reg_prov_fix(votiPercPlot)

geoIT, labelLiv = mappe.get_topo_data(chLiv)
# st.dataframe(votiPercPlot)
choropleth = (
    alt.Chart(geoIT)
    .mark_geoshape()
    .transform_lookup(
        lookup=labelLiv,
        from_=alt.LookupData(data=votiPercPlot, key=chLiv, fields=[chPart])
    )
    .encode(
        alt.Color(f"{chPart}:Q"),
        tooltip=[
            alt.Tooltip(f"{labelLiv}:N", title=chLiv),
            alt.Tooltip(f"{chPart}:Q", title=f"% {chPart}", format=".2f")
        ],
    )
)
st.altair_chart(choropleth, use_container_width=True)
