import os
from dotenv import load_dotenv

# Carica le variabili dal file .env
load_dotenv()

# Legge il token
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Se non lo trova, ferma tutto e ti avvisa
if not TOKEN:
    raise ValueError("ERRORE: Nessun Token trovato! Controlla il file .env")