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

def format_inventory_message(products, title="📋 Elenco Prodotti", shopping_list_mode=False):
    """
    Formatta la lista dei prodotti.
    shopping_list_mode=True: Separa 'Da Comprare' (Rosso) da 'Opzionali' (Giallo).
    shopping_list_mode=False: Mostra tutto raggruppato per categoria con icone R/G/V.
    """
    if not products:
        if shopping_list_mode:
            return f"{title}\n\n🎉 **Ottimo! Hai tutto quello che ti serve.**\nLa dispensa è piena."
        else:
            return f"{title}\n\n📦 **Nessun prodotto trovato.**\nInizia ad aggiungere qualcosa!"

    text = f"**{title}**\n"

    # --- LOGICA LISTA DELLA SPESA (SEPARATA) ---
    if shopping_list_mode:
        red_list = []  # Quantità < Soglia
        yellow_list = []  # Quantità == Soglia

        for p in products:
            if p['quantita'] < p['soglia_minima']:
                red_list.append(p)
            elif p['quantita'] == p['soglia_minima']:
                yellow_list.append(p)

        # 1. Sezione DA COMPRARE (Rossi)
        if red_list:
            text += "\n🔥 **DA COMPRARE**\n"
            grouped_red = {}
            for p in red_list:
                cat = p['nome_categoria'] if p['nome_categoria'] else "Altro"
                if cat not in grouped_red: grouped_red[cat] = []
                grouped_red[cat].append(p)

            for category, items in grouped_red.items():
                for item in items:
                    # Rimuove .0 se è intero
                    qty_str = f"{int(item['quantita'])}" if item['quantita'].is_integer() else f"{item['quantita']}"
                    # FORMATO: "🔴 Nome: Quantità"
                    text += f"🔴 **{item['nome']}**: {qty_str}\n"

        # 2. Sezione OPZIONALI (Gialli)
        if yellow_list:
            text += "\n⚠️ **OPZIONALI (In esaurimento)**\n"
            grouped_yellow = {}
            for p in yellow_list:
                cat = p['nome_categoria'] if p['nome_categoria'] else "Altro"
                if cat not in grouped_yellow: grouped_yellow[cat] = []
                grouped_yellow[cat].append(p)

            for category, items in grouped_yellow.items():
                for item in items:
                    # Rimuove .0 se è intero
                    qty_str = f"{int(item['quantita'])}" if item['quantita'].is_integer() else f"{item['quantita']}"
                    # FORMATO: "🟡 Nome: Quantità"
                    text += f"🟡 **{item['nome']}**: {qty_str}\n"

        return text

    # --- LOGICA INVENTARIO COMPLETO (STANDARD) ---
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

            # Logica Icone a 3 stati
            if qty < soglia:
                icon = "🔴"  # Sotto soglia
            elif qty == soglia:
                icon = "🟡"  # Al limite
            else:
                icon = "🟢"  # Ok

            qty_str = f"{int(qty)}" if qty.is_integer() else f"{qty}"
            soglia_str = f"{int(soglia)}" if soglia.is_integer() else f"{soglia}"

            # FORMATO INVENTARIO: "🔴 Nome: Quantità (Min: Soglia)"
            text += f"{icon} **{item['nome']}**: {qty_str} (Min: {soglia_str})\n"

    return text