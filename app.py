import polars as pl
import streamlit as st
import altair as alt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import numpy as np
import voti_tidy as vt
import mappe
import modelli as mod


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
In questo formato i dati non sono _tidy_. Infatti, le caratteristiche del comune sono ripetute tante volte
quante il numero di partiti candidati. Vogliamo, invece, che l'unità statistica sia il singolo comune
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

### Esplorare il dataset
Selezionando un comune, verrà anche mostrato il suo "__comune gemello__", ovvero quello in cui i risultati sono stati,
in percentuale più simili. Due comuni sono detti più simili se la loro distanza euclidea tra i partiti che
nazionalmente hanno superato il 3% è piccola.
"""

# dato un comune, trova e restituisce il comune con la minor distanza euclidea dei voti dei partiti in vt.partitiPlot
def find_closer(comune:str):
    comune_row = vt.votiPerc.filter(pl.col("COMUNE")==comune).row(0)
    closest = "NESSUNO"
    min_dist = 100000
    for row in vt.votiPerc.iter_rows():
        dist = 0
        if row[3] != comune:
            for i in range(7,15):
                dist += (row[i] - comune_row[i]) ** 2
            if dist < min_dist:
                min_dist = dist
                closest = (row[3], row[2])

    return closest


df_com = None  # per evitare che sia non definito nel comune gemello
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


# bar chart dei voti percentuali per partito
# usiamo votiPercPlot come dataframe temporaneo, da manipolare di volta in volta per creare i singoli grafici
votiPercPlot = (
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
    alt.Chart(votiPercPlot)
    .mark_bar()
    .encode(
        alt.X("PERC:Q"),
        alt.Y("LISTA:N", sort="-x")
    )
)

text_bar = (
    bar_chart
    .mark_text(
        align="left",
        baseline="middle",
        dx=3
    )
    .encode(
        text="PERC:Q"
    )
)

st.altair_chart(bar_chart + text_bar, use_container_width=True)
if df_com  is not None and df_com != "TUTTI":
    gemello = find_closer(df_com)
    st.write(f"Il comune gemello è __{gemello[0].title()}__, nella provincia di {gemello[1].title()}")

"""
### Ridgeline plot

Vediamo come cambia la distribuzione della percentuale dei voti validi raccolta per partito e per regione.
Come sempre, l'unità statistica è il signolo comune. Si noti che i partiti che hanno raccolto meno preferenze a livello
nazionale hanno una distribuzione più stretta (ovvero con minor varianza, in termini assoluti) e dunque il picco della
distribuzione è più alto. Per uniformità, sono riportati solo i partiti che hanno superato il 3% a livello nazionale.
"""
regioni = sorted(vt.votiPerc.get_column("REGIONE").unique().to_list())
partitoDistr = st.selectbox("Ripartizione geografica", ["ITALIA"] + regioni, key="distr")

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
        alt.Color("LISTA:N", scale=alt.Scale(domain=vt.partitiPlot,range=vt.colors),legend=None)
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

Analizziamo il rapporto tra alcune variabili e la percentuale di voto partito per parito.
Qui e nel seguito, l'opzione _centrodestra_ si riferisce a FdI, Lega e FI, mentre _centrosinistra_ a PD, M5S e AVS.
"""
# slider per gli scatterplot
partitoPop = st.selectbox("Partito di cui mostrare i grafici:", vt.partiti_ext, key="scatter")

st.write("### Scatterplot log(numero di elettori) - share di voto")
mod.make_model_graph("ELETTORI", True, False,f"Numero di elettori nel comune", partitoPop)
st.write("### Scatterplot percentuale di elettori maschi - share di voto")
mod.make_model_graph("M_PERC", False, True,"Percentuale di elettori maschi", partitoPop)
st.write("### Scatterplot affluenza - share di voto")
mod.make_model_graph("AFFLUENZA", False, True, "Affluenza percentuale", partitoPop)
# da sistemare
"""
In generale, notiamo che i partiti di centrodestra ottengono risultati migliori nei comuni meno popolosi, 
con percentuali di elettori maschi alte e affluenza alta. I trend di Fratelli d'Italia e Lega si assomigliano abbastanza,
mentre quello di Forza Italia non segue l'andamento del resto della coalizione. Per questi ultimi, in particolare, la grandezza
del comune non appare significativa, e i trend per le altre due esplicative vanno in direzione opposta (benché debolmente)
rispetto a quanto visto per Lega e FdI. Si potrebbe ipotizzare che tale comportamento sia dovuto al fatto che Forza Italia, seguendo
politiche più centriste, faccia riferimento ad un elettorato con caratteristiche diverse.

Per quanto riguarda il centrosinistra, si nota un andamento sostanzialmente opposto, come d'altro canto è naturale
considerando che le due coalizioni assieme raccolgono quasi il 90% dei consensi nazionali.

### Il modello completo
Con le variabili esplicative, il modello completo risulta
"""
partitoModel = st.selectbox("Partito di cui visualizzare il modello completo:", vt.partitiPlot, key="compl_model")
st.write(mod.make_compl_model(partitoModel).summary())
"""
Il warning visualizzato non è rilevante ai nostri fini. Molti p-values sono vicini a 0, indicando che le variabili
considerate sono significative globalmente. Per alcuni partiti, alcune esplicative non risultano significative,
tuttavia non è opportuno modificare l'insieme delle esplicative tra un partito e l'altro. Gli $R^2$ sono piuttosto
piccoli, in quanto le tre variabili considerate, per quanto significative, spiegano da sole molto poco. È evidente, infatti,
che i risultati di un partito in un comune dipendano da molti fattori qui non misurati, come posizione geografica,
risultati delle scorse elezioni, distribuzione delle età, eccetera. Inoltre la variabilità non spiegabile è presumibilmente 
piuttosto elevata: anche due comuni identici per qualsiasi varaibile rilevabile potrebbero avere risultati ben diversi.
In ogni caso, avendo a disposizione ulteriori dati su cui lavorare, l'ampiamento di questo modello risulterebbe agevole.

### Il comune medio (anzi, mediano)

Come voterebbe, mediamente, un comune di una certa regione, fissando numero di elettori, percentuale di
elettori maschi e affluenza? Modificando i valori a piacere, si può vedere come cambia la ripartizione dei voti.
Da un'idea del [NYTimes](https://www.nytimes.com/interactive/2019/08/08/opinion/sunday/party-polarization-quiz.html),
rielaborata secondo i (pochi) dati a disposizione.

"""
# input dell'utente
regione = st.selectbox("Regione", ["ITALIA"] + regioni, key="mod_elettori")
elettori = st.number_input("Numero di elettori del comune", min_value=200, max_value=2000000, value=100000, key="mod_reg")
m_perc = st.number_input("Percentuale di elettori maschi nel comune", min_value=0, max_value=100, value=50, key="mod_m")
affluenza = st.number_input("Affluenza registrata nel comune", min_value=0, max_value=100, value=50, key="mod_affl")
# creazione e visualizzazione della pie chart
st.altair_chart(mod.prediction(regione, elettori, m_perc, affluenza), use_container_width=True)
"""
__Nota metodologica:__ L'idea di base sarebbe stata quella di modellare l'elettore medio in base alle sue caratteristiche.
Tale analisi sarebbe possibile avendo a disposizione i valori di un campione di elettori.
Tuttavia, per i dati a disposizione, in cui l'unità statistica è il singolo comune, questo non è realizzabile se non
facendo assunzioni piuttosto irrealistiche. 

Ricorrendo al metodo di stima [_Quantile regression_](https://en.wikipedia.org/wiki/Quantile_regression), 
le assunzioni fatte dal modello sono piuttosto deboli.
In pratica, questo metodo permette di assumere solamente linearità nella relazione tra le esplicative e la risposta,
con una buona robustezza agli outliers, dovuta al fatto che stiamo stimando la mediana e non la media.
Il modello non ammette interazione tra le variabili esplicative, dunque l'effetto, ad esempio, dell'aumento di un punto 
dell'affluenza è considerato costante qualsiasi sia il valore assunto dalle altre esplicative.
"""

"""
## Alcune ulteriori analisi, aiutati da R

Di seguito riportiamo delle ulteriori analisi, basate su alcuni concetti del corso di _Analisi dei Dati 
Multidimensionali_, con uno sguardo più approfondito a livello statistico e meno adatto ad un pubblico generalista.
Per uniformità, consideriamo solo i partiti che hanno superato il 3% dei consensi nazionali e che erano candidati in 
tutte le circoscrizioni.

### Analisi delle correlazioni

Per prima cosa, vediamo quanto può dirci l'andamento di un partito sui risultati degli altri. Il seguente grafico è 
eccessivamente complesso da ricreare in Python e richiede una ventina di secondi per l'elaborazione, dunque
lo prendiamo in prestito da R.
```{r}
europee <- read.csv("VotiPerc_R.csv", header=TRUE)
X <- europee[,7:14]
names(X) <- c("FdI","PD","M5S", "FI", "Lega", "AVS", "SUE", "Azione")
library(GGally)
library(ggplot2)
ggpairs(X, 
        lower = list(continuous = "points"),   # Scatterplots
        upper = list(continuous = "cor"),     # Correlazioni
        diag = list(continuous = "density"))  # Densità
```
"""
st.image("corr.png")
"""
Vediamo come quasi tutte le correlazioni siano significative. Vista la grande dimensione e l'eterogeneità delle unità 
statistiche, anche correlazioni intorno allo 0.2 risultano interessanti. Notiamo, ad esempio, che un risultato migliore 
per Fratelli d'Italia porta a percentuali minori per tutti gli altri partiti tranne la Lega.
A questo proposito, si può osservare che, mentre Fratelli d'Italia e Lega sono positivamente correlati, la correlazione 
Forza Italia gli altri due partiti di centrodestra è negativa. Il diverso trend di Forza Italia è consistente con quanto
visto in precedenza. Inolte, il Partito Democratico risulta positivamente correlato con il Movimento 5 Stelle e debolmente
anche con Alleanza Verdi e Sinistra. Potrebbe risultare sorprendente, infine, la correlazione positiva tra Movimento 5 Stelle e Forza Italia.

### Analisi delle componenti principali

La [_Principal Component Analysis_](https://en.wikipedia.org/wiki/Principal_component_analysis) (PCA) è un metodo di 
riduzione della dimensionalità con cui cerchiamo di spiegare la variabilità dei dati tramite un minor numero di variabili
 dette, appunto, componenti principali.

Utilizzando i dati così come sono otteniamo, aiutandoci con R
```{r}
pc_original <- prcomp(X, scale=F, center=F)
summary(pc_original)
```
```
## Importance of components:
##                            PC1      PC2     PC3     PC4     PC5     PC6     PC7     PC8
## Standard deviation     42.5896 10.51303 8.93115 6.69422 5.35687 3.76738 3.46642 2.95531
## Proportion of Variance  0.8586  0.05232 0.03776 0.02121 0.01358 0.00672 0.00569 0.00413
## Cumulative Proportion   0.8586  0.91091 0.94866 0.96988 0.98346 0.99018 0.99587 1.00000
```

Utilizzando i dati centrati ma non riscalati, come il default della funzione _PCA()_ 
della libreria _scikit-learn_ in Python, otteniamo
"""

votiPCA = vt.votiPerc.select(vt.partitiPlot)

# data una PCA (sklearn) restituisce un dataframe conentente varianza spiegata (assoluta, in proporzione e cumulativa)
# da ognuna delle componenti principali
def pca_expl_var(princomp):
    expl_var = (
        pl.DataFrame(
            [
                princomp.explained_variance_.tolist(),
                princomp.explained_variance_ratio_.tolist(),
                np.cumsum(princomp.explained_variance_ratio_).tolist()
            ],
            orient="row",
            schema=["1", "2", "3", "4", "5", "6", "7", "8"]
        )
        .with_columns(
                pl.Series("DESCR", ["VAR SPIEGATA", "PROP VAR SP", "CUM PROP VAR SP"])
        )
        .select(
            ["DESCR", "1", "2", "3", "4", "5", "6", "7", "8"]
        )
    )
    return expl_var

# PCA e visualizzazione delle varianze spiegate da ogni PC
pca = PCA()
pca_result = pca.fit_transform(votiPCA)
st.dataframe(pca_expl_var(pca),use_container_width=True)

"""
Utilizzando, invece, i dati standardizzati facciamo emergere la relazione tra i partiti al netto delle loro percentuali medie
e delle loro varianze. In pratica, diamo lo stesso peso ad ogni partito. Si ottiene
"""
# con i dati standardizzati
pca_std = PCA()
scaler = StandardScaler()
scaled = scaler.fit_transform(votiPCA)
pca_std_res = pca_std.fit_transform(scaled)

eigen_expl = pca_expl_var(pca_std)
st.dataframe(eigen_expl,use_container_width=True)

eigen_expl = (
    eigen_expl
    .unpivot(
        index="DESCR",
        variable_name="component"
    )
    .filter(
        pl.col("DESCR") == "VAR SPIEGATA"
    )
)

# screeplot
screeplot = (
    alt.Chart(eigen_expl)
    .mark_line()
    .encode(
        alt.X("component", axis=alt.Axis(labelAngle=0), title="Componente principale"),
        alt.Y("value", title="Varianza spiegata")
    )
)

points = (
    screeplot
    .mark_point(size=60)
    .encode(
        alt.X("component", axis=alt.Axis(labelAngle=0), title="Componente principale"),
        alt.Y("value", title="Varianza spiegata")
    )
)

st.altair_chart(screeplot+points,use_container_width=True)

"""
In queste condizioni, vediamo che tre componenti principali da sole spiegano circa il 58% della varianza totale. 
Per i dati grezzi, invece, due componenti spiegano già il 91%. Ciò è dovuto al fatto che i partiti più piccoli hanno 
molta meno varianza nei risultati, in termini assoluti, rispetto ai partiti maggiori.

#### Biplot
"""
PC12 = pl.DataFrame(pca_std_res).select("column_0","column_1")

# visualizzazione dei punti (ognuno è un comune)
biplot = (
    alt.Chart(PC12)
    .mark_circle()
    .encode(
        alt.X("column_0", axis=alt.Axis(labelAngle=0), scale=alt.Scale(domain=[-12, 12]), title="PC1"),
        alt.Y("column_1", scale=alt.Scale(domain=[-12, 12]), title="PC2")
        # mettere tooltip
    )
    .properties(
        width=600,
        height=600
    )
)

# definizione e visualizzazione delle frecce (ognuna è un partito)
arrow_data = pl.DataFrame({
    "x": [0] * 8,
    "y": [0] * 8,
    "x2": pca_std.components_[0, :]*15,
    "y2": pca_std.components_[1, :]*15,
    "x_txt":pca_std.components_[0, :]*16.5,
    "y_txt":pca_std.components_[1, :]*16.5,
    "part": ["FdI", "PD", "M5S", "FI", "Lega", "AVS", "SUE", "Azione"]
})

arrows = (
    alt.Chart(arrow_data)
    .mark_rule(
        color="red",
        strokeWidth=3
    )
    .encode(
        x = "x",
        y = "y",
        x2 = "x2",
        y2 = "y2"
    )
)

text_biplot = (
    alt.Chart(arrow_data)
    .mark_text(
    color="red",
    fontSize=15,
    fontWeight="bold"
    )
    .encode(
        x = "x_txt",
        y = "y_txt",
        text="part"
    )
)

st.altair_chart(biplot+arrows+text_biplot, use_container_width=True)
"""
I partiti le cui frecce indicano direzioni simili sono positivamente correlati, quelli a 90° sono incorrelati, 
mentre quelli che indicano direzioni opposte sono correlati negativamente. Il risultato è tuttavia un'approssimazione 
basata sulle prime due componenti principali, ovvero spiega solo il 43.5% della varianza totale.
Le conclusioni che si traggono da questo biplot sono simili ma non del tutto analoghe a quelle che si traggono dall'analisi
della matrice di correlazione. In questo senso, il biplot è un utile strumento per farsi un'idea grafica delle relazioni
tra le variabili, ma, essendo una riduzione di dimensionalità, comporta una perdita di informazione.


### Analisi fattoriale

La [_Factor Analysis_](https://en.wikipedia.org/wiki/Factor_analysis) (FA) è una tecnica di riduzione della dimensionalità
 simile alla PCA. Tuttavia, si differenza nel fatto che interpreta le p (nel nostro caso 8) variabili osservate come 
 risultato della realizzazione di m<<p varaibili non osservabili (dette, appunto, fattori).

```{r}
factanal(X, 4)
```
```
## 
## Call:
## factanal(x = X, factors = 4)
## 
## Uniquenesses:
##    FdI     PD    M5S     FI   Lega    AVS    SUE Azione 
##  0.419  0.005  0.688  0.005  0.678  0.005  0.788  0.898 
## 
## Loadings:
##        Factor1 Factor2 Factor3 Factor4
## FdI    -0.285  -0.345  -0.298  -0.540 
## PD      0.979  -0.186                 
## M5S     0.165   0.127           0.517 
## FI              0.986  -0.110         
## Lega   -0.419  -0.194  -0.237  -0.229 
## AVS            -0.124   0.988         
## SUE                             0.456 
## Azione -0.109  -0.147           0.256 
## 
##                Factor1 Factor2 Factor3 Factor4
## SS loadings      1.268   1.217   1.143   0.885
## Proportion Var   0.158   0.152   0.143   0.111
## Cumulative Var   0.158   0.311   0.454   0.564
## 
## Test of the hypothesis that 4 factors are sufficient.
## The chi square statistic is 2822.55 on 2 degrees of freedom.
## The p-value is 0
```
Ci si potrebbe perdere nell'interpretazione dei fattori, ma il test sulla bontà di questa riduzione di dimensionalità 
ha _p-value_ indistinguibile da 0. Pertanto, l'analisi dei fattori non si presta bene a questo dataset.
"""

"""
## Mappe dei risultati
### Una prima mappa con Streamlit
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

### Risultati per partito, per regione o provincia
Selezionando un livello si può modificare la visualizzazione tra regione o provincia.
La scala dei colori visualizzata è relativa al massimo di ogni partito.
Quando alcune aree geografiche non vengono visualizzate, ciò significa che il partito selezionato non vi era candidato.
"""

chLiv = st.selectbox("Livello", ["REGIONE", "PROVINCIA"], key="chLivello")
# il livello comune è tralasciato sia perché supera i 5000 elementi di limite di default di Altair, sia perché il
# mismatch dei nomi tra i due dataframe renderebbe molti comuni non visualizzati
chPart = st.selectbox("Partito", vt.partiti, key="chPartito").replace("'", "\\'")

# raggruppiamo al livello richiesto
votiPercPlot = (
    vt.voti_grouped_by(chLiv)
    .with_columns(
        pl.col(chLiv).str.to_titlecase()
    )
)

# alcune provincie hanno nomi non coincidenti nei due dataframe, modifichiamo per semplicità quelli in votiPercPlot
votiPercPlot = mappe.reg_prov_fix(votiPercPlot)

geoIT, labelLiv = mappe.get_topo_data(chLiv)

choropleth = (
    alt.Chart(geoIT)
    .mark_geoshape()
    .transform_lookup(
        lookup=labelLiv,
        from_=alt.LookupData(data=votiPercPlot, key=chLiv, fields=[chPart])
    )
    .encode(
        alt.Color(f"{chPart}:Q", sort="descending").scale(scheme="viridis"),
        tooltip=[
            alt.Tooltip(f"{labelLiv}:N", title=chLiv),
            alt.Tooltip(f"{chPart}:Q", title=f"% {chPart}", format=".2f")
        ],
    )
)
st.altair_chart(choropleth, use_container_width=True)

"""
## Conclusioni e commenti
Il progetto si pone l'obiettivo di esplorare e visualizzare le relazioni che emorgono dai dati a disposizione.
Come si può vedere, sono emerse correlazioni interessanti sia tra i vari partiti, sia tra i partiti e le tre variabili
che descrivono il comune. Un proseguimento ovvio di questa analisi potrebbe essere l'aggiunta di ulteriori variabili
di descrizione del comune. Questo, però, è reso particolarmente complesso dal fatto che i dati non contengono i codici
ISTAT dei comuni. Ricavarli dal nome del comune è certamente possibile, ma è un processo estremamente lungo che esula 
dagli scopi di questo progetto e di questo corso.

Tra le relazioni più interessanti emerse, trovo particolamente interessanti quelle del modello. In particolare, che il 
centrodestra ottiene risultati migliori in comuni meno popolosi, con più maschi e affluenza maggiore, mentre per 
il centrosinistra vale l'opposto. Inoltre, un fatto evidente in più punti è la forte differenza che intercorre tra Fratelli
d'Italia e Lega, che mostrano sempre comportamenti simili, e Forza Italia, che spesso mostra andamenti non allineati.
Inoltre, dalle correlazioni si evidenziano valori positivi tra Partito Democratico, Movimento 5 Stelle e Alleanza
Verdi Sinistra, mentre non sono così chiari i rapporti di Stati Uniti d'Europa e Azione con gli altri partiti.

Per quanto riguarda il progetto in sé, l'ho trovato una grande opportunità per imparare a usare Python in maniera più
organizzata e per esplorare diversi modi per affrontare i problemi emersi, oltre ad alcune librerie.
Mi ha fatto realizzare quanto ci sia un grande livello di complessità nascosta dietro a tutto quello che usiamo e diamo 
per scontato, dalla singola libreria alle funzioni di R. Molte cose facilmente realizzabili in R hanno richiesto 
un bel po' di tempo per essere implementate in Python, pur affidando la parte più pesante del lavoro
a delle librerie apposite. L'esplorazione di questo dataset inoltre mi ha dato molti spunti su cui riflettere in vista
della tesi che intendo sviluppare su argomenti sempre legati ai dati elettorali.
"""
