import mysql.connector
from mysql.connector import Error

# ---------------------------------------------------------
# Fill in your MySQL connection details here
# or pass them via environment variables / config file.
# ---------------------------------------------------------
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",       # <-- your MySQL user
    "password": "",           # <-- your MySQL password
    "database": "prakriap",   # <-- your database name
    "charset":  "utf8mb4",
    "use_unicode": True,
    "autocommit": False,
}


class _Row(dict):
    """Dict subclass that also supports attribute-style access (row["key"] and row.key)."""
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(item)


class Database:
    """MySQL layer for wholesale hardware & plumbing trade app."""

    def __init__(self, config: dict = None):
        cfg = config or DB_CONFIG
        self.conn = mysql.connector.connect(**cfg)
        self.conn.autocommit = False

    # ------------------------------------------------------------------ internal
    def _cursor(self):
        """Return a fresh cursor; reconnect if the connection dropped."""
        if not self.conn.is_connected():
            self.conn.reconnect(attempts=3, delay=1)
        return self.conn.cursor(dictionary=True)

    def _to_rows(self, raw):
        """Convert list of dicts returned by mysql-connector into _Row objects."""
        return [_Row(r) for r in raw]

    # ------------------------------------------------------------------ public API
    def execute(self, sql: str, params: tuple = ()) -> int:
        """Execute a DML statement, commit and return lastrowid."""
        # MySQL uses %s placeholders, not ?
        sql = sql.replace("?", "%s")
        cur = self._cursor()
        cur.execute(sql, params)
        self.conn.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id

    def fetchone(self, sql: str, params: tuple = ()):
        """Return a single _Row or None."""
        sql = sql.replace("?", "%s")
        cur = self._cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return _Row(row) if row else None

    def fetchall(self, sql: str, params: tuple = ()):
        """Return a list of _Row objects."""
        sql = sql.replace("?", "%s")
        cur = self._cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return self._to_rows(rows)

    # ------------------------------------------------------------------ business logic
    def update_order_status(self, oid: int, status: str):
        self.execute("UPDATE orders SET status=%s WHERE id=%s", (status, oid))

    def delete_order(self, oid: int):
        self.execute("DELETE FROM orders WHERE id=%s", (oid,))

    def get_order_items(self, oid: int):
        sql = """
            SELECT oi.id,
                   COALESCE(p.name, '') AS product,
                   oi.qty,
                   oi.price,
                   oi.qty * oi.price AS subtotal
            FROM order_items oi
            LEFT JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = %s
        """
        return self.fetchall(sql, (oid,))

    def add_order_item(self, order_id: int, product_id: int, qty: int, price: float) -> int:
        row_id = self.execute(
            "INSERT INTO order_items (order_id, product_id, qty, price) VALUES (%s, %s, %s, %s)",
            (order_id, product_id, qty, price),
        )
        self._recalc_order(order_id)
        return row_id

    def delete_order_item(self, item_id: int, order_id: int):
        self.execute("DELETE FROM order_items WHERE id=%s", (item_id,))
        self._recalc_order(order_id)

    def _recalc_order(self, order_id: int):
        row = self.fetchone(
            "SELECT COALESCE(SUM(qty * price), 0) AS total FROM order_items WHERE order_id=%s",
            (order_id,),
        )
        self.execute(
            "UPDATE orders SET total=%s WHERE id=%s",
            (float(row["total"]), order_id),
        )

    def close(self):
        if self.conn.is_connected():
            self.conn.close()
