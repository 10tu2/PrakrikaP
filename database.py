import sqlite3

DB_FILE = "trade_store.db"

class Database:
    """SQLite layer for wholesale hardware & plumbing trade app."""

    def __init__(self, path: str = DB_FILE):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.commit()
        self._create_tables()
        self._migrate()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def _create_tables(self):
        stmts = [
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )""",
            """
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                phone TEXT,
                address TEXT
            )""",
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                phone TEXT,
                address TEXT
            )""",
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT,
                price REAL NOT NULL DEFAULT 0,
                stock INTEGER NOT NULL DEFAULT 0,
                category_id INTEGER,
                supplier_id INTEGER
            )""",
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                date TEXT NOT NULL DEFAULT (date('now')),
                status TEXT NOT NULL DEFAULT 'новый',
                total REAL NOT NULL DEFAULT 0
            )""",
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER,
                qty INTEGER NOT NULL DEFAULT 1,
                price REAL NOT NULL DEFAULT 0
            )""",
        ]
        for stmt in stmts:
            self.conn.execute(stmt)
        self.conn.commit()

    # ------------------------------------------------------------------
    # Migrations
    # ------------------------------------------------------------------
    def _migrate(self):
        """Add missing columns to existing tables."""
        def has_column(table, col):
            chk = self.conn.execute(
                "SELECT 1 FROM pragma_table_info(?) WHERE name=?",
                (table, col)
            ).fetchone()
            return chk is not None

        migrations = [
            ("products", "sku", "ALTER TABLE products ADD COLUMN sku TEXT"),
            ("products", "price", "ALTER TABLE products ADD COLUMN price REAL NOT NULL DEFAULT 0"),
            ("products", "stock", "ALTER TABLE products ADD COLUMN stock INTEGER NOT NULL DEFAULT 0"),
            ("products", "category_id", "ALTER TABLE products ADD COLUMN category_id INTEGER"),
            ("products", "supplier_id", "ALTER TABLE products ADD COLUMN supplier_id INTEGER"),
            ("orders", "total", "ALTER TABLE orders ADD COLUMN total REAL NOT NULL DEFAULT 0"),
        ]
        for table, col, sql in migrations:
            if not has_column(table, col):
                try:
                    self.conn.execute(sql)
                    self.conn.commit()
                except sqlite3.OperationalError:
                    pass

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------
    def execute(self, sql: str, params: tuple = ()) -> int:
        """Execute a write statement; return lastrowid."""
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur.lastrowid

    def fetchone(self, sql: str, params: tuple = ()):
        return self.conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: tuple = ()):
        return self.conn.execute(sql, params).fetchall()

    # ------------------------------------------------------------------
    # Order helpers
    # ------------------------------------------------------------------
    def update_order_status(self, oid: int, status: str):
        self.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))

    def delete_order(self, oid: int):
        self.execute("DELETE FROM orders WHERE id=?", (oid,))

    def get_order_items(self, oid: int):
        sql = """
            SELECT oi.id,
                   COALESCE(p.name, '') AS product,
                   oi.qty,
                   oi.price,
                   oi.qty * oi.price AS subtotal
            FROM order_items oi
            LEFT JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
        """
        return self.fetchall(sql, (oid,))

    def add_order_item(self, order_id: int, product_id: int, qty: int, price: float) -> int:
        row_id = self.execute(
            "INSERT INTO order_items (order_id, product_id, qty, price) VALUES (?,?,?,?)",
            (order_id, product_id, qty, price),
        )
        self._recalc_order(order_id)
        return row_id

    def delete_order_item(self, item_id: int, order_id: int):
        self.execute("DELETE FROM order_items WHERE id=?", (item_id,))
        self._recalc_order(order_id)

    def _recalc_order(self, order_id: int):
        row = self.fetchone(
            "SELECT COALESCE(SUM(qty * price), 0) AS total FROM order_items WHERE order_id=?",
            (order_id,),
        )
        self.execute("UPDATE orders SET total=? WHERE id=?", (row["total"], order_id))

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def close(self):
        self.conn.close()
