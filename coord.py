import polars as pl
from voti_tidy import votiPerc
import streamlit as st


@st.cache_data
def get_coord():
    cities = pl.read_csv("cities_coord.csv")

    coord = (cities.select(["name", "location"])
             .with_columns(
        pl.col("location").str.json_decode(),
        pl.col("name").str.to_uppercase()
        ).unnest("location")
        .drop("__type")
        .unique(subset="name", keep="none")
        .sort("name"))
    return votiPerc.join(coord, left_on="COMUNE", right_on="name")


votiCoord = get_coord


if __name__ == "__main__":
    votiCoord.glimpse()
    print(votiCoord)
