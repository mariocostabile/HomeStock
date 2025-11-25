from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# --- KEYBOARD GENERATORS ---

def create_smart_grid(buttons, back_button_data=None):
    """
    Prende una lista piatta di bottoni.
    Se sono >= 4, li mette su 2 colonne. Altrimenti 1 colonna.
    Il tasto indietro viene messo sempre in fondo su una riga a parte.
    """
    keyboard = []

    # Logica griglia
    if len(buttons) >= 2:
        for i in range(0, len(buttons), 2):
            keyboard.append(buttons[i:i + 2])
    else:
        for btn in buttons:
            keyboard.append([btn])

    # Aggiunta tasto back
    if back_button_data:
        keyboard.append([InlineKeyboardButton("🔙 Indietro", callback_data=back_button_data)])

    return InlineKeyboardMarkup(keyboard)


def get_main_menu_keyboard():
    # Definiamo solo i bottoni, la griglia pensa al layout
    buttons = [
        InlineKeyboardButton("📂 Gestisci Categorie", callback_data='menu_categorie'),
        InlineKeyboardButton("🛒 Gestisci Prodotti", callback_data='menu_prodotti')
    ]
    return create_smart_grid(buttons)


# --- FORMATTING ---

def format_inventory_message(products, title="📋 Elenco Prodotti"):
    if not products:
        return f"{title}\n\n_Nessun prodotto trovato._"

    text = f"**{title}**\n"

    grouped = {}
    for p in products:
        cat = p['nome_categoria'] if p['nome_categoria'] else "Senza Categoria"
        if cat not in grouped:
            grouped[cat] = []
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