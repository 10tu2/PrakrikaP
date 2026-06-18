"""
Database module for PrakrikaP warehouse management app.
Handles SQLite connections, schema creation, seeding, and common queries.
"""
import sqlite3

DB_FILE = "trade_store.db"


class Database:

    def __init__(self, path=DB_FILE):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.init_db()
        self.seed()

    def execute(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()
        return cur

    def fetchall(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def fetchone(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchone()

    def init_db(self):
        self.execute("""CREATE TABLE IF NOT EXISTS categories(
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
            )""")
        self.execute("""CREATE TABLE IF NOT EXISTS suppliers(
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            address TEXT DEFAULT ''
            )""")
        self.execute("""CREATE TABLE IF NOT EXISTS customers(
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            address TEXT DEFAULT ''
            )""")
        self.execute("""CREATE TABLE IF NOT EXISTS products(
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT UNIQUE,
            category_id INTEGER REFERENCES categories(category_id),
            supplier_id INTEGER REFERENCES suppliers(supplier_id),
            unit TEXT DEFAULT 'шт',
            price REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 0,
            description TEXT DEFAULT ''
            )""")
        self.execute("""CREATE TABLE IF NOT EXISTS orders(
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER REFERENCES customers(customer_id),
            order_date TEXT DEFAULT CURRENT_DATE,
            status TEXT DEFAULT 'NEW',
            total REAL DEFAULT 0,
            notes TEXT DEFAULT ''
            )""")
        self.execute("""CREATE TABLE IF NOT EXISTS order_items(
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(product_id),
            quantity INTEGER DEFAULT 1,
            price REAL DEFAULT 0
            )""")

    def seed(self):
        try:
            if not self.fetchone("SELECT 1 FROM categories"):
                self.execute("INSERT INTO categories (name) VALUES ('Общее')")
        except Exception:
            pass
        try:
            if not self.fetchone("SELECT 1 FROM suppliers"):
                self.execute("INSERT INTO suppliers (name) VALUES ('Общий поставщик')")
        except Exception:
            pass

    def recalc_total(self, order_id):
        try:
            res = self.fetchone(
                "SELECT COALESCE(SUM(quantity * price), 0) as total "
                "FROM order_items WHERE order_id = ?", (order_id,))
            total = res["total"] if res and res["total"] is not None else 0
            self.execute(
                "UPDATE orders SET total = ? WHERE order_id = ?",
                (total, order_id))
        except Exception:
            pass

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
