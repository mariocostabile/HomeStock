from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import database
import constants
import utils


# --- MENU PRINCIPALE CATEGORIE ---
async def menu_categorie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # MODIFICA: Usiamo la CHAT (gruppo o privato) come proprietario
    owner_id = update.effective_chat.id
    categorie = database.get_categories(owner_id)

    text = "📂 **Gestione Categorie**\n\nEcco le categorie di questo inventario:"
    if not categorie:
        text += "\n_Nessuna categoria presente._"
    else:
        for cat in categorie:
            text += f"\n• {cat['nome']}"

    buttons = [
        InlineKeyboardButton("➕ Nuova Categoria", callback_data='add_cat'),
        InlineKeyboardButton("✏️ Modifica / Elimina", callback_data='edit_cat_list')
    ]

    markup = utils.create_smart_grid(buttons, back_button_data='main_menu', cols=1)

    await query.edit_message_text(text, reply_markup=markup, parse_mode='Markdown')
    return ConversationHandler.END


# --- FLUSSO AGGIUNTA ---
async def ask_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_cat_menu')]]
    await query.edit_message_text("✍️ **Scrivi il nome della categoria:**", reply_markup=InlineKeyboardMarkup(keyboard),
                                  parse_mode='Markdown')
    return constants.INSERIMENTO_NOME_CATEGORIA


async def save_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.message.text
    # MODIFICA: Usiamo la CHAT come proprietario
    owner_id = update.effective_chat.id

    if database.add_category(owner_id, nome):
        msg = f"✅ Categoria **{nome}** creata!"
    else:
        msg = f"❌ La categoria **{nome}** esiste già!"

    buttons = [InlineKeyboardButton("➕ Ancora una", callback_data='add_cat')]
    markup = utils.create_smart_grid(buttons, back_button_data='back_to_cat_menu')

    await update.message.reply_text(msg, reply_markup=markup, parse_mode='Markdown')
    return constants.SCELTA_DOPO_CATEGORIA


# --- FLUSSO MODIFICA/ELIMINA ---

async def list_categories_for_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra la lista delle categorie (A SCACCHIERA)"""
    # MODIFICA: Usiamo la CHAT
    chat_id = update.effective_chat.id

    query = update.callback_query if update.callback_query else None

    categorie = database.get_categories(chat_id)
    flash_message = context.user_data.pop('flash_msg', None)

    base_text = "✏️ **Quale categoria vuoi modificare?**"
    text = f"{flash_message}\n\n{base_text}" if flash_message else base_text

    if not categorie:
        if query:
            await query.answer("Nessuna categoria da modificare!", show_alert=True)
            return await menu_categorie(update, context)
        else:
            await update.message.reply_text("Nessuna categoria rimasta.")
            return ConversationHandler.END

    buttons = []
    for cat in categorie:
        buttons.append(InlineKeyboardButton(f"📂 {cat['nome']}", callback_data=f"sel_edit_cat_{cat['id']}"))

    markup = utils.create_smart_grid(buttons, back_button_data='back_to_cat_menu')

    if query:
        await query.answer()
        try:
            await query.edit_message_text(text, reply_markup=markup, parse_mode='Markdown')
        except Exception:
            await query.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')

    return constants.MODIFICA_CATEGORIA


# --- FUNZIONE HELPER PER DISEGNARE IL PANNELLO ---
async def render_category_panel(query, cat_id):
    cat = database.get_category_by_id(cat_id)

    if not cat:
        return False

    n_prod = database.count_products_in_category(cat_id)

    text = (
        f"📂 **Modifica: {cat['nome']}**\n"
        f"Contiene {n_prod} prodotti.\n\n"
        f"Cosa vuoi fare?"
    )

    buttons = [
        InlineKeyboardButton("✏️ Rinomina", callback_data='act_cat_rename'),
        InlineKeyboardButton("🗑️ Elimina", callback_data='act_cat_delete')
    ]
    markup = utils.create_smart_grid(buttons, back_button_data='edit_cat_list')

    await query.edit_message_text(text, reply_markup=markup, parse_mode='Markdown')
    return True


async def show_category_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    cat_id = parts[-1]
    context.user_data['edit_cat_id'] = cat_id

    if not await render_category_panel(query, cat_id):
        await query.answer("Categoria non trovata.")
        return await list_categories_for_edit(update, context)

    return constants.AZIONI_CATEGORIA


async def handle_category_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action = query.data
    cat_id = context.user_data.get('edit_cat_id')

    if action == 'edit_cat_list':
        return await list_categories_for_edit(update, context)

    if action == 'act_cat_delete':
        database.delete_category(cat_id)
        context.user_data['flash_msg'] = "🗑️ **Categoria eliminata con successo!**"
        return await list_categories_for_edit(update, context)

    if action == 'act_cat_rename':
        await query.answer()
        keyboard = [[InlineKeyboardButton("🔙 Annulla", callback_data='back_to_cat_panel')]]
        await query.edit_message_text("✍️ **Scrivi il nuovo nome:**", reply_markup=InlineKeyboardMarkup(keyboard),
                                      parse_mode='Markdown')
        return constants.RINOMINA_CATEGORIA

    if action == 'back_to_cat_panel':
        await query.answer()
        if not await render_category_panel(query, cat_id):
            return await list_categories_for_edit(update, context)
        return constants.AZIONI_CATEGORIA


async def save_renamed_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text
    cat_id = context.user_data['edit_cat_id']

    if database.update_category_name(cat_id, new_name):
        context.user_data['flash_msg'] = f"✅ Rinomina completata: **{new_name}**"
        return await list_categories_for_edit(update, context)
    else:
        await update.message.reply_text("❌ Esiste già una categoria con questo nome! Riprova o clicca Annulla.")
        return constants.RINOMINA_CATEGORIA