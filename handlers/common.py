from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import utils


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"Ciao {user.first_name}! 👋\nBenvenuto su HomeStock.\nCosa vuoi fare?"

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=utils.get_main_menu_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=utils.get_main_menu_keyboard())
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Operazione annullata.",
                                                      reply_markup=utils.get_main_menu_keyboard())
    else:
        await update.message.reply_text("❌ Operazione annullata.", reply_markup=utils.get_main_menu_keyboard())
    return ConversationHandler.END