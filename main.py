import sys
import os  # <--- FONDAMENTALE per il riavvio forzato
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)
from telegram.error import TimedOut, NetworkError
from telegram.request import HTTPXRequest

import config
import database
import constants
from handlers import common, categories, products

# 1. Configurazione Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Zittiamo le librerie che "parlano" troppo
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# --- FUNZIONE KILLER PER ERRORI DI RETE (CRUCIALE PER START.SH) ---
async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Questa funzione intercetta gli errori mentra il bot è attivo.
    Se è un errore di rete, uccide il processo per far scattare start.sh.
    """
    try:
        logger.error(f"⚠️ Eccezione rilevata: {context.error}")

        # Se l'errore riguarda la connessione (Timeout, NetworkError, OSError)
        if isinstance(context.error, (TimedOut, NetworkError, OSError)):
            logger.error("🛑 CRASH DI RETE RILEVATO! Chiudo il processo forzatamente...")
            # os._exit(1) è brutale: chiude tutto all'istante senza aspettare.
            os._exit(1)
    except:
        # Se fallisce anche l'handler, chiudiamo comunque
        os._exit(1)


if __name__ == '__main__':
    # Init Database
    database.init_db()

    # --- CONFIGURAZIONE RETE ---
    # Impostiamo i timeout per rendere il bot più tollerante alle reti mobili
    trequest = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
        http_version='1.1'
    )

    # 2. Costruzione App
    app = (
        ApplicationBuilder()
        # NOTA: Assicurati che nel tuo config.py la variabile si chiami TOKEN o TELEGRAM_TOKEN
        .token(config.TELEGRAM_TOKEN if hasattr(config, 'TELEGRAM_TOKEN') else config.TOKEN)
        .request(trequest)
        .build()
    )

    # --- REGISTRAZIONE DEL KILLER (Error Handler) ---
    app.add_error_handler(global_error_handler)

    # --- CONVERSATION CATEGORIE ---
    conv_cat = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(categories.ask_category_name, pattern='^add_cat$'),
            CallbackQueryHandler(categories.list_categories_for_edit, pattern='^edit_cat_list$')
        ],
        states={
            constants.INSERIMENTO_NOME_CATEGORIA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, categories.save_category),
                CallbackQueryHandler(categories.menu_categorie, pattern='^back_to_cat_menu$')
            ],
            constants.SCELTA_DOPO_CATEGORIA: [
                CallbackQueryHandler(categories.ask_category_name, pattern='^add_cat$'),
                CallbackQueryHandler(categories.menu_categorie, pattern='^back_to_cat_menu$')
            ],
            constants.MODIFICA_CATEGORIA: [
                CallbackQueryHandler(categories.show_category_panel, pattern='^sel_edit_cat_'),
                CallbackQueryHandler(categories.menu_categorie, pattern='^back_to_cat_menu$'),
                CallbackQueryHandler(categories.list_categories_for_edit, pattern='^edit_cat_list$')
            ],
            constants.AZIONI_CATEGORIA: [
                CallbackQueryHandler(categories.handle_category_actions, pattern='^(act_cat_|edit_cat_list)')
            ],
            constants.RINOMINA_CATEGORIA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, categories.save_renamed_category),
                CallbackQueryHandler(categories.handle_category_actions, pattern='^back_to_cat_panel$')
            ]
        },
        fallbacks=[CommandHandler('cancel', common.cancel)],
        per_message=False
    )

    # --- CONVERSATION PRODOTTI ---
    conv_prod = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(products.step_1_ask_category, pattern='^add_prod_start$'),
            CallbackQueryHandler(products.start_modify_flow, pattern='^mod_start$')
        ],
        states={
            constants.SCELTA_CATEGORIA_PRODOTTO: [
                CallbackQueryHandler(products.step_2_ask_name, pattern='^sel_cat_'),
                CallbackQueryHandler(products.menu_prodotti, pattern='^menu_prodotti$')
            ],
            constants.NOME_PRODOTTO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, products.step_3_ask_qty),
                CallbackQueryHandler(products.step_1_ask_category, pattern='^back_to_step_1$')
            ],
            constants.QUANTITA_PRODOTTO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, products.step_4_ask_threshold),
                CallbackQueryHandler(products.step_2_ask_name, pattern='^back_to_step_2$')
            ],
            constants.SOGLIA_PRODOTTO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, products.step_5_save_final),
                CallbackQueryHandler(products.step_3_ask_qty, pattern='^back_to_step_3$')
            ],
            constants.FINE_PRODOTTO: [
                CallbackQueryHandler(products.step_1_ask_category, pattern='^add_prod_start$'),
                CallbackQueryHandler(common.start, pattern='^main_menu$')
            ],
            constants.MODIFICA_PRODOTTO: [
                CallbackQueryHandler(products.manage_product_selection,
                                     pattern='^(mod_cat_|mod_prod_|act_|back_to_prod_list)'),
                CallbackQueryHandler(products.start_modify_flow, pattern='^mod_start$'),
                CallbackQueryHandler(products.menu_prodotti, pattern='^menu_prodotti$')
            ]
        },
        fallbacks=[CommandHandler('cancel', common.cancel),
                   CallbackQueryHandler(common.cancel, pattern='^cancel_flow$')],
        per_message=False
    )

    # Aggiunta Handlers
    app.add_handler(conv_cat)
    app.add_handler(conv_prod)

    app.add_handler(CommandHandler("start", common.start))
    app.add_handler(CommandHandler("cancel", common.cancel))

    # Menu Navigations
    app.add_handler(CallbackQueryHandler(common.start, pattern='^main_menu$'))
    app.add_handler(CallbackQueryHandler(categories.menu_categorie, pattern='^menu_categorie$'))
    app.add_handler(CallbackQueryHandler(products.menu_prodotti, pattern='^menu_prodotti$'))

    # Views & Prints
    app.add_handler(CallbackQueryHandler(products.show_full_inventory, pattern='^show_full_inventory$'))
    app.add_handler(CallbackQueryHandler(products.show_shopping_list, pattern='^show_shopping_list$'))
    app.add_handler(CallbackQueryHandler(products.print_shopping_list_text, pattern='^print_shopping_list$'))
    app.add_handler(CallbackQueryHandler(products.print_full_inventory_text, pattern='^print_full_inventory$'))

    print("🚀 HomeStock è in esecuzione...")
    print("Premi Ctrl+C per fermare lo script start.sh")

    # 3. AVVIO CON GESTIONE CRASH
    # Usiamo run_polling "pulito" perché la gestione errori è delegata a global_error_handler
    # Tuttavia, teniamo il try/except esterno per catturare errori in fase di avvio iniziale.
    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"\n❌ ERRORE FATALE MAIN: {e}")
        # Se capita qualcosa qui, forziamo l'uscita per start.sh
        os._exit(1)