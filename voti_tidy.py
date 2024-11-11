import polars as pl
from fontTools.misc.psOperators import ps_array

file = "Europee2024.txt"
voti = pl.read_csv(file, separator=";")

# togliamo una colonna inutile e rinominiamo per semplificarci la vita
voti: pl.DataFrame = (voti
                      .drop("DATA_ELEZIONE")
                      .rename({
    "DESCCIRCEUROPEA"   : "CIRCOSCRIZIONE",
    "DESCREGIONE"       : "REGIONE",
    "DESCPROVINCIA"     : "PROVINCIA",
    "DESCCOMUNE"        : "COMUNE"
}))

# vediamo che ci sono 7896 comuni e 15 partiti totali, non tutti presenti in ogni circoscrizione
# notiamo la differenza tra un valone null, che indica che il partito non era candidato in quel comune
# (perché non si è candidato in quella circoscrizione)
# e il valore 0 che indica che il partito non ha raccolto voti nel comune indicato (ma era candidato)

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


# partiti = voti.select("DESCLISTA").unique().to_struct().to_list()
# print("___________")
# print(partiti)
# print(type(partiti))
# votiAbs: pl.DataFrame = (voti.pivot(on="DESCLISTA", values="NUMVOTI"))
# print(votiAbs)
# se voglianmo che ogni comune appaia una sola volta
votiAbs: pl.DataFrame = (voti.pivot(on="DESCLISTA", values="NUMVOTI")
                         .with_columns(
    VOTI_VALIDI=pl.sum_horizontal(partiti)
))

votiPerc: pl.DataFrame = votiAbs.select(["CIRCOSCRIZIONE", "REGIONE", "PROVINCIA", "COMUNE", "ELETTORI", "ELETTORI_M"])

# Add percentage columns for each party by dividing the party votes by VOTI_VALIDI and multiplying by 100
for partito in partiti:
    votiPerc = votiPerc.with_columns([
        (votiAbs[partito] / votiAbs["VOTI_VALIDI"] * 100).round(2).alias(partito)])



if __name__ == "__main__":
    pl.Config.set_tbl_width_chars(200)
    pl.Config(tbl_cols=20)
    print(votiPerc)
    print(votiPerc.filter(pl.col("ALLEANZA VERDI E SINISTRA") == pl.max("ALLEANZA VERDI E SINISTRA")))
    votiPerc.write_csv("VotiPerc_R.csv")
    votiAbs.write_csv("VotiAbs_R.csv")
    voti.glimpse()

