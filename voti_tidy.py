import polars as pl
import streamlit as st
from statsmodels.tsa.statespace.tools import prepare_trend_data


def get_raw_data():
    file = "Europee2024.txt"
    voti = pl.read_csv(file, separator=";")

    # togliamo una colonna inutile e rinominiamo per semplificarci la vita
    # questo sarà il dataframe che rappresenta l'linformazione iniziale "raw"
    # indico il tipo atteso altrimenti pycharm si confonde
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
            [(abs[partito] / abs["VOTI_VALIDI"] * 100).round(2).alias(partito)]  # da risolvere la questione round()
        )  # da rivedere rounding
    perc = perc.with_columns(
        CENTRODESTRA=pl.col("FRATELLI D'ITALIA") + pl.col("LEGA SALVINI PREMIER") + pl.col("FORZA ITALIA - NOI MODERATI - PPE"),
        CENTROSINISTRA=pl.col("PARTITO DEMOCRATICO") + pl.col("MOVIMENTO 5 STELLE") + pl.col("ALLEANZA VERDI E SINISTRA"),
        AFFLUENZA=pl.col("VOTANTI") / pl.col("ELETTORI") * 100
    )
    return abs, perc


def voti_grouped_by(livello, cond=None):
    if livello == "ITALIA":
        votiAbsGrouped = (
            votiAbs
            .sum()
        )
    else:
        votiAbsGrouped = (
            votiAbs
            .filter(pl.col(livello) == cond)
            .group_by(livello)
            .sum()
        )

    df = votiAbsGrouped.select(["CIRCOSCRIZIONE", "REGIONE", "PROVINCIA", "COMUNE"])
    for partito in partiti:
        df = df.with_columns(
            [(votiAbsGrouped.get_column(partito) / votiAbsGrouped.get_column("VOTI_VALIDI") * 100).round(2).alias(partito)]  # da risolvere la questione round()
        )
    return df

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
colors = ["blue","red","yellow","lightblue","darkgreen","lightgreen","purple","darkblue"]
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
    print(votiAbs.select(["ELETTORI", "ELETTORI_M"]).mean())
