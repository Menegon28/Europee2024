import polars as pl

file = "Europee2024.txt"
voti = pl.read_csv(file, separator=";")
# vediamo com'è la tabella
pl.Config.set_tbl_width_chars(300)
pl.Config(tbl_cols=30)
# print(voti)

# togliamo una colonna inutile
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
# votiAbs: pl.DataFrame = (voti.pivot(on="DESCLISTA", values="NUMVOTI"))
# print(votiAbs)
# se voglianmo che ogni comune appaia una sola volta
votiAbs: pl.DataFrame = (voti.pivot(on="DESCLISTA", values="NUMVOTI")
                         .with_columns(
    VOTI_VALIDI = pl.sum_horizontal(partiti)
))

votiPerc: pl.DataFrame = votiAbs.select(["CIRCOSCRIZIONE", "REGIONE", "PROVINCIA", "COMUNE"])

# Add percentage columns for each party by dividing the party votes by VOTI_VALIDI and multiplying by 100
for partito in partiti:
    votiPerc = votiPerc.with_columns([
        (votiAbs[partito] / votiAbs["VOTI_VALIDI"] * 100).round(2).alias(partito)])



if __name__ == "__main__":
    print(votiAbs)

    votiAbs.glimpse()
    print(votiAbs)
    print(votiAbs.null_count())
    # non sono candidati ovunque: RV, SVP, DemSovrPop, Animalisti/Italexit

    # totali per colonna
    print(votiAbs.sum())
    votiPerc.glimpse()
    print(votiPerc)
