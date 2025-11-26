from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# --- KEYBOARD GENERATORS ---

def create_smart_grid(buttons, back_button_data=None, cols=None):
    """
    Prende una lista piatta di bottoni.
    - Se cols=1: Forza 1 colonna (Bottoni Larghi).
    - Se cols=2: Forza 2 colonne (Griglia).
    - Se cols=None (Auto): Se bottoni >= 2 fa 2 colonne, altrimenti 1.
    Il tasto indietro viene messo sempre in fondo su una riga a parte.
    """
    keyboard = []

    # Logica decisione colonne
    use_grid = False

    if cols == 1:
        use_grid = False  # Forza lista verticale
    elif cols == 2:
        use_grid = True  # Forza griglia
    else:
        # Logica Automatica (Default)
        if len(buttons) >= 2:
            use_grid = True
        else:
            use_grid = False

    # Costruzione Layout
    if use_grid:
        for i in range(0, len(buttons), 2):
            keyboard.append(buttons[i:i + 2])
    else:
        for btn in buttons:
            keyboard.append([btn])

    # Aggiungi tasto indietro se richiesto
    if back_button_data:
        keyboard.append([InlineKeyboardButton("🔙 Indietro", callback_data=back_button_data)])

    return InlineKeyboardMarkup(keyboard)


def get_main_menu_keyboard():
    # Definiamo i bottoni del menu principale
    buttons = [
        InlineKeyboardButton("🛒 Gestisci Prodotti", callback_data='menu_prodotti'),
        InlineKeyboardButton("📂 Gestisci Categorie", callback_data='menu_categorie'),
        InlineKeyboardButton("🚨 Genera Lista Spesa", callback_data='show_shopping_list'),
        InlineKeyboardButton("📋 Inventario Completo", callback_data='show_full_inventory')
    ]
    # Smart grid automatica
    return create_smart_grid(buttons)


# --- FORMATTING ---

def format_inventory_message(products, title="📋 Elenco Prodotti"):
    """Formatta la lista dei prodotti in modo standard"""
    if not products:
        # MODIFICATO QUI: Usiamo il grassetto (**) invece del corsivo (_)
        return f"{title}\n\n📦 **Nessun prodotto trovato.**\nInizia ad aggiungere qualcosa!"

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