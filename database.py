"""Database module for PrakrikaP warehouse management app.

Handles SQLite connections, schema creation, seeding, and common queries.
All database operations are wrapped in try/except blocks to prevent crashes.
"""
import sqlite3

DB_FILE = "trade_store.db"


class Database:
    """Safe database wrapper for SQLite operations."""

    def __init__(self, path=DB_FILE):
        self._initialised = False
        self.path = path
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            self._initialised = True
            self.init_db()
            self.seed()
        except Exception as e:
            self._initialised = False
            raise RuntimeError(f"Cannot open database: {e}")

    def execute(self, sql, params=()):
        """Execute SQL and commit. Returns cursor or None on failure."""
        if not self._initialised:
            return None
        try:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            self.conn.commit()
            return cur
        except Exception:
            return None

    def fetchall(self, sql, params=()):
        """Fetch all rows. Returns empty list on failure."""
        if not self._initialised:
            return []
        try:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            return cur.fetchall()
        except Exception:
            return []

    def fetchone(self, sql, params=()):
        """Fetch single row. Returns None on failure."""
        if not self._initialised:
            return None
        try:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            return cur.fetchone()
        except Exception:
            return None

    def init_db(self):
        """Create tables if they do not exist."""
        schemas = [
            """CREATE TABLE IF NOT EXISTS categories(
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )""",
            """CREATE TABLE IF NOT EXISTS suppliers(
                supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT DEFAULT '',
                email TEXT DEFAULT '',
                address TEXT DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS customers(
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT DEFAULT '',
                email TEXT DEFAULT '',
                address TEXT DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS products(
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
            )""",
            """CREATE TABLE IF NOT EXISTS orders(
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER REFERENCES customers(customer_id),
                order_date TEXT DEFAULT CURRENT_DATE,
                status TEXT DEFAULT 'NEW',
                total REAL DEFAULT 0,
                notes TEXT DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS order_items(
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(product_id),
                quantity INTEGER DEFAULT 1,
                price REAL DEFAULT 0
            )""",
        ]
        for schema in schemas:
            self.execute(schema)

    def seed(self):
        """Insert default data if tables are empty."""
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
        """Recalculate order total from its items."""
        try:
            res = self.fetchone(
                "SELECT COALESCE(SUM(quantity * price), 0) AS total "
                "FROM order_items WHERE order_id = ?", (order_id,))
            total = float(res["total"]) if res and res["total"] is not None else 0.0
            self.execute(
                "UPDATE orders SET total = ? WHERE order_id = ?", (total, order_id))
        except Exception:
            pass

    def close(self):
        """Close database connection safely."""
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass
