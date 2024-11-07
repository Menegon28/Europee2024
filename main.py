import streamlit as st
import polars as pl
import voti_tidy as vt
import coord

st.write("### Mappe dei risultati")
st.write("Dall'interfaccia, selezionare un __partito__ e un __intervallo della percentuale di voti__. "
         "Si ottiene così una mappa che indica tutti i comuni in cui il paritito selezionato ha ottenuto una percentuale "
         "di voti compatibile con l'intervallo selezionato. È anche possibile visualizzare l'elenco di questi comuni in calce.")

partitoMappa = st.selectbox("Partito", vt.partiti)
# minPerc = st.slider("Seleziona la percentuale minima", 0, 100)
(minPerc, maxPerc) = st.slider("Seleziona l'intevallo percentuale", 0, 100, value=(0,100))


votiCoordFilter = (coord.votiCoord
                   .drop("CIRCOSCRIZIONE")
                   .filter(pl.col(partitoMappa) > minPerc)
                   .filter(pl.col(partitoMappa) <= maxPerc)
                   .sort(["REGIONE", "PROVINCIA", "COMUNE"]))
if votiCoordFilter.is_empty():
    st.write("Nessun comune corrispondente alla descrizione")
else:
    st.map(votiCoordFilter,
           latitude="latitude",
           longitude="longitude")
    st.write("Elenco dei comuni corrispondenti e percentuale dei voti di ogni partito")
    st.write(votiCoordFilter.drop(["latitude", "longitude"]))

st.write("__Nota metodologica__: Questa mappa è stata realizzata tramite un _inner join_ tra i dati dei risultati elettorali e "
         "di un database contenente i valori di latitudine e longitudine di (quasi) tutti i comuni italiani. "
         "Come è naturale, questo ha comportato una perdita di informazioni dovuta a qualche differenza nei nomi "
         "come indicati nelle due tabelle. Si sono apportate alcune correzioni di base (e.g. accenti) "
         "e si è proceduto manualmente per i comuni più grandi. Al momento, circa 600 comuni non sono riportati, "
         "tutti al di sotto dei 20 mila elettori totali.")
