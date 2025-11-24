from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import database
import constants


async def menu_categorie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    categorie = database.get_categories(user_id)

    text = "📂 **Le tue Categorie:**\n\n"
    if not categorie:
        text += "_Nessuna categoria. Aggiungine una!_"
    else:
        for cat in categorie:
            text += f"• {cat['nome']}\n"

    keyboard = [
        [InlineKeyboardButton("➕ Nuova Categoria", callback_data='add_cat')],
        [InlineKeyboardButton("🔙 Menu Principale", callback_data='main_menu')]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END


async def ask_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_cat_list')]]

    await query.edit_message_text(
        "✍️ **Scrivi il nome della categoria:**\n(Es. Frigo, Bagno)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return constants.INSERIMENTO_NOME_CATEGORIA


async def save_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.message.text
    user_id = update.effective_user.id

    if database.add_category(user_id, nome):
        msg = f"✅ Categoria **{nome}** creata!"
    else:
        msg = f"❌ La categoria **{nome}** esiste già!"

    keyboard = [
        [InlineKeyboardButton("➕ Ancora una", callback_data='add_cat')],
        [InlineKeyboardButton("🏠 Menu", callback_data='main_menu')]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return constants.SCELTA_DOPO_CATEGORIA