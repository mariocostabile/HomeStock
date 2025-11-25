# HomeStock

HomeStock è un bot Telegram progettato per semplificare la gestione dell'inventario domestico. Permette agli utenti di tracciare gli articoli casalinghi, organizzarli in categorie, impostare soglie di scorta minima e generare automaticamente liste della spesa.

Il progetto è sviluppato in Python utilizzando la libreria `python-telegram-bot`, adottando un'architettura modulare e un database SQLite per la persistenza dei dati.

## Funzionalità

* **Gestione Categorie:** Creazione, rinomina ed eliminazione di categorie (es. Cucina, Bagno, Dispensa).
* **Gestione Prodotti:** Aggiunta di prodotti con nome, quantità attuale e soglia minima di allerta.
* **Lista della Spesa Intelligente:** Generazione automatica di una lista degli articoli la cui quantità è inferiore alla soglia impostata.
* **Visualizzazione Inventario Completo:** Mostra una lista completa di tutti gli articoli posseduti, raggruppati per categoria con indicatori di stato.
* **Pannello di Controllo Interattivo:** Interfaccia inline per modificare rapidamente le scorte (+/-), aggiornare le soglie, spostare articoli tra categorie o eliminarli.
* **Interfaccia Smart Grid:** L'interfaccia adatta automaticamente la disposizione dei pulsanti (lista vs griglia a due colonne) in base al numero di elementi per ottimizzare lo spazio sullo schermo.
* **Sicurezza dei Dati:** L'eliminazione di una categoria non cancella i prodotti contenuti; questi vengono spostati in un'area sicura "Senza Categoria" per essere riassegnati.

## Architettura Tecnica

Il progetto segue una struttura modulare per garantire manutenibilità e scalabilità:

* **Linguaggio:** Python 3.x
* **Framework:** `python-telegram-bot` (Asincrono)
* **Database:** SQLite (Supporto nativo, nessuna configurazione server richiesta)
* **Design Pattern:** Separazione delle responsabilità (Layer Database, Utility UI e Logica degli Handler sono separati).

### Struttura del Progetto

```text
HomeStock/
├── handlers/               # Logica del bot e stati della conversazione
│   ├── __init__.py
│   ├── categories.py       # Logica CRUD Categorie
│   ├── common.py           # Comandi Start e Cancel
│   └── products.py         # Gestione Prodotti e visualizzazioni
├── .env                    # Variabili d'ambiente (Token API)
├── .gitignore              # Regole di esclusione Git
├── config.py               # Caricamento configurazioni
├── constants.py            # Definizioni degli stati per ConversationHandler
├── database.py             # Connessione SQLite e query
├── main.py                 # Entry point e routing
├── utils.py                # Helper UI e funzioni di formattazione
└── requirements.txt        # Dipendenze Python