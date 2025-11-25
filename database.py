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

# ==========================
# SEZIONE CATEGORIE
# ==========================

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

# --- LE FUNZIONI CHE TI MANCAVANO ---

def get_category_by_id(cat_id):
    """Recupera una singola categoria per ID"""
    conn = get_connection()
    curs = conn.execute("SELECT * FROM categorie WHERE id = ?", (cat_id,))
    res = curs.fetchone()
    conn.close()
    return res

def count_products_in_category(cat_id):
    """Conta quanti prodotti ci sono in una categoria"""
    conn = get_connection()
    curs = conn.execute("SELECT COUNT(*) FROM prodotti WHERE categoria_id = ?", (cat_id,))
    count = curs.fetchone()[0]
    conn.close()
    return count

def update_category_name(cat_id, new_name):
    """Rinomina una categoria"""
    conn = get_connection()
    try:
        conn.execute("UPDATE categorie SET nome = ? WHERE id = ?", (new_name, cat_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Nome già esistente
    finally:
        conn.close()

def delete_category(cat_id):
    """Elimina una categoria e imposta i suoi prodotti come 'Senza Categoria'"""
    conn = get_connection()
    # 1. Prima scolleghiamo i prodotti (li rendiamo orfani manualmente)
    conn.execute("UPDATE prodotti SET categoria_id = NULL WHERE categoria_id = ?", (cat_id,))
    # 2. Poi cancelliamo la categoria
    conn.execute("DELETE FROM categorie WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()

# ==========================
# SEZIONE PRODOTTI
# ==========================

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

def get_orphaned_products(owner_id):
    """Recupera i prodotti che non hanno una categoria (orfani)"""
    conn = get_connection()
    curs = conn.execute("SELECT * FROM prodotti WHERE owner_id = ? AND categoria_id IS NULL", (owner_id,))
    result = curs.fetchall()
    conn.close()
    return result

# ==========================
# SEZIONE MODIFICA PRODOTTI
# ==========================

def get_products_by_category(category_id):
    conn = get_connection()
    query = "SELECT * FROM prodotti WHERE categoria_id = ?"
    curs = conn.execute(query, (category_id,))
    result = curs.fetchall()
    conn.close()
    return result

def get_product_by_id(product_id):
    conn = get_connection()
    curs = conn.execute("SELECT * FROM prodotti WHERE id = ?", (product_id,))
    result = curs.fetchone()
    conn.close()
    return result

def update_product_quantity(product_id, new_quantity):
    conn = get_connection()
    conn.execute("UPDATE prodotti SET quantita = ? WHERE id = ?", (new_quantity, product_id))
    conn.commit()
    conn.close()

def update_product_threshold(product_id, new_threshold):
    conn = get_connection()
    conn.execute("UPDATE prodotti SET soglia_minima = ? WHERE id = ?", (new_threshold, product_id))
    conn.commit()
    conn.close()

def update_product_category(product_id, new_category_id):
    conn = get_connection()
    conn.execute("UPDATE prodotti SET categoria_id = ? WHERE id = ?", (new_category_id, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = get_connection()
    conn.execute("DELETE FROM prodotti WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()