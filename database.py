import sqlite3

DB_FILE = "trade_store.db"

# Статусы, при которых товар считается «зарезервированным» (ещё не списан окончательно)
ACTIVE_STATUSES = ('новый', 'в обработке')
# Статусы, при которых товар уже отгружен (позиции остаются в order_items для истории)
COMPLETED_STATUS = 'выполнен'
CANCELLED_STATUS = 'отменён'


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

        def add_col(table: str, col: str, sql: str):
            if not has_column(table, col):
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

    def execute(self, sql: str, params: tuple = ()) -> int:
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur.lastrowid

    def fetchone(self, sql: str, params: tuple = ()):
        return self.conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: tuple = ()):
        return self.conn.execute(sql, params).fetchall()

    # ------------------------------------------------------------------
    # Смена статуса заказа с корректировкой остатков
    # ------------------------------------------------------------------
    def update_order_status(self, oid: int, new_status: str):
        """
        Меняет статус заказа и корректирует stock:
        - новый/в обработке  → без изменений (товар уже списан при добавлении позиций)
        - выполнен           → товар уже списан, ничего не возвращаем; просто фиксируем статус
        - отменён            → возвращаем кол-во в stock (если заказ был активным)
        При переходе обратно из выполнен/отменён в активный — снова резервируем.
        """
        old_row = self.fetchone("SELECT status FROM orders WHERE id=?", (oid,))
        if old_row is None:
            return
        old_status = old_row["status"]

        if old_status == new_status:
            return

        items = self.fetchall(
            "SELECT product_id, qty FROM order_items WHERE order_id=?", (oid,)
        )

        was_active = old_status in ACTIVE_STATUSES
        was_completed = old_status == COMPLETED_STATUS
        was_cancelled = old_status == CANCELLED_STATUS

        is_active = new_status in ACTIVE_STATUSES
        is_completed = new_status == COMPLETED_STATUS
        is_cancelled = new_status == CANCELLED_STATUS

        for it in items:
            pid, qty = it["product_id"], it["qty"]
            if pid is None:
                continue

            if was_active and is_cancelled:
                # Возвращаем товар — заказ отменён
                self.execute("UPDATE products SET stock = stock + ? WHERE id=?", (qty, pid))

            elif was_active and is_completed:
                # Товар уже списан из stock при создании позиции — ничего не делаем
                pass

            elif (was_cancelled or was_completed) and is_active:
                # Возобновляем активный заказ — резервируем снова
                stock = self.get_product_stock(pid)
                if qty > stock:
                    raise ValueError(
                        f"Недостаточно товара (id={pid}) для возобновления заказа. "
                        f"Доступно: {stock}, требуется: {qty}."
                    )
                self.execute("UPDATE products SET stock = stock - ? WHERE id=?", (qty, pid))

            elif was_cancelled and is_completed:
                # Из отменённого сразу в выполнен — резервируем и тут же «отгружаем» (net=0)
                pass

            elif was_completed and is_cancelled:
                # Отменяем уже выполненный: возвращаем товар
                self.execute("UPDATE products SET stock = stock + ? WHERE id=?", (qty, pid))

        self.execute("UPDATE orders SET status=? WHERE id=?", (new_status, oid))

    def delete_order(self, oid: int):
        """Delete order and restore product stock only if order was active."""
        order = self.fetchone("SELECT status FROM orders WHERE id=?", (oid,))
        if order is None:
            return
        status = order["status"]
        items = self.fetchall(
            "SELECT product_id, qty FROM order_items WHERE order_id=?", (oid,)
        )
        # Возвращаем сток только если заказ был активным (товар был заблокирован)
        if status in ACTIVE_STATUSES:
            for it in items:
                if it["product_id"] is not None:
                    self.execute(
                        "UPDATE products SET stock = stock + ? WHERE id=?",
                        (it["qty"], it["product_id"]),
                    )
        self.execute("DELETE FROM order_items WHERE order_id=?", (oid,))
        self.execute("DELETE FROM orders WHERE id=?", (oid,))

    def get_order_items(self, oid: int):
        sql = """
            SELECT oi.id,
                   oi.product_id,
                   COALESCE(p.name, '') AS product,
                   oi.qty,
                   oi.price,
                   oi.qty * oi.price AS subtotal
            FROM order_items oi
            LEFT JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
        """
        return self.fetchall(sql, (oid,))

    def get_product_stock(self, product_id: int) -> int:
        row = self.fetchone(
            "SELECT COALESCE(stock, 0) AS stock FROM products WHERE id=?",
            (product_id,)
        )
        return int(row["stock"]) if row else 0

    def get_reserved_stock(self, product_id: int, exclude_order_id: int = None) -> int:
        """
        Зарезервировано = кол-во в позициях АКТИВНЫХ заказов.
        Выполненные/отменённые не считаются — товар уже либо списан, либо возвращён.
        """
        placeholders = ','.join(f"'{s}'" for s in ACTIVE_STATUSES)
        if exclude_order_id is not None:
            row = self.fetchone(
                f"SELECT COALESCE(SUM(oi.qty), 0) AS res "
                f"FROM order_items oi "
                f"JOIN orders o ON o.id = oi.order_id "
                f"WHERE oi.product_id=? AND oi.order_id != ? AND o.status IN ({placeholders})",
                (product_id, exclude_order_id),
            )
        else:
            row = self.fetchone(
                f"SELECT COALESCE(SUM(oi.qty), 0) AS res "
                f"FROM order_items oi "
                f"JOIN orders o ON o.id = oi.order_id "
                f"WHERE oi.product_id=? AND o.status IN ({placeholders})",
                (product_id,),
            )
        return int(row["res"]) if row else 0

    def add_order_item(self, order_id: int, product_id: int, qty: int, price: float) -> int:
        stock = self.get_product_stock(product_id)
        if qty > stock:
            raise ValueError(f"Недостаточно товара на складе. Доступно: {stock}.")
        row_id = self.execute(
            "INSERT INTO order_items (order_id, product_id, qty, price) VALUES (?,?,?,?)",
            (order_id, product_id, qty, price),
        )
        self.execute("UPDATE products SET stock = stock - ? WHERE id=?", (qty, product_id))
        self._recalc_order(order_id)
        return row_id

    def delete_order_item(self, item_id: int, order_id: int):
        """Удаляет позицию заказа. Возвращает stock только если заказ активный."""
        order = self.fetchone("SELECT status FROM orders WHERE id=?", (order_id,))
        item = self.fetchone("SELECT product_id, qty FROM order_items WHERE id=?", (item_id,))
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
