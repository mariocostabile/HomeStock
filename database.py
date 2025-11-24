import sqlite3

DB_NAME = "homestock.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabella Categorie
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categorie (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        UNIQUE(owner_id, nome)
    )
    ''')

    # Tabella Prodotti
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prodotti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        categoria_id INTEGER,
        nome TEXT NOT NULL,
        quantita REAL DEFAULT 0,
        unita_misura TEXT DEFAULT 'pz',
        soglia_minima REAL DEFAULT 1,
        tipo_scadenza TEXT, 
        FOREIGN KEY (categoria_id) REFERENCES categorie (id) ON DELETE SET NULL
    )
    ''')
    conn.commit()
    conn.close()

# --- CATEGORIE ---

def add_category(owner_id, nome_categoria):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO categorie (owner_id, nome) VALUES (?, ?)", (owner_id, nome_categoria))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_categories(owner_id):
    conn = get_connection()
    curs = conn.execute("SELECT * FROM categorie WHERE owner_id = ?", (owner_id,))
    result = curs.fetchall()
    conn.close()
    return result

# --- PRODOTTI ---

def add_product(owner_id, categoria_id, nome, quantita, soglia):
    conn = get_connection()
    conn.execute('''
        INSERT INTO prodotti (owner_id, categoria_id, nome, quantita, soglia_minima)
        VALUES (?, ?, ?, ?, ?)
    ''', (owner_id, categoria_id, nome, quantita, soglia))
    conn.commit()
    conn.close()

def get_products(owner_id):
    conn = get_connection()
    query = '''
        SELECT p.*, c.nome as nome_categoria 
        FROM prodotti p
        LEFT JOIN categorie c ON p.categoria_id = c.id
        WHERE p.owner_id = ?
        ORDER BY c.nome, p.nome
    '''
    curs = conn.execute(query, (owner_id,))
    result = curs.fetchall()
    conn.close()
    return result

def get_low_stock_products(owner_id):
    conn = get_connection()
    query = '''
        SELECT p.*, c.nome as nome_categoria 
        FROM prodotti p
        LEFT JOIN categorie c ON p.categoria_id = c.id
        WHERE p.owner_id = ? AND p.quantita <= p.soglia_minima
        ORDER BY c.nome, p.nome
    '''
    curs = conn.execute(query, (owner_id,))
    result = curs.fetchall()
    conn.close()
    return result

# --- FUNZIONI PER LA MODIFICA (AGGIORNATE) ---

def get_products_by_category(category_id):
    """Restituisce solo i prodotti di una certa categoria"""
    conn = get_connection()
    query = "SELECT * FROM prodotti WHERE categoria_id = ?"
    curs = conn.execute(query, (category_id,))
    result = curs.fetchall()
    conn.close()
    return result

def get_product_by_id(product_id):
    """Restituisce un singolo prodotto"""
    conn = get_connection()
    curs = conn.execute("SELECT * FROM prodotti WHERE id = ?", (product_id,))
    result = curs.fetchone()
    conn.close()
    return result

def update_product_quantity(product_id, new_quantity):
    """Aggiorna la quantità"""
    conn = get_connection()
    conn.execute("UPDATE prodotti SET quantita = ? WHERE id = ?", (new_quantity, product_id))
    conn.commit()
    conn.close()

def update_product_threshold(product_id, new_threshold):
    """NUOVA: Aggiorna la soglia minima"""
    conn = get_connection()
    conn.execute("UPDATE prodotti SET soglia_minima = ? WHERE id = ?", (new_threshold, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id):
    """Elimina il prodotto"""
    conn = get_connection()
    conn.execute("DELETE FROM prodotti WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()