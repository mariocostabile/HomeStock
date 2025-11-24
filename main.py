import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, ConversationHandler, MessageHandler, filters
)
import config
import database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- STATI DELLA CONVERSAZIONE ---
INSERIMENTO_NOME_CATEGORIA, SCELTA_DOPO_CATEGORIA = range(2)
SCELTA_CATEGORIA_PRODOTTO, NOME_PRODOTTO, QUANTITA_PRODOTTO, SOGLIA_PRODOTTO, FINE_PRODOTTO, MODIFICA_PRODOTTO = range(
    10, 16)


# --- UTILS E FORMATTAZIONE ---

def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 Gestisci Categorie", callback_data='menu_categorie')],
        [InlineKeyboardButton("🛒 Gestisci Prodotti", callback_data='menu_prodotti')]
    ])


def format_inventory_message(products, title="📋 Elenco Prodotti"):
    if not products: return f"{title}\n\n_Nessun prodotto trovato._"
    text = f"**{title}**\n"
    grouped = {}
    for p in products:
        cat = p['nome_categoria'] if p['nome_categoria'] else "Senza Categoria"
        if cat not in grouped: grouped[cat] = []
        grouped[cat].append(p)

    for category, items in grouped.items():
        text += f"\n📂 **{category}**\n"
        for item in items:
            qty = item['quantita']
            soglia = item['soglia_minima']
            icon = "🔴" if qty <= soglia else "🟢"
            qty_str = f"{int(qty)}" if qty.is_integer() else f"{qty}"
            text += f"{icon} **{item['nome']}**: {qty_str} (Soglia: {int(soglia)})\n"
    return text


# --- MAIN MENU & NAVIGATION ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"Ciao {user.first_name}! 👋\nBenvenuto su HomeStock.\nCosa vuoi fare?"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_main_menu_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Operazione annullata.", reply_markup=get_main_menu_keyboard())
    else:
        await update.message.reply_text("❌ Operazione annullata.", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


# ==========================================
# SEZIONE 1: GESTIONE CATEGORIE
# ==========================================

async def menu_categorie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    categorie = database.get_categories(user_id)
    text = "📂 **Le tue Categorie:**\n\n"
    if not categorie:
        text += "_Nessuna categoria. Aggiungine una!_"
    else:
        for cat in categorie: text += f"• {cat['nome']}\n"
    keyboard = [[InlineKeyboardButton("➕ Nuova Categoria", callback_data='add_cat')],
                [InlineKeyboardButton("🔙 Menu Principale", callback_data='main_menu')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END


async def ask_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_cat_list')]]
    await query.edit_message_text("✍️ **Scrivi il nome della categoria:**\n(Es. Frigo, Bagno)",
                                  reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return INSERIMENTO_NOME_CATEGORIA


async def save_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.message.text
    user_id = update.effective_user.id
    if database.add_category(user_id, nome):
        msg = f"✅ Categoria **{nome}** creata!"
    else:
        msg = f"❌ La categoria **{nome}** esiste già!"
    keyboard = [[InlineKeyboardButton("➕ Ancora una", callback_data='add_cat'),
                 InlineKeyboardButton("🏠 Menu", callback_data='main_menu')]]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return SCELTA_DOPO_CATEGORIA


# ==========================================
# SEZIONE 2: GESTIONE PRODOTTI
# ==========================================

async def menu_prodotti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("➕ Aggiungi Prodotto", callback_data='add_prod_start')],
        [InlineKeyboardButton("✏️ Modifica / Aggiorna", callback_data='mod_start')],
        [InlineKeyboardButton("🚨 Genera Lista Spesa", callback_data='show_shopping_list')],
        [InlineKeyboardButton("📋 Inventario Completo", callback_data='show_full_inventory')],
        [InlineKeyboardButton("🔙 Menu Principale", callback_data='main_menu')]
    ]
    await query.edit_message_text("🛒 **Gestione Prodotti**\nCosa vuoi fare?",
                                  reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END


# --- VISUALIZZAZIONE ---
async def show_full_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = database.get_products(update.effective_user.id)
    message_text = format_inventory_message(products, title="📋 Inventario Completo")
    keyboard = [[InlineKeyboardButton("🔙 Menu Prodotti", callback_data='menu_prodotti')]]
    await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


async def show_shopping_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = database.get_low_stock_products(update.effective_user.id)
    message_text = format_inventory_message(products, title="🚨 Lista della Spesa")
    if not products: message_text += "\n🎉 Ottimo! Hai tutto quello che ti serve."
    keyboard = [[InlineKeyboardButton("🔙 Menu Prodotti", callback_data='menu_prodotti')]]
    await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


# --- MODIFICA PRODOTTI (LOGICA CORRETTA PER ELIMINA) ---

async def start_modify_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Mostra categorie per modifica"""
    query = update.callback_query
    await query.answer()
    categorie = database.get_categories(update.effective_user.id)

    if not categorie:
        await query.edit_message_text("⚠️ Non hai categorie!", reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Indietro", callback_data='menu_prodotti')]]))
        return ConversationHandler.END

    keyboard = []
    for cat in categorie:
        keyboard.append([InlineKeyboardButton(f"📂 {cat['nome']}", callback_data=f"mod_cat_{cat['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Indietro", callback_data='menu_prodotti')])

    await query.edit_message_text("✏️ **Scegli una categoria da modificare:**",
                                  reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return MODIFICA_PRODOTTO


async def list_products_for_category(query, context, cat_id):
    products = database.get_products_by_category(cat_id)
    keyboard = []
    if products:
        for p in products:
            keyboard.append([InlineKeyboardButton(f"{p['nome']}", callback_data=f"mod_prod_{p['id']}")])
    else:
        pass

    keyboard.append([InlineKeyboardButton("🔙 Indietro", callback_data='mod_start')])
    await query.edit_message_text("📦 **Scegli il prodotto da gestire:**", reply_markup=InlineKeyboardMarkup(keyboard),
                                  parse_mode='Markdown')


async def manage_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce navigazione e modifica"""
    query = update.callback_query
    data = query.data

    # 1. SCELTA CATEGORIA -> MOSTRA PRODOTTI
    if data.startswith("mod_cat_"):
        cat_id = data.split("_")[2]
        context.user_data['current_mod_cat_id'] = cat_id
        await list_products_for_category(query, context, cat_id)
        return MODIFICA_PRODOTTO

    # 2. SCELTA PRODOTTO -> MOSTRA PANNELLO
    if data.startswith("mod_prod_"):
        prod_id = data.split("_")[2]
        prod = database.get_product_by_id(prod_id)
        context.user_data['current_mod_cat_id'] = prod['categoria_id']
        await show_control_panel(query, prod)
        return MODIFICA_PRODOTTO

    # 3. AZIONI (+ / - / DELETE)
    if data.startswith("act_"):
        parts = data.split("_")

        # --- CASO SPECIALE: DELETE (Ha solo 3 parti: act_del_ID) ---
        if parts[1] == "del":
            prod_id = parts[2]  # Qui l'ID è all'indice 2!
            database.delete_product(prod_id)
            await query.answer("🗑️ Prodotto eliminato!")
            cat_id = context.user_data.get('current_mod_cat_id')
            await list_products_for_category(query, context, cat_id)
            return MODIFICA_PRODOTTO

        # --- CASO STANDARD: STOCK/SOGLIA (Ha 4 parti: act_stock_plus_ID) ---
        target = parts[1]
        action = parts[2]
        prod_id = parts[3]  # Qui l'ID è all'indice 3

        prod = database.get_product_by_id(prod_id)
        if not prod:
            await query.answer("Errore: Prodotto non trovato.", show_alert=True)
            return MODIFICA_PRODOTTO

        if target == "stock":
            new_val = prod['quantita'] + 1 if action == "plus" else prod['quantita'] - 1
            if new_val < 0: new_val = 0
            database.update_product_quantity(prod_id, new_val)
            await query.answer(f"Stock: {new_val}")

        elif target == "thr":
            new_val = prod['soglia_minima'] + 1 if action == "plus" else prod['soglia_minima'] - 1
            if new_val < 0: new_val = 0
            database.update_product_threshold(prod_id, new_val)
            await query.answer(f"Soglia: {new_val}")

        # Ricarica pannello
        updated_prod = database.get_product_by_id(prod_id)
        await show_control_panel(query, updated_prod)
        return MODIFICA_PRODOTTO

    # 4. TORNA ALLA LISTA PRODOTTI
    if data == "back_to_prod_list":
        cat_id = context.user_data.get('current_mod_cat_id')
        await list_products_for_category(query, context, cat_id)
        return MODIFICA_PRODOTTO


async def show_control_panel(query, prod):
    """Disegna il pannello"""
    qty = prod['quantita']
    soglia = prod['soglia_minima']
    qty_str = f"{int(qty)}" if qty.is_integer() else f"{qty}"
    soglia_str = f"{int(soglia)}" if soglia.is_integer() else f"{soglia}"

    status = "🟢 OK" if qty > soglia else "🔴 SCORTA BASSA"

    text = (
        f"✏️ **Gestione: {prod['nome']}**\n"
        f"----------------------------\n"
        f"📦 Quantità: **{qty_str}**\n"
        f"⚠️ Soglia: **{soglia_str}**\n"
        f"Stato: {status}\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("➖ Stock", callback_data=f"act_stock_minus_{prod['id']}"),
            InlineKeyboardButton("Stock ➕", callback_data=f"act_stock_plus_{prod['id']}")
        ],
        [
            InlineKeyboardButton("➖ Soglia", callback_data=f"act_thr_minus_{prod['id']}"),
            InlineKeyboardButton("Soglia ➕", callback_data=f"act_thr_plus_{prod['id']}")
        ],
        [InlineKeyboardButton("🗑️ Elimina Prodotto", callback_data=f"act_del_{prod['id']}")],
        [InlineKeyboardButton("🔙 Indietro", callback_data="back_to_prod_list")]
    ]

    try:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except Exception:
        pass


# --- FLOW INSERIMENTO (Standard) ---
async def step_1_ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    categorie = database.get_categories(user_id)
    if not categorie:
        await query.edit_message_text("⚠️ Non hai categorie!", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END
    keyboard = []
    for cat in categorie: keyboard.append([InlineKeyboardButton(cat['nome'], callback_data=f"sel_cat_{cat['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Indietro", callback_data='menu_prodotti')])
    if query.message: await query.edit_message_text("1️⃣ **Scegli la categoria:**",
                                                    reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return SCELTA_CATEGORIA_PRODOTTO


async def step_2_ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("sel_cat_"): context.user_data['temp_cat_id'] = query.data.split("_")[2]
    keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_step_1')]]
    await query.edit_message_text("2️⃣ **Come si chiama il prodotto?**", reply_markup=InlineKeyboardMarkup(keyboard),
                                  parse_mode='Markdown')
    return NOME_PRODOTTO


async def step_3_ask_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        context.user_data['temp_nome'] = update.message.text
        keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_step_2')]]
        await update.message.reply_text(f"Ok, **{context.user_data['temp_nome']}**.\n3️⃣ **Quantità attuale?**",
                                        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_step_2')]]
        await query.edit_message_text(f"Ok, **{context.user_data.get('temp_nome')}**.\n3️⃣ **Quantità attuale?**",
                                      reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return QUANTITA_PRODOTTO


async def step_4_ask_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        try:
            context.user_data['temp_qty'] = float(update.message.text)
        except ValueError:
            return QUANTITA_PRODOTTO
        keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_step_3')]]
        await update.message.reply_text("4️⃣ **Soglia minima?**", reply_markup=InlineKeyboardMarkup(keyboard),
                                        parse_mode='Markdown')
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_step_3')]]
        await query.edit_message_text("4️⃣ **Soglia minima?**", reply_markup=InlineKeyboardMarkup(keyboard),
                                      parse_mode='Markdown')
    return SOGLIA_PRODOTTO


async def step_5_save_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        soglia = float(update.message.text)
    except ValueError:
        return SOGLIA_PRODOTTO
    database.add_product(update.effective_user.id, context.user_data['temp_cat_id'], context.user_data['temp_nome'],
                         context.user_data['temp_qty'], soglia)
    msg = f"✅ **{context.user_data['temp_nome']}** aggiunto!"
    keyboard = [[InlineKeyboardButton("➕ Altro", callback_data='add_prod_start')],
                [InlineKeyboardButton("🏠 Menu", callback_data='main_menu')]]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return FINE_PRODOTTO


# --- MAIN ---

if __name__ == '__main__':
    database.init_db()
    app = ApplicationBuilder().token(config.TOKEN).build()

    conv_cat = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_category_name, pattern='^add_cat$')],
        states={
            INSERIMENTO_NOME_CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_category),
                                         CallbackQueryHandler(menu_categorie, pattern='^back_to_cat_list$')],
            SCELTA_DOPO_CATEGORIA: [CallbackQueryHandler(ask_category_name, pattern='^add_cat$'),
                                    CallbackQueryHandler(start, pattern='^main_menu$')]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    conv_prod = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(step_1_ask_category, pattern='^add_prod_start$'),
            CallbackQueryHandler(start_modify_flow, pattern='^mod_start$')
        ],
        states={
            SCELTA_CATEGORIA_PRODOTTO: [CallbackQueryHandler(step_2_ask_name, pattern='^sel_cat_'),
                                        CallbackQueryHandler(menu_prodotti, pattern='^menu_prodotti$')],
            NOME_PRODOTTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_3_ask_qty),
                            CallbackQueryHandler(step_1_ask_category, pattern='^back_to_step_1$')],
            QUANTITA_PRODOTTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_4_ask_threshold),
                                CallbackQueryHandler(step_2_ask_name, pattern='^back_to_step_2$')],
            SOGLIA_PRODOTTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_5_save_final),
                              CallbackQueryHandler(step_3_ask_qty, pattern='^back_to_step_3$')],
            FINE_PRODOTTO: [CallbackQueryHandler(step_1_ask_category, pattern='^add_prod_start$'),
                            CallbackQueryHandler(start, pattern='^main_menu$')],

            # --- MODIFICA CORRETTA ---
            MODIFICA_PRODOTTO: [
                CallbackQueryHandler(manage_product_selection, pattern='^(mod_cat_|mod_prod_|act_|back_to_prod_list)'),
                CallbackQueryHandler(start_modify_flow, pattern='^mod_start$'),
                CallbackQueryHandler(menu_prodotti, pattern='^menu_prodotti$')
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel), CallbackQueryHandler(cancel, pattern='^cancel_flow$')]
    )

    app.add_handler(conv_cat)
    app.add_handler(conv_prod)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(start, pattern='^main_menu$'))
    app.add_handler(CallbackQueryHandler(menu_categorie, pattern='^menu_categorie$'))
    app.add_handler(CallbackQueryHandler(menu_prodotti, pattern='^menu_prodotti$'))
    app.add_handler(CallbackQueryHandler(show_full_inventory, pattern='^show_full_inventory$'))
    app.add_handler(CallbackQueryHandler(show_shopping_list, pattern='^show_shopping_list$'))

    print("HomeStock è in esecuzione... 🚀")
    app.run_polling()