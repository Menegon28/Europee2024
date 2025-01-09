import polars as pl
import streamlit as st
from statsmodels.tsa.statespace.tools import prepare_trend_data

# legge, modifica i nomi di colonna e restituisce i dati nello stesso formato in cui sono contenuti nel file
def get_raw_data():
    file = "Europee2024.txt"
    voti = pl.read_csv(file, separator=";")

    # togliamo una colonna inutile e rinominiamo per semplificarci la vita
    # questo sarà il dataframe che rappresenta l'linformazione iniziale "raw"
    voti: pl.dataframe = (
        voti
        .drop("DATA_ELEZIONE")
        .rename({
            "DESCCIRCEUROPEA": "CIRCOSCRIZIONE",
            "DESCREGIONE": "REGIONE",
            "DESCPROVINCIA": "PROVINCIA",
            "DESCCOMUNE": "COMUNE",
            "DESCLISTA": "LISTA"
        }
        )
    )
    return voti


# effettua il preprocessing, creando un dataset per i voti in valore assoluto e uno per i voti espressi sulla percentuale
# dei voti validi, dove ogni comune è una unità statistica e i risultati di ogni lista una variabile
@st.cache_data
def data_preprocessing():
    voti = get_raw_data()

    # effettuamo un pivot per rendere il singolo comune l'unità statistica e il numero di voti di ogni lista una variabile
    abs: pl.DataFrame = (
        voti
        .pivot(on="LISTA", values="NUMVOTI")
        .with_columns(
            VOTI_VALIDI=pl.sum_horizontal(partiti)
        )
    )

    # inizializza il dataframe per le percentuali di voto per partito
    perc: pl.DataFrame = abs.select(
        ["CIRCOSCRIZIONE", "REGIONE", "PROVINCIA", "COMUNE", "ELETTORI", "ELETTORI_M", "VOTANTI"]
    )
    # crea il dataframe votiPerc aggiungendo alle colonne delle caratteristiche dei comuni le percentuali di ogni partito
    for partito in partiti:
        perc = perc.with_columns(
            # per una questione di visualizzazione in Streamlit, arrotondiamo tutto alla seconda cifra decimale
            (abs.get_column(partito) / abs.get_column("VOTI_VALIDI") * 100).round(2).alias(partito)
        )
    perc = perc.with_columns(
        CENTRODESTRA=pl.col("FRATELLI D'ITALIA") + pl.col("LEGA SALVINI PREMIER") + pl.col("FORZA ITALIA - NOI MODERATI - PPE"),
        CENTROSINISTRA=pl.col("PARTITO DEMOCRATICO") + pl.col("MOVIMENTO 5 STELLE") + pl.col("ALLEANZA VERDI E SINISTRA"),
        AFFLUENZA=pl.col("VOTANTI") / pl.col("ELETTORI") * 100
    )
    return abs, perc

# restituisce un dataframe polars contenente le percentuali di voto di tutti i partiti per un certo livello geografico
# (italia, circorscizione, regione, provincia o comune)
# se specificata la condizione cond, restituisce solo quel circ/reg/prov/comune
def voti_grouped_by(livello, cond=None):
    if livello == "ITALIA":
        abs_gr = votiAbs.sum()
        # return votiAbs.sum()
    else:
        abs_gr = (
            get_raw_data()
            .select(
                ["CIRCOSCRIZIONE", "REGIONE", "PROVINCIA", "COMUNE", "LISTA", "NUMVOTI"]
            )
            .group_by([livello, "LISTA"])
            .sum()
            .pivot(
                on="LISTA",
                values="NUMVOTI"
            )
            .with_columns(
                VOTI_VALIDI=pl.sum_horizontal(partiti)
            )
        )

    perc_gr = abs_gr.select(["CIRCOSCRIZIONE", "REGIONE", "PROVINCIA", "COMUNE"])
    for partito in partiti:
        perc_gr = perc_gr.with_columns(
            (abs_gr.get_column(partito) / abs_gr.get_column("VOTI_VALIDI") * 100).round(2).alias(partito)
        )

    if livello == "ITALIA" or cond is None:
        return perc_gr
    else:
        return perc_gr.filter(pl.col(livello) == cond)


# scriviamo a mano per tenere questo preciso ordine
partiti = [
    "FRATELLI D'ITALIA",
    "PARTITO DEMOCRATICO",
    "MOVIMENTO 5 STELLE",
    "FORZA ITALIA - NOI MODERATI - PPE",
    "LEGA SALVINI PREMIER",
    "ALLEANZA VERDI E SINISTRA",
    "STATI UNITI D'EUROPA",
    "AZIONE - SIAMO EUROPEI",
    "PACE TERRA DIGNITA'",
    "LIBERTA'",
    "SÜDTIROLER VOLKSPARTEI (SVP)",
    "ALTERNATIVA POPOLARE",
    "DEMOCRAZIA SOVRANA POPOLARE",
    "PARTITO ANIMALISTA - ITALEXIT PER L'ITALIA",
    "RASSEMBLEMENT VALDÔTAIN"
]

partiti_ext = partiti + ["CENTRODESTRA", "CENTROSINISTRA"]

# partiti oltre il 3%
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

# colors = ["blue","red","yellow","lightblue","darkgreen","lightgreen","purple","darkblue"]
colors = ["#1f77b4","#d62728","#e7ba52","#aec7e8","#2ca02c","#98df8a","#9467bd","#393b79"]
# dati iniziali già preprocessati
votiAbs, votiPerc = data_preprocessing()


if __name__ == "__main__":
    pl.Config.set_tbl_width_chars(200)
    pl.Config(tbl_cols=30)
    print("VOTI:")
    print(get_raw_data())
    print(votiPerc)
    print(votiPerc["PARTITO DEMOCRATICO"])
    get_raw_data().glimpse()
    print(votiAbs.select(partiti+["VOTI_VALIDI"]).sum())
