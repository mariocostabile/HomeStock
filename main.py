import sys
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)
from telegram.error import TimedOut, NetworkError
from telegram.request import HTTPXRequest  # <--- IMPORTANTE: Importiamo questo

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

if __name__ == '__main__':
    # Init Database
    database.init_db()

    # --- CONFIGURAZIONE RETE ---
    # Qui impostiamo i timeout per reti mobili instabili
    trequest = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=30,   # Aumentato
        write_timeout=30,  # Aumentato
        connect_timeout=30,# Aumentato
        http_version='1.1' # Stabilità per reti mobili
    )

    # 2. Costruzione App
    app = (
        ApplicationBuilder()
        .token(config.TOKEN)
        .request(trequest)  # <--- Inseriamo la configurazione qui!
        .build()
    )

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

    # 3. AVVIO CON GESTIONE CRASH (PER START.SH)
    try:
        # Qui NON passiamo più i timeout, perché li abbiamo messi in 'trequest' sopra
        app.run_polling(
            allowed_updates=Update.ALL_TYPES
        )
    except (TimedOut, NetworkError) as e:
        print(f"\n⚠️ ERRORE DI RETE RILEVATO: {e}")
        print("🔄 Chiudo il processo Python per permettere a start.sh di riavviarlo...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRORE IMPREVISTO: {e}")
        print("🔄 Riavvio forzato...")
        sys.exit(1)