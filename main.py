import polars as pl
import streamlit as st
import altair as alt
import statsmodels.api as sm
import statsmodels.formula.api as smf
import voti_tidy as vt
import mappe
import modelli as mod

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
circoscrizioni = sorted(vt.votiPerc.get_column("CIRCOSCRIZIONE").unique().to_list())
df_circ = st.selectbox("Circoscrizione", ["ITALIA"]+circoscrizioni, key="df_circ")
if df_circ == "ITALIA":
    votiPercDf = vt.voti_grouped_by("ITALIA")
else:
    regioni = sorted(
        vt.votiPerc
        .filter(pl.col("CIRCOSCRIZIONE") == df_circ)
        .get_column("REGIONE")
        .unique().to_list())
    df_reg = st.selectbox("Regione", ["TUTTE"] + regioni, key="df_reg")

    if df_reg == "TUTTE":
        votiPercDf = vt.voti_grouped_by("CIRCOSCRIZIONE", df_circ)
    else:
        province = sorted(
            vt.votiPerc
            .filter(pl.col("REGIONE") == df_reg)
            .get_column("PROVINCIA")
            .unique().to_list())
        df_prov = st.selectbox("Provincia", ["TUTTE"] + province, key="df_prov")

        if df_prov == "TUTTE":
            votiPercDf = vt.voti_grouped_by("REGIONE", df_reg)
        else:
            comuni = sorted(
                vt.votiPerc
                .filter(pl.col("PROVINCIA") == df_prov)
                .get_column("COMUNE")
                .unique().to_list())
            df_com = st.selectbox("Comune", ["TUTTI"] + comuni, key="df_com")

            if df_com == "TUTTI":
                votiPercDf = vt.voti_grouped_by("PROVINCIA", df_prov)
            else:
                votiPercDf = vt.votiPerc.filter(pl.col("COMUNE") == df_com)

votiPercDf = (
    votiPercDf
    .unpivot(
        on=vt.partiti,
        variable_name="LISTA",
        value_name="PERC"
    )
    .filter(
        pl.col("PERC").is_not_null()
    )
)

bar_chart = (
    alt.Chart(votiPercDf)
    .mark_bar()
    .encode(
        alt.X("PERC"),
        alt.Y("LISTA", sort="-x")
    )
)

st.altair_chart(bar_chart, use_container_width=True)
st.write("### Ridgeline plot")
regioni = sorted(vt.votiPerc.get_column("REGIONE").unique().to_list())
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
        alt.Y("density:Q", title=None, axis=None, scale=alt.Scale(domain=[0, 0.3])),
        alt.Row("LISTA:N", title=None, sort=vt.partitiPlot, header=alt.Header(labelAngle=0, labelAlign="left")),
        # alt.Facet("LISTA:N", title=None, sort=vt.partitiPlot, header=alt.Header(labelAlign='left')),
        alt.Color("LISTA:N", scale=alt.Scale(domain=vt.partitiPlot,range=vt.colors))  # legend=alt.Legend(orient="none", legendX=720)
    ).properties(
        height=75,
        bounds="flush"
    )
)

st.altair_chart(distrChart, use_container_width=True)
"""
Ad essere rigorosi, per i dati così presentati, valutando anche i relativi qqplot in R, rifiutiamo l'ipotesi di normalità per quasi 
tutti i partiti. Ciò è principalmente dovuto alla presenza di outlier forti rispetto a media e varianza stimate delle variabili. 
Inoltre, il supporto qui considerato è l'intervallo [0, 100], dunque difficilmente compatibile con una distribuzione normale per medie 
vicine ad uno degli estremi. Si noti a questo proposito che la distribuzione più vicina ad una normale è quella di 
Fratelli d'Italia: ciò è dovuto al fatto che la media della variabile è ragionevolmente vicina al centro dell'intervallo.

Ciò detto, al netto delle code la normalità approssimata è una assunzione plausibile, come si può ben vedere dall'andamento
a gaussiana delle distribuzioni.
"""

### scatterplots a 2 vabiabili
"""
## Alcune ipotesi di ricerca

Analizziamo il rapporto tra alcune variabili e la percentuale di voto partito per parito
"""
# slider per gli scatterplot
partitoPop = st.selectbox("Partito di cui mostrare i grafici:", vt.partiti_ext, key="scatter")

# aggiungiamo una colonna log(ELETTORI) per usarla come esplicativa di un modello lineare
votiPercPlot = vt.votiPerc.with_columns(
    logELETTORI=pl.col("ELETTORI").log(),
    M_PERC=pl.col("ELETTORI_M") / pl.col("ELETTORI") * 100
)



st.write("### Scatterplot log(numero di elettori) - share di voto")
mod.make_model_graph("ELETTORI", True, False,f"% di {partitoPop.title()}", partitoPop)
st.write("### Scatterplot percentuale di elettori maschi - share di voto")
mod.make_model_graph("M_PERC", False, True,"Percentuale di elettori maschi", partitoPop)
st.write("### Scatterplot affluenza - share di voto")
mod.make_model_graph("AFFLUENZA", False, True, "Affluenza percentuale", partitoPop)
# da sistemare
"""
In generale, notiamo che i partiti di centrodestra ottengono risultati migliori nei comuni meno popolosi, 
con percentuali di elettori maschi alte e affluenza alta. I trend di Fratelli d'Italia e Lega si assomigliano abbastanza,
mentre quello di Forza Italia non segue l'andamento del resto della coalizione. In particolare, la grandezza
del comune non appare significativa, e i trend per le altre due esplicative vanno in direzione opposta (benché debolmente)
a quanto visto per Lega e FdI. Si potrebbe ipotizzare che tale comportamento sia dovuto al fatto che Forza Italia, seguendo
politiche più centriste, faccia riferimento ad un elettorato con caratteristiche diverse.

Per quanto riguarda il centrosinistra, si nota un andamento sostanzialmente opposto, come d'altro canto è naturale
considerando che le due coalizioni assieme raccolgono quasi il 90% dei consensi nazionali.
"""


"""
## Il comune medio

Come voterebbe, mediamente, un comune di una certa regione, fissando numero di elettori, percentuale di
elettori maschi e affluenza? Modificando i valori a piacere, si può vedere come cambia la ripartizione dei voti.
Da un'idea del [NYTimes](https://www.nytimes.com/interactive/2019/08/08/opinion/sunday/party-polarization-quiz.html),
rielaborata secondo i (pochi) dati a disposizione.

"""
regione = st.selectbox("Regione", ["ITALIA"] + regioni, key="mod_elettori")
elettori = st.number_input("Numero di elettori del comune", min_value=200, max_value=2000000, value=100000, key="mod_reg")
m_perc = st.number_input("Percentuale di elettori maschi nel comune", min_value=0, max_value=100, value=50, key="mod_m")
affluenza = st.number_input("Affluenza registrata nel comune", min_value=0, max_value=100, value=50, key="mod_affl")
st.altair_chart(mod.prediction(regione, elettori, m_perc, affluenza), use_container_width=True)
"""
__Nota metodologica:__ L'idea di base sarebbe stata quella di modellare l'elettore medio in base alle sue caratteristiche.
Tale analisi sarebbe possibile avendo a disposizione i valori di un campione di elettori.
Tuttavia, per i dati a disposizione, in cui l'unità statistica è il singolo comune, questo non è realizzabile se non
facendo assunzioni piuttosto irrealistiche. 

Ricorrendo al metodo di stima _GLS_, le assunzioni fatte dal modello sono piuttosto deboli.
Sotto l'ipotesi di normalità, che come si è visto appare ragionevole, le tre esplicative appaiono globalmente 
significative, con p-values estremamente piccoli.
Il modello non ammette interazione tra le variabili esplicative, dunque l'effetto, ad esempio, dell'aumento di un punto 
dell'affluenza è considerato costante qualsiasi sia il valore assunto dalle altre esplicative.
"""
# Il modello assume distribuzione normale per lo share dei voti dei partiti, che, come si è visto, appare ragionevole.
# Inoltre, assume omoschedasticità (giustificata dalla trasformazione logaritmica dell'esplicativa _ELETTORI_) e
# incorrelazione tra un comune e l'altro.
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
__Nota metodologica:__ Questa mappa è stata realizzata tramite un _inner join_ tra i dati dei risultati 
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
