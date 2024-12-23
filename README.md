# ProgettoSdE2
### Analisi dei dati elettorali delle Europee 2024 in Italia, per il corso di Sistemi di Elaborazione 2

Il progetto intende esplorare il dataset delle elezioni Europee del 2024 in Italia. I dati sono pubblicamente disponibili sul sito [Eligendo](https://elezionistorico.interno.gov.it/eligendo/opendata.php), gestito dal Ministero dell'Interno. Per evitare modifiche ai dati, viene utilizzato direttamente il file `Europee2024.txt`.
Questo dataset contiene i risultati registrati comune per comune, lista per lista, espressi in numeri assoluti. Inoltre, include alcune informazioni di base sul comune, come regione e provincia di appartenenza e numero di elettori e votanti, divisi per sesso. 
Il progetto mira a visualizzare in maniera intuitiva i riusltati, che sono anche navigabili precisamente dal tool "_Esplorare il dataset_". Inoltre, mira a rilevare relazioni di similarità e differenze tra i partiti e tra i partiti e alcune variabili, tramite un modello statistico. Infine, una parte del progetto è dedicata ad analisi più approfondite svolte coi metodi visti nel corso di _Analisi dei Dati Multidimensionali_. 
Il progetto è strutturato come applicazione web gestita tramite [Streamlit](https://streamlit.io/). La gestione delle dipendenze è implementata tramite [UV](https://docs.astral.sh/uv/).
Per eseguire il codice, posizionandosi sulla cartella da terminale, basta eseguire `uv run streamlit run app.py` per avviare l'interfaccia web.
Le librerie necessarie per il corretto funzionamento sono riportate nel file `pyproject.TOML`, e sono le seguenti:
```
requires-python = ">=3.12"
dependencies = [
    "altair==5.3.0",
    "polars>=1.14.0",
    "scikit-learn>=1.6.0",
    "statsmodels>=0.14.4",
    "streamlit>=1.40.1",
]
```
Il requisito di sulla versione di Python è probabilmente più stringente del necessario, ma viene mantenuto per evitare problemi con Vega-Altair.
Il file principale dell'applicazione è `app.py`. Questo contiene tutto il testo visualizzato, parte del codice e si basa sugli altri file _Python_ per eseguire le rimanenti parti di codice, in modo da poter tenere il codice più ordinato.
