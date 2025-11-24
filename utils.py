from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 Gestisci Categorie", callback_data='menu_categorie')],
        [InlineKeyboardButton("🛒 Gestisci Prodotti", callback_data='menu_prodotti')]
    ])


def format_inventory_message(products, title="📋 Elenco Prodotti"):
    if not products:
        return f"{title}\n\n_Nessun prodotto trovato._"

    text = f"**{title}**\n"

    # Raggruppamento manuale per evitare dipendenze esterne complesse
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
            # Icona: 🔴 se sotto soglia, 🟢 se ok
            icon = "🔴" if qty <= soglia else "🟢"

            # Formattazione numeri (rimuove .0 se intero)
            qty_str = f"{int(qty)}" if qty.is_integer() else f"{qty}"

            text += f"{icon} **{item['nome']}**: {qty_str} (Soglia: {int(soglia)})\n"

    return text