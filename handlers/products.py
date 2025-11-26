from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import database
import constants
import utils


# --- MENU PRODOTTI ---
async def menu_prodotti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    buttons = [
        InlineKeyboardButton("➕ Aggiungi Prodotto", callback_data='add_prod_start'),
        InlineKeyboardButton("✏️ Modifica / Aggiorna", callback_data='mod_start')
    ]
    markup = utils.create_smart_grid(buttons, back_button_data='main_menu')

    await query.edit_message_text("🛒 **Gestione Prodotti**\nQui puoi aggiungere o modificare le scorte.",
                                  reply_markup=markup, parse_mode='Markdown')
    return ConversationHandler.END


# --- VISUALIZZAZIONE (DASHBOARD INTERATTIVA) ---

async def show_full_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = database.get_products(update.effective_user.id)

    # TITOLO DASHBOARD
    message_text = utils.format_inventory_message(products, title="📋 **Situazione Dispensa**")

    buttons = [InlineKeyboardButton("📤 Invia in Chat", callback_data='print_full_inventory')]
    markup = utils.create_smart_grid(buttons, back_button_data='main_menu')

    await query.edit_message_text(message_text, reply_markup=markup, parse_mode='Markdown')


async def show_shopping_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = database.get_low_stock_products(update.effective_user.id)

    if not products:
        message_text = "🚨 **Situazione Scorte**\n\n🎉 **Ottimo! Hai tutto quello che ti serve.**"
        buttons = []
    else:
        # TITOLO DASHBOARD
        message_text = utils.format_inventory_message(products, title="🚨 **Prodotti in Esaurimento**")
        buttons = [InlineKeyboardButton("📤 Invia in Chat", callback_data='print_shopping_list')]

    markup = utils.create_smart_grid(buttons, back_button_data='main_menu')

    await query.edit_message_text(message_text, reply_markup=markup, parse_mode='Markdown')


# --- FUNZIONI DI STAMPA (MODIFICATE: TORNA AL MENU) ---

async def print_shopping_list_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    user = update.effective_user

    products = database.get_low_stock_products(user.id)
    if not products: return

    # 1. TITOLO SCONTRINO
    message_text = utils.format_inventory_message(products, title="🛒 **LISTA DELLA SPESA**")

    # 2. CANCELLIAMO il vecchio menu
    await query.message.delete()

    # 3. Mandiamo lo SCONTRINO (Lista statica)
    await context.bot.send_message(chat_id=chat_id, text=message_text, parse_mode='Markdown')

    # 4. Mandiamo il MENU PRINCIPALE (Invece della dashboard prodotti)
    menu_text = f"Ciao {user.first_name}! 👋\nEccoci tornati al menu principale."
    menu_markup = utils.get_main_menu_keyboard()

    await context.bot.send_message(chat_id=chat_id, text=menu_text, reply_markup=menu_markup)


async def print_full_inventory_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    user = update.effective_user

    products = database.get_products(user.id)

    # 1. TITOLO REPORT
    message_text = utils.format_inventory_message(products, title="📦 **INVENTARIO TOTALE**")

    # 2. Delete
    await query.message.delete()

    # 3. Manda REPORT
    await context.bot.send_message(chat_id=chat_id, text=message_text, parse_mode='Markdown')

    # 4. Manda MENU PRINCIPALE
    menu_text = f"Ciao {user.first_name}! 👋\nEccoci tornati al menu principale."
    menu_markup = utils.get_main_menu_keyboard()

    await context.bot.send_message(chat_id=chat_id, text=menu_text, reply_markup=menu_markup)


# --- INSERIMENTO PRODOTTI ---
async def step_1_ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    categorie = database.get_categories(user_id)

    if not categorie:
        await query.edit_message_text("⚠️ Non hai categorie!", reply_markup=utils.get_main_menu_keyboard())
        return ConversationHandler.END

    buttons = []
    for cat in categorie:
        buttons.append(InlineKeyboardButton(cat['nome'], callback_data=f"sel_cat_{cat['id']}"))

    markup = utils.create_smart_grid(buttons, back_button_data='menu_prodotti')

    if query.message:
        await query.edit_message_text("**Scegli la categoria:**", reply_markup=markup, parse_mode='Markdown')
    return constants.SCELTA_CATEGORIA_PRODOTTO


async def step_2_ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("sel_cat_"):
        context.user_data['temp_cat_id'] = query.data.split("_")[2]

    keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_step_1')]]
    await query.edit_message_text("**Come si chiama il prodotto?**", reply_markup=InlineKeyboardMarkup(keyboard),
                                  parse_mode='Markdown')
    return constants.NOME_PRODOTTO


async def step_3_ask_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        context.user_data['temp_nome'] = update.message.text
        keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_step_2')]]
        await update.message.reply_text(
            f"Ok, **{context.user_data['temp_nome']}**.\n**Quantità attuale?**\n(Scrivi solo il numero)",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_step_2')]]
        await query.edit_message_text(
            f"Ok, **{context.user_data.get('temp_nome')}**.\n**Quantità attuale?**\n(Scrivi solo il numero)",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return constants.QUANTITA_PRODOTTO


async def step_4_ask_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        try:
            context.user_data['temp_qty'] = float(update.message.text)
        except ValueError:
            await update.message.reply_text("⚠️ Per favore inserisci un numero valido!")
            return constants.QUANTITA_PRODOTTO

        keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_step_3')]]
        await update.message.reply_text("**Soglia minima?**", reply_markup=InlineKeyboardMarkup(keyboard),
                                        parse_mode='Markdown')
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_step_3')]]
        await query.edit_message_text("4️⃣ **Quantità Minima?**", reply_markup=InlineKeyboardMarkup(keyboard),
                                      parse_mode='Markdown')
    return constants.SOGLIA_PRODOTTO


async def step_5_save_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        soglia = float(update.message.text)
    except ValueError:
        await update.message.reply_text("⚠️ Numero non valido!")
        return constants.SOGLIA_PRODOTTO

    database.add_product(
        update.effective_user.id,
        context.user_data['temp_cat_id'],
        context.user_data['temp_nome'],
        context.user_data['temp_qty'],
        soglia
    )

    msg = f"✅ **{context.user_data['temp_nome']}** aggiunto!\n(Stock: {context.user_data['temp_qty']} | Minimo: {soglia})"

    keyboard = [[InlineKeyboardButton("➕ Altro", callback_data='add_prod_start')],
                [InlineKeyboardButton("🏠 Menu", callback_data='main_menu')]]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return constants.FINE_PRODOTTO

# --- MODIFICA PRODOTTI ---

async def list_products_for_category(query, context, cat_id):
    if cat_id == 'orphan':
        products = database.get_orphaned_products(query.from_user.id)
        title = "⚠️ Prodotti Senza Categoria"
    else:
        products = database.get_products_by_category(cat_id)
        title = "📦 Scegli il prodotto:"

    buttons = []
    if products:
        for p in products:
            buttons.append(InlineKeyboardButton(f"{p['nome']}", callback_data=f"mod_prod_{p['id']}"))

    markup = utils.create_smart_grid(buttons, back_button_data='mod_start')

    text = f"**{title}**" if products else f"{title}\n\n_Vuoto_"
    await query.edit_message_text(text, reply_markup=markup, parse_mode='Markdown')


async def show_move_category_selection(query, context, prod_id):
    user_id = query.from_user.id
    categorie = database.get_categories(user_id)

    if not categorie:
        await query.answer("Crea prima delle categorie!", show_alert=True)
        return

    buttons = []
    for cat in categorie:
        buttons.append(InlineKeyboardButton(f"📂 {cat['nome']}", callback_data=f"act_move_do_{prod_id}_{cat['id']}"))

    markup = utils.create_smart_grid(buttons, back_button_data=f"mod_prod_{prod_id}")

    await query.edit_message_text("📍 **Dove vuoi spostare questo prodotto?**", reply_markup=markup,
                                  parse_mode='Markdown')


async def show_control_panel(query, prod):
    qty = prod['quantita']
    soglia = prod['soglia_minima']
    qty_str = f"{int(qty)}" if qty.is_integer() else f"{qty}"
    soglia_str = f"{int(soglia)}" if soglia.is_integer() else f"{soglia}"

    cat_name = "⚠️ Nessuna"
    if prod['categoria_id']:
        cat_info = database.get_category_by_id(prod['categoria_id'])
        if cat_info: cat_name = cat_info['nome']

    status = "🟢 OK" if qty > soglia else "🔴 SCORTA BASSA"

    text = (
        f"✏️ **Gestione: {prod['nome']}**\n"
        f"📂 Categoria: {cat_name}\n"
        f"----------------------------\n"
        f"📦 Quantità: **{qty_str}**\n"
        f"⚠️ Minimo: **{soglia_str}**\n"
        f"Stato: {status}\n"
    )

    keyboard = [
        [InlineKeyboardButton("➖ Stock", callback_data=f"act_stock_minus_{prod['id']}"),
         InlineKeyboardButton("Stock ➕", callback_data=f"act_stock_plus_{prod['id']}")],
        [InlineKeyboardButton("➖ Minimo", callback_data=f"act_thr_minus_{prod['id']}"),
         InlineKeyboardButton("Minimo ➕", callback_data=f"act_thr_plus_{prod['id']}")],
        [InlineKeyboardButton("📂 Sposta in Categoria", callback_data=f"act_move_start_{prod['id']}")],
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
    user_id = update.effective_user.id
    categorie = database.get_categories(user_id)
    orphans = database.get_orphaned_products(user_id)

    buttons = []

    if orphans:
        buttons.append(InlineKeyboardButton(f"⚠️ Senza Categoria ({len(orphans)})", callback_data="mod_cat_orphan"))

    if not categorie and not orphans:
        await query.edit_message_text("⚠️ Non hai categorie né prodotti!", reply_markup=utils.get_main_menu_keyboard())
        return ConversationHandler.END

    for cat in categorie:
        buttons.append(InlineKeyboardButton(f"📂 {cat['nome']}", callback_data=f"mod_cat_{cat['id']}"))

    markup = utils.create_smart_grid(buttons, back_button_data='menu_prodotti')

    await query.edit_message_text("✏️ **Scegli una categoria da modificare:**", reply_markup=markup,
                                  parse_mode='Markdown')
    return constants.MODIFICA_PRODOTTO


async def manage_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("mod_cat_"):
        cat_id = data.split("_")[2]
        context.user_data['current_mod_cat_id'] = cat_id
        await list_products_for_category(query, context, cat_id)
        return constants.MODIFICA_PRODOTTO

    if data.startswith("mod_prod_"):
        prod_id = data.split("_")[2]
        prod = database.get_product_by_id(prod_id)
        if prod['categoria_id'] is None:
            context.user_data['current_mod_cat_id'] = 'orphan'
        else:
            context.user_data['current_mod_cat_id'] = prod['categoria_id']
        await show_control_panel(query, prod)
        return constants.MODIFICA_PRODOTTO

    if data.startswith("act_"):
        parts = data.split("_")
        action_type = parts[1]

        if action_type == "del":
            prod_id = parts[2]
            database.delete_product(prod_id)
            await query.answer("🗑️ Prodotto eliminato!")
            cat_id = context.user_data.get('current_mod_cat_id')
            await list_products_for_category(query, context, cat_id)
            return constants.MODIFICA_PRODOTTO

        if action_type == "move" and parts[2] == "start":
            prod_id = parts[3]
            await show_move_category_selection(query, context, prod_id)
            return constants.MODIFICA_PRODOTTO

        if action_type == "move" and parts[2] == "do":
            prod_id = parts[3]
            new_cat_id = parts[4]
            database.update_product_category(prod_id, new_cat_id)
            await query.answer("✅ Prodotto spostato!")
            prod = database.get_product_by_id(prod_id)
            context.user_data['current_mod_cat_id'] = new_cat_id
            await show_control_panel(query, prod)
            return constants.MODIFICA_PRODOTTO

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

    if data == "back_to_prod_list":
        cat_id = context.user_data.get('current_mod_cat_id')
        await list_products_for_category(query, context, cat_id)
        return constants.MODIFICA_PRODOTTO