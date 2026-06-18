import sqlite3

DB_FILE = "trade_store.db"

class Database:
    """Database module for PrakrikaP warehouse management app.

    Handles SQLite connections, schema creation, seeding, and common queries.
    All database operations are wrapped in try/except blocks to prevent crashes.
    """

    def __init__(self, path=DB_FILE):
        try:
            self.path = path
            self.conn = sqlite3.connect(self.path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            self._initialised = True
        except Exception as e:
            self._initialised = False
            raise RuntimeError(f"Cannot open database: {e}")

    def init_db(self):
        """Create tables if they do not exist."""
        try:
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
        except Exception:
            pass

    def execute(self, sql, params=()):
        """Execute an SQL statement and commit.

        Returns the cursor for further access (e.g. lastrowid).
        Raises on fatal error.
        """
        if not self._initialised:
            raise RuntimeError("Database is not initialised")
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()
        return cur

    def fetchall(self, sql, params=()):
        """Fetch all rows matching query. Returns a list of sqlite3.Row.

        Never raises to UI; on error returns empty list.
        """
        try:
            if not self._initialised:
                return []
            cur = self.conn.cursor()
            cur.execute(sql, params)
            return cur.fetchall()
        except Exception:
            return []

    def fetchone(self, sql, params=()):
        """Fetch a single row matching query. Returns a sqlite3.Row or None.

        Never raises to UI; on error returns None.
        """
        try:
            if not self._initialised:
                return None
            cur = self.conn.cursor()
            cur.execute(sql, params)
            return cur.fetchone()
        except Exception:
            return None

    def fetchsingle(self, sql, params=(), default=0):
        """Fetch a single value. Returns default on error or no result.

        Useful for totals, aggregates, and config values.
        """
        try:
            row = self.fetchone(sql, params)
            if row is None:
                return default
            key = row.keys()[0]
            val = row[key]
            return val if val is not None else default
        except Exception:
            return default

    def seed(self):
        """Seed database with minimal data if tables are empty."""
        try:
            if self.fetchone("SELECT 1 FROM categories") is None:
                self.execute("INSERT INTO categories (name) VALUES ('Общее')")
            if self.fetchone("SELECT 1 FROM suppliers") is None:
                self.execute("INSERT INTO suppliers (name) VALUES ('Общий поставщик')")
        except Exception:
            pass

    def recalc_total(self, order_id):
        """Recalculate order total based on item rows.

        Updates orders.total safely; never raises to UI.
        """
        try:
            total_sql = (
                "SELECT COALESCE(SUM(quantity * price), 0) AS total "
                "FROM order_items WHERE order_id = ?"
            )
            total = self.fetchsingle(total_sql, (order_id,), default=0.0)
            self.execute(
                "UPDATE orders SET total = ? WHERE order_id = ?", (total, order_id)
            )
        except Exception:
            pass

    def close(self):
        """Close the database connection safely."""
        try:
            if self._initialised and self.conn:
                self.conn.close()
        except Exception:
            pass
        self._initialised = False
