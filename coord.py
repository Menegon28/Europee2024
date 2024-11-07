import polars as pl
from voti_tidy import votiPerc

cities = pl.read_csv("cities_coord2.csv")

coord = (cities.select(["name","location"])
         .with_columns(
    pl.col("location").str.json_decode(),
    pl.col("name").str.to_uppercase()
    ).unnest("location")
    .drop("__type").sort("name"))

votiCoord = votiPerc.join(coord, left_on="COMUNE", right_on="name")
votiCoord.glimpse()

partitiPerc = [
    "FRATELLI D'ITALIA (%)",
    "PARTITO DEMOCRATICO (%)",
    "MOVIMENTO 5 STELLE (%)",
    "FORZA ITALIA - NOI MODERATI - PPE (%)",
    "LEGA SALVINI PREMIER (%)",
    "ALLEANZA VERDI E SINISTRA (%)",
    "STATI UNITI D'EUROPA (%)",
    "AZIONE - SIAMO EUROPEI (%)",
    "PACE TERRA DIGNITA' (%)",
    "LIBERTA' (%)",
    "SÜDTIROLER VOLKSPARTEI (SVP) (%)",
    "ALTERNATIVA POPOLARE (%)",
    "DEMOCRAZIA SOVRANA POPOLARE (%)",
    "PARTITO ANIMALISTA - ITALEXIT PER L'ITALIA (%)",
    "RASSEMBLEMENT VALDÔTAIN (%)"
]

if __name__ == "__main__":
    cities.glimpse()
    print(cities)
    print(coord)
    print(votiCoord)
    votiCoord.glimpse()
    with pl.Config(tbl_rows=30):
        print(votiPerc.join(coord, left_on="COMUNE", right_on="name", how="anti").sort("ELETTORI", descending=True))