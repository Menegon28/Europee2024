import polars as pl

file = "Anagrafica_provincia.csv"

ages = pl.read_csv(file).drop("ITTER107","TIPO_DATO15","Tipo di indicatore demografico","SEXISTAT1",
                              "ETA1","STATCIV2","Stato civile","TIME","Seleziona periodo","Flag Codes","Flags")
ages.glimpse()
print(ages)
ages = ((((((((ages.pivot(on="Sesso",
                 index=["Territorio","Età"],
                 values="Value",
                 aggregate_function="min")
        .with_columns(pl.col("Età").str.strip_suffix(" anni").alias("Età strip")))
        .filter(pl.col("Età") != "100 anni e più"))  # ignoriamo per semplicità
        .filter(pl.col("Età") != "total"))
        .filter(pl.col("Età") != "totale"))
        .with_columns(pl.col("Età strip").cast(pl.Int64).alias("Età int")))
        .drop("Età", "Età strip"))
        .select(["Territorio", "Età int", "maschi", "femmine", "totale"])))
print(ages)
bins = [17, 29, 49, 64]
labels = ["0-17", "18-29", "30-49", "50-64", "65+"]
print(ages.with_columns(
   pl.col("Età int").cut(bins, labels=labels).alias("age_group"))
    .group_by(["Territorio", "age_group"])
      .agg([
              pl.col("maschi").sum(),
              pl.col("femmine").sum(),
              pl.col("totale").sum()
          ])
    .sort(["Territorio", "age_group"])
)







