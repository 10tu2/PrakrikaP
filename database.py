import sqlite3
import hashlib
import os

DB_FILE = "trade_store.db"

ACTIVE_STATUSES = ('новый', 'в обработке')
COMPLETED_STATUS = 'выполнен'
CANCELLED_STATUS = 'отменён'

ROLE_ADMIN    = 'admin'
ROLE_EMPLOYEE = 'employee'


def _hash_password(password: str, salt: str = None):
    """SHA-256 + соль. Возвращает (hash_hex, salt_hex)."""
    if salt is None:
        salt = os.urandom(16).hex()
    h = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return h, salt


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
        self._ensure_default_admin()

    def _create_tables(self):
        stmts = [
            """CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )""",
            """CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                phone TEXT,
                address TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                phone TEXT,
                address TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT,
                price REAL DEFAULT 0,
                stock INTEGER DEFAULT 0,
                category_id INTEGER,
                supplier_id INTEGER
            )""",
            """CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                date TEXT,
                status TEXT DEFAULT 'новый',
                total REAL DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_id INTEGER,
                qty INTEGER DEFAULT 1,
                price REAL DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL DEFAULT '',
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'employee'
            )""",
        ]
        for stmt in stmts:
            self.conn.execute(stmt)
        self.conn.commit()

    def _migrate(self):
        def has_column(table: str, col: str) -> bool:
            row = self.conn.execute(
                "SELECT 1 FROM pragma_table_info(?) WHERE name=?",
                (table, col)
            ).fetchone()
            return row is not None

        def has_table(table: str) -> bool:
            row = self.conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            ).fetchone()
            return row is not None

        def add_col(table: str, col: str, sql: str):
            if has_table(table) and not has_column(table, col):
                try:
                    self.conn.execute(sql)
                    self.conn.commit()
                except sqlite3.OperationalError:
                    pass

        add_col("products", "sku",         "ALTER TABLE products ADD COLUMN sku TEXT")
        add_col("products", "price",        "ALTER TABLE products ADD COLUMN price REAL DEFAULT 0")
        add_col("products", "stock",        "ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 0")
        add_col("products", "category_id",  "ALTER TABLE products ADD COLUMN category_id INTEGER")
        add_col("products", "supplier_id",  "ALTER TABLE products ADD COLUMN supplier_id INTEGER")
        add_col("orders", "client_id", "ALTER TABLE orders ADD COLUMN client_id INTEGER")
        add_col("orders", "date",      "ALTER TABLE orders ADD COLUMN date TEXT")
        add_col("orders", "status",    "ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'новый'")
        add_col("orders", "total",     "ALTER TABLE orders ADD COLUMN total REAL DEFAULT 0")
        add_col("order_items", "order_id",   "ALTER TABLE order_items ADD COLUMN order_id INTEGER")
        add_col("order_items", "product_id", "ALTER TABLE order_items ADD COLUMN product_id INTEGER")
        add_col("order_items", "qty",        "ALTER TABLE order_items ADD COLUMN qty INTEGER DEFAULT 1")
        add_col("order_items", "price",      "ALTER TABLE order_items ADD COLUMN price REAL DEFAULT 0")
        add_col("clients", "contact", "ALTER TABLE clients ADD COLUMN contact TEXT")
        add_col("clients", "phone",   "ALTER TABLE clients ADD COLUMN phone TEXT")
        add_col("clients", "address", "ALTER TABLE clients ADD COLUMN address TEXT")
        add_col("suppliers", "contact", "ALTER TABLE suppliers ADD COLUMN contact TEXT")
        add_col("suppliers", "phone",   "ALTER TABLE suppliers ADD COLUMN phone TEXT")
        add_col("suppliers", "address", "ALTER TABLE suppliers ADD COLUMN address TEXT")
        add_col("users", "full_name", "ALTER TABLE users ADD COLUMN full_name TEXT NOT NULL DEFAULT ''")

    def _ensure_default_admin(self):
        """Создаёт учётную запись admin/admin если пользователей нет."""
        count = self.fetchone("SELECT COUNT(*) AS c FROM users")["c"]
        if count == 0:
            h, s = _hash_password("admin")
            self.execute(
                "INSERT INTO users(username, full_name, password_hash, salt, role) VALUES(?,?,?,?,?)",
                ("admin", "Администратор", h, s, ROLE_ADMIN),
            )

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    def authenticate(self, username: str, password: str):
        """Возвращает sqlite3.Row пользователя или None."""
        row = self.fetchone("SELECT * FROM users WHERE username=?", (username,))
        if row is None:
            return None
        h, _ = _hash_password(password, row["salt"])
        return row if h == row["password_hash"] else None

    def create_user(self, username: str, full_name: str, password: str, role: str):
        h, s = _hash_password(password)
        self.execute(
            "INSERT INTO users(username, full_name, password_hash, salt, role) VALUES(?,?,?,?,?)",
            (username, full_name, h, s, role),
        )

    def update_user(self, uid: int, full_name: str, role: str):
        self.execute(
            "UPDATE users SET full_name=?, role=? WHERE id=?",
            (full_name, role, uid),
        )

    def change_password(self, uid: int, new_password: str):
        h, s = _hash_password(new_password)
        self.execute(
            "UPDATE users SET password_hash=?, salt=? WHERE id=?",
            (h, s, uid),
        )

    def delete_user(self, uid: int):
        self.execute("DELETE FROM users WHERE id=?", (uid,))

    def get_users(self):
        return self.fetchall("SELECT id, username, full_name, role FROM users ORDER BY username")

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------
    def execute(self, sql: str, params: tuple = ()) -> int:
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur.lastrowid

    def fetchone(self, sql: str, params: tuple = ()):
        return self.conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: tuple = ()):
        return self.conn.execute(sql, params).fetchall()

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------
    def update_order_status(self, oid: int, new_status: str):
        old_row = self.fetchone("SELECT status FROM orders WHERE id=?", (oid,))
        if old_row is None:
            return
        old_status = old_row["status"]
        if old_status == new_status:
            return
        items = self.fetchall(
            "SELECT product_id, qty FROM order_items WHERE order_id=?", (oid,)
        )
        was_active    = old_status in ACTIVE_STATUSES
        was_completed = old_status == COMPLETED_STATUS
        was_cancelled = old_status == CANCELLED_STATUS
        is_active     = new_status in ACTIVE_STATUSES
        is_cancelled  = new_status == CANCELLED_STATUS

        for it in items:
            pid, qty = it["product_id"], it["qty"]
            if pid is None:
                continue
            if was_active and is_cancelled:
                self.execute("UPDATE products SET stock = stock + ? WHERE id=?", (qty, pid))
            elif was_active and new_status == COMPLETED_STATUS:
                pass
            elif (was_cancelled or was_completed) and is_active:
                stock = self.get_product_stock(pid)
                if qty > stock:
                    raise ValueError(
                        f"Недостаточно товара (id={pid}) для возобновления заказа. "
                        f"Доступно: {stock}, требуется: {qty}."
                    )
                self.execute("UPDATE products SET stock = stock - ? WHERE id=?", (qty, pid))
            elif was_completed and is_cancelled:
                self.execute("UPDATE products SET stock = stock + ? WHERE id=?", (qty, pid))
        self.execute("UPDATE orders SET status=? WHERE id=?", (new_status, oid))

    def delete_order(self, oid: int):
        order = self.fetchone("SELECT status FROM orders WHERE id=?", (oid,))
        if order is None:
            return
        items = self.fetchall(
            "SELECT product_id, qty FROM order_items WHERE order_id=?", (oid,)
        )
        if order["status"] in ACTIVE_STATUSES:
            for it in items:
                if it["product_id"] is not None:
                    self.execute(
                        "UPDATE products SET stock = stock + ? WHERE id=?",
                        (it["qty"], it["product_id"]),
                    )
        self.execute("DELETE FROM order_items WHERE order_id=?", (oid,))
        self.execute("DELETE FROM orders WHERE id=?", (oid,))

    def get_order_items(self, oid: int):
        return self.fetchall("""
            SELECT oi.id, oi.product_id,
                   COALESCE(p.name,'') AS product,
                   oi.qty, oi.price,
                   oi.qty * oi.price AS subtotal
            FROM order_items oi
            LEFT JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
        """, (oid,))

    def get_product_stock(self, product_id: int) -> int:
        row = self.fetchone(
            "SELECT COALESCE(stock, 0) AS stock FROM products WHERE id=?",
            (product_id,)
        )
        return int(row["stock"]) if row else 0

    def get_reserved_stock(self, product_id: int, exclude_order_id: int = None) -> int:
        ph = ','.join(f"'{s}'" for s in ACTIVE_STATUSES)
        if exclude_order_id is not None:
            row = self.fetchone(
                f"SELECT COALESCE(SUM(oi.qty),0) AS res "
                f"FROM order_items oi JOIN orders o ON o.id=oi.order_id "
                f"WHERE oi.product_id=? AND oi.order_id!=? AND o.status IN ({ph})",
                (product_id, exclude_order_id),
            )
        else:
            row = self.fetchone(
                f"SELECT COALESCE(SUM(oi.qty),0) AS res "
                f"FROM order_items oi JOIN orders o ON o.id=oi.order_id "
                f"WHERE oi.product_id=? AND o.status IN ({ph})",
                (product_id,),
            )
        return int(row["res"]) if row else 0

    def add_order_item(self, order_id: int, product_id: int, qty: int, price: float) -> int:
        stock = self.get_product_stock(product_id)
        if qty > stock:
            raise ValueError(f"Недостаточно товара на складе. Доступно: {stock}.")
        row_id = self.execute(
            "INSERT INTO order_items(order_id, product_id, qty, price) VALUES(?,?,?,?)",
            (order_id, product_id, qty, price),
        )
        self.execute("UPDATE products SET stock = stock - ? WHERE id=?", (qty, product_id))
        self._recalc_order(order_id)
        return row_id

    def delete_order_item(self, item_id: int, order_id: int):
        order = self.fetchone("SELECT status FROM orders WHERE id=?", (order_id,))
        item  = self.fetchone("SELECT product_id, qty FROM order_items WHERE id=?", (item_id,))
        if item and item["product_id"] is not None:
            if order and order["status"] in ACTIVE_STATUSES:
                self.execute(
                    "UPDATE products SET stock = stock + ? WHERE id=?",
                    (item["qty"], item["product_id"]),
                )
        self.execute("DELETE FROM order_items WHERE id=?", (item_id,))
        self._recalc_order(order_id)

    def _recalc_order(self, order_id: int):
        row = self.fetchone(
            "SELECT COALESCE(SUM(qty * price), 0) AS total FROM order_items WHERE order_id=?",
            (order_id,),
        )
        self.execute("UPDATE orders SET total=? WHERE id=?", (row["total"], order_id))

    def close(self):
        self.conn.close()
