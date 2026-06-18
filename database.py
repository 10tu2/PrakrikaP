import sqlite3
import os

DB_FILE = "hardware_trade.db"


class Database:
    """SQLite database for wholesale hardware & plumbing trade app."""

    def __init__(self, path: str = DB_FILE):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _create_tables(self):
        sql = """
        CREATE TABLE IF NOT EXISTS categories (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT    NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            unit        TEXT    NOT NULL DEFAULT 'шт',
            price       REAL    NOT NULL DEFAULT 0,
            stock       INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS clients (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT NOT NULL,
            phone   TEXT,
            address TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id  INTEGER REFERENCES clients(id) ON DELETE SET NULL,
            created_at TEXT    NOT NULL DEFAULT (date('now')),
            status     TEXT    NOT NULL DEFAULT 'Новый',
            total      REAL    NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
            qty        INTEGER NOT NULL DEFAULT 1,
            price      REAL    NOT NULL DEFAULT 0
        );
        """
        self.conn.executescript(sql)
        self.conn.commit()

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------

    def fetchall(self, sql: str, params=()) -> list:
        cur = self.conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

    def fetchone(self, sql: str, params=()):
        cur = self.conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None

    def execute(self, sql: str, params=()) -> int:
        """Execute INSERT/UPDATE/DELETE and return lastrowid."""
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur.lastrowid

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------

    def get_categories(self):
        return self.fetchall("SELECT * FROM categories ORDER BY name")

    def add_category(self, name: str) -> int:
        return self.execute("INSERT INTO categories (name) VALUES (?)", (name,))

    def update_category(self, cat_id: int, name: str):
        self.execute("UPDATE categories SET name=? WHERE id=?", (name, cat_id))

    def delete_category(self, cat_id: int):
        self.execute("DELETE FROM categories WHERE id=?", (cat_id,))

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------

    def get_products(self):
        sql = """
            SELECT p.id, p.name, c.name AS category, p.unit, p.price, p.stock
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            ORDER BY p.name
        """
        return self.fetchall(sql)

    def get_product(self, pid: int):
        return self.fetchone("SELECT * FROM products WHERE id=?", (pid,))

    def add_product(self, name, category_id, unit, price, stock) -> int:
        return self.execute(
            "INSERT INTO products (name, category_id, unit, price, stock) VALUES (?,?,?,?,?)",
            (name, category_id, unit, price, stock),
        )

    def update_product(self, pid, name, category_id, unit, price, stock):
        self.execute(
            "UPDATE products SET name=?, category_id=?, unit=?, price=?, stock=? WHERE id=?",
            (name, category_id, unit, price, stock, pid),
        )

    def delete_product(self, pid: int):
        self.execute("DELETE FROM products WHERE id=?", (pid,))

    # ------------------------------------------------------------------
    # Clients
    # ------------------------------------------------------------------

    def get_clients(self):
        return self.fetchall("SELECT * FROM clients ORDER BY name")

    def add_client(self, name, phone, address) -> int:
        return self.execute(
            "INSERT INTO clients (name, phone, address) VALUES (?,?,?)",
            (name, phone, address),
        )

    def update_client(self, cid, name, phone, address):
        self.execute(
            "UPDATE clients SET name=?, phone=?, address=? WHERE id=?",
            (name, phone, address, cid),
        )

    def delete_client(self, cid: int):
        self.execute("DELETE FROM clients WHERE id=?", (cid,))

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def get_orders(self):
        sql = """
            SELECT o.id, c.name AS client, o.created_at, o.status, o.total
            FROM orders o
            LEFT JOIN clients c ON c.id = o.client_id
            ORDER BY o.id DESC
        """
        return self.fetchall(sql)

    def get_order(self, oid: int):
        return self.fetchone("SELECT * FROM orders WHERE id=?", (oid,))

    def add_order(self, client_id, status="Новый") -> int:
        return self.execute(
            "INSERT INTO orders (client_id, status) VALUES (?,?)",
            (client_id, status),
        )

    def update_order_status(self, oid: int, status: str):
        self.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))

    def delete_order(self, oid: int):
        self.execute("DELETE FROM orders WHERE id=?", (oid,))

    def get_order_items(self, oid: int):
        sql = """
            SELECT oi.id, p.name AS product, oi.qty, oi.price, oi.qty*oi.price AS subtotal
            FROM order_items oi
            LEFT JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
        """
        return self.fetchall(sql, (oid,))

    def add_order_item(self, order_id, product_id, qty, price) -> int:
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
            "SELECT COALESCE(SUM(qty*price),0) AS t FROM order_items WHERE order_id=?",
            (order_id,),
        )
        self.execute("UPDATE orders SET total=? WHERE id=?", (row["t"], order_id))

    def close(self):
        self.conn.close()
