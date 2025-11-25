# --- STATI CATEGORIE ---
# Prima avevi solo range(2), ora dobbiamo gestire anche la modifica, le azioni e la rinomina
INSERIMENTO_NOME_CATEGORIA, SCELTA_DOPO_CATEGORIA, MODIFICA_CATEGORIA, AZIONI_CATEGORIA, RINOMINA_CATEGORIA = range(5)

# --- STATI PRODOTTI ---
# Partiamo da 10 per non accavallarci con le categorie
SCELTA_CATEGORIA_PRODOTTO, NOME_PRODOTTO, QUANTITA_PRODOTTO, SOGLIA_PRODOTTO, FINE_PRODOTTO, MODIFICA_PRODOTTO = range(10, 16)