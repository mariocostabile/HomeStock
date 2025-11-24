from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import database
import constants
import utils


# --- MENU PRODOTTI ---
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
    message_text = utils.format_inventory_message(products, title="📋 Inventario Completo")
    keyboard = [[InlineKeyboardButton("🔙 Menu Prodotti", callback_data='menu_prodotti')]]
    await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


async def show_shopping_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = database.get_low_stock_products(update.effective_user.id)
    message_text = utils.format_inventory_message(products, title="🚨 Lista della Spesa")
    if not products: message_text += "\n🎉 Ottimo! Hai tutto quello che ti serve."
    keyboard = [[InlineKeyboardButton("🔙 Menu Prodotti", callback_data='menu_prodotti')]]
    await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


# --- INSERIMENTO PRODOTTI ---
async def step_1_ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    categorie = database.get_categories(user_id)

    if not categorie:
        await query.edit_message_text("⚠️ Non hai categorie!", reply_markup=utils.get_main_menu_keyboard())
        return ConversationHandler.END

    keyboard = []
    for cat in categorie:
        keyboard.append([InlineKeyboardButton(cat['nome'], callback_data=f"sel_cat_{cat['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Indietro", callback_data='menu_prodotti')])

    if query.message:
        await query.edit_message_text("1️⃣ **Scegli la categoria:**", reply_markup=InlineKeyboardMarkup(keyboard),
                                      parse_mode='Markdown')
    return constants.SCELTA_CATEGORIA_PRODOTTO


async def step_2_ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("sel_cat_"):
        context.user_data['temp_cat_id'] = query.data.split("_")[2]

    keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_step_1')]]
    await query.edit_message_text("2️⃣ **Come si chiama il prodotto?**", reply_markup=InlineKeyboardMarkup(keyboard),
                                  parse_mode='Markdown')
    return constants.NOME_PRODOTTO


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
    return constants.QUANTITA_PRODOTTO


async def step_4_ask_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        try:
            context.user_data['temp_qty'] = float(update.message.text)
        except ValueError:
            return constants.QUANTITA_PRODOTTO

        keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_step_3')]]
        await update.message.reply_text("4️⃣ **Soglia minima?**", reply_markup=InlineKeyboardMarkup(keyboard),
                                        parse_mode='Markdown')
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_step_3')]]
        await query.edit_message_text("4️⃣ **Soglia minima?**", reply_markup=InlineKeyboardMarkup(keyboard),
                                      parse_mode='Markdown')
    return constants.SOGLIA_PRODOTTO


async def step_5_save_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        soglia = float(update.message.text)
    except ValueError:
        return constants.SOGLIA_PRODOTTO

    database.add_product(
        update.effective_user.id,
        context.user_data['temp_cat_id'],
        context.user_data['temp_nome'],
        context.user_data['temp_qty'],
        soglia
    )

    msg = f"✅ **{context.user_data['temp_nome']}** aggiunto!"
    keyboard = [[InlineKeyboardButton("➕ Altro", callback_data='add_prod_start')],
                [InlineKeyboardButton("🏠 Menu", callback_data='main_menu')]]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return constants.FINE_PRODOTTO


# --- MODIFICA PRODOTTI (HELPER & LOGIC) ---

async def list_products_for_category(query, context, cat_id):
    products = database.get_products_by_category(cat_id)
    keyboard = []
    if products:
        for p in products:
            keyboard.append([InlineKeyboardButton(f"{p['nome']}", callback_data=f"mod_prod_{p['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Indietro", callback_data='mod_start')])
    await query.edit_message_text("📦 **Scegli il prodotto da gestire:**", reply_markup=InlineKeyboardMarkup(keyboard),
                                  parse_mode='Markdown')


async def show_control_panel(query, prod):
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
        [InlineKeyboardButton("➖ Stock", callback_data=f"act_stock_minus_{prod['id']}"),
         InlineKeyboardButton("Stock ➕", callback_data=f"act_stock_plus_{prod['id']}")],
        [InlineKeyboardButton("➖ Soglia", callback_data=f"act_thr_minus_{prod['id']}"),
         InlineKeyboardButton("Soglia ➕", callback_data=f"act_thr_plus_{prod['id']}")],
        [InlineKeyboardButton("🗑️ Elimina Prodotto", callback_data=f"act_del_{prod['id']}")],
        [InlineKeyboardButton("🔙 Indietro", callback_data="back_to_prod_list")]
    ]
    try:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except Exception:
        pass


async def start_modify_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    return constants.MODIFICA_PRODOTTO


async def manage_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    # 1. SCELTA CATEGORIA -> LISTA PRODOTTI
    if data.startswith("mod_cat_"):
        cat_id = data.split("_")[2]
        context.user_data['current_mod_cat_id'] = cat_id
        await list_products_for_category(query, context, cat_id)
        return constants.MODIFICA_PRODOTTO

    # 2. SCELTA PRODOTTO -> PANNELLO
    if data.startswith("mod_prod_"):
        prod_id = data.split("_")[2]
        prod = database.get_product_by_id(prod_id)
        context.user_data['current_mod_cat_id'] = prod['categoria_id']
        await show_control_panel(query, prod)
        return constants.MODIFICA_PRODOTTO

    # 3. AZIONI
    if data.startswith("act_"):
        parts = data.split("_")

        # DELETE
        if parts[1] == "del":
            prod_id = parts[2]
            database.delete_product(prod_id)
            await query.answer("🗑️ Prodotto eliminato!")
            cat_id = context.user_data.get('current_mod_cat_id')
            await list_products_for_category(query, context, cat_id)
            return constants.MODIFICA_PRODOTTO

        # STOCK/SOGLIA
        target, action, prod_id = parts[1], parts[2], parts[3]
        prod = database.get_product_by_id(prod_id)

        if not prod:
            await query.answer("Errore: Prodotto non trovato.", show_alert=True)
            return constants.MODIFICA_PRODOTTO

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

        updated_prod = database.get_product_by_id(prod_id)
        await show_control_panel(query, updated_prod)
        return constants.MODIFICA_PRODOTTO

    # 4. BACK TO LIST
    if data == "back_to_prod_list":
        cat_id = context.user_data.get('current_mod_cat_id')
        await list_products_for_category(query, context, cat_id)
        return constants.MODIFICA_PRODOTTO