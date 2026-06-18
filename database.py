import sqlite3


class Database:
  """SQLite layer for wholesale hardware trade app."""

  def __init__(self, path: str = "trade_store.db"):
    self.path = path
    self.conn = sqlite3.connect(self.path)
    self.conn.row_factory = sqlite3.Row
    self.conn.execute("PRAGMA foreign_keys = ON")
    self._create_tables()

  def _create_tables(self):
    sql = """
      CREATE TABLE IF NOT EXISTS categories (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name  TEXT    NOT NULL UNIQUE
      );

      CREATE TABLE IF NOT EXISTS suppliers (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        name    TEXT NOT NULL,
        contact TEXT,
        phone   TEXT,
        address TEXT
      );

      CREATE TABLE IF NOT EXISTS clients (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        name    TEXT NOT NULL,
        contact TEXT,
        phone   TEXT,
        address TEXT
      );

      CREATE TABLE IF NOT EXISTS products (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL,
        sku         TEXT,
        price       REAL    NOT NULL DEFAULT 0,
        stock       INTEGER NOT NULL DEFAULT 0,
        category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
        supplier_id INTEGER REFERENCES suppliers(id)  ON DELETE SET NULL
      );

      CREATE TABLE IF NOT EXISTS orders (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER REFERENCES clients(id) ON DELETE SET NULL,
        date      TEXT    NOT NULL DEFAULT (date('now')),
        status    TEXT    NOT NULL DEFAULT 'новый',
        total     REAL    NOT NULL DEFAULT 0
      );

      CREATE TABLE IF NOT EXISTS order_items (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id   INTEGER NOT NULL REFERENCES orders(id)   ON DELETE CASCADE,
        product_id INTEGER          REFERENCES products(id) ON DELETE SET NULL,
        qty        INTEGER NOT NULL DEFAULT 1,
        price      REAL    NOT NULL DEFAULT 0
      );
    """
    self.conn.executescript(sql)
    self.conn.commit()

  # ------------------------------------------------------------------
  # Generic helpers
  # ------------------------------------------------------------------

  def execute(self, sql: str, params: tuple = ()) -> int:
    """Execute a write query; return lastrowid."""
    cur = self.conn.execute(sql, params)
    self.conn.commit()
    return cur.lastrowid

  def fetchone(self, sql: str, params: tuple = ()):
    cur = self.conn.execute(sql, params)
    return cur.fetchone()

  def fetchall(self, sql: str, params: tuple = ()):
    cur = self.conn.execute(sql, params)
    return cur.fetchall()

  # ------------------------------------------------------------------
  # Order helpers
  # ------------------------------------------------------------------

  def update_order_status(self, oid: int, status: str):
    self.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))

  def delete_order(self, oid: int):
    self.execute("DELETE FROM orders WHERE id=?", (oid,))

  def get_order_items(self, oid: int):
    sql = """
      SELECT oi.id, p.name AS product, oi.qty, oi.price,
             oi.qty * oi.price AS subtotal
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
