import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)
import config
import database
import constants
from handlers import common, categories, products

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == '__main__':
    # 1. Init Database
    database.init_db()

    # 2. Build App
    app = ApplicationBuilder().token(config.TOKEN).build()

    # --- CONVERSATION CATEGORIE ---
    conv_cat = ConversationHandler(
        entry_points=[
            # Aggiunta Categoria
            CallbackQueryHandler(categories.ask_category_name, pattern='^add_cat$'),

            # --- QUESTA È LA RIGA CHE PROBABILMENTE MANCAVA ---
            # Modifica / Elimina Categoria (Entry Point)
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
                CallbackQueryHandler(categories.menu_categorie, pattern='^back_to_cat_menu$')
            ],
            constants.AZIONI_CATEGORIA: [
                # Qui gestiamo le azioni, incluso il tornare alla lista
                CallbackQueryHandler(categories.handle_category_actions, pattern='^(act_cat_|edit_cat_list)')
            ],
            constants.RINOMINA_CATEGORIA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, categories.save_renamed_category),
                CallbackQueryHandler(categories.handle_category_actions, pattern='^back_to_cat_panel$')
            ]
        },
        fallbacks=[CommandHandler('cancel', common.cancel)]
    )

    # 4. Conversation Prodotti
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
                   CallbackQueryHandler(common.cancel, pattern='^cancel_flow$')]
    )

    # 5. Add Handlers
    app.add_handler(conv_cat)
    app.add_handler(conv_prod)

    app.add_handler(CommandHandler("start", common.start))
    app.add_handler(CommandHandler("cancel", common.cancel))

    # Menu Navigations
    app.add_handler(CallbackQueryHandler(common.start, pattern='^main_menu$'))
    app.add_handler(CallbackQueryHandler(categories.menu_categorie, pattern='^menu_categorie$'))
    app.add_handler(CallbackQueryHandler(products.menu_prodotti, pattern='^menu_prodotti$'))

    # Views
    app.add_handler(CallbackQueryHandler(products.show_full_inventory, pattern='^show_full_inventory$'))
    app.add_handler(CallbackQueryHandler(products.show_shopping_list, pattern='^show_shopping_list$'))

    print("HomeStock (Professional Edition) è in esecuzione... 🚀")
    app.run_polling()