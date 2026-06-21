from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QLabel
)
from PyQt6.QtCore import Qt
from dialogs import (
    ProductDialog, OrderDialog, ClientDialog,
    SupplierDialog, CategoryDialog, ViewOrderDialog
)


class BaseTab(QWidget):
    HEADERS = ["ID"]

    def __init__(self, db, title: str = ""):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        if title:
            layout.addWidget(QLabel(f"<b>{title}</b>"))
        btn_bar = QHBoxLayout()
        self.btn_add  = QPushButton("+ \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c")
        self.btn_edit = QPushButton("\u270e \u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c")
        self.btn_del  = QPushButton("- \u0423\u0434\u0430\u043b\u0438\u0442\u044c")
        for b in (self.btn_add, self.btn_edit, self.btn_del):
            btn_bar.addWidget(b)
        btn_bar.addStretch()
        layout.addLayout(btn_bar)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.btn_add.clicked.connect(self.on_add)
        self.btn_edit.clicked.connect(self.on_edit)
        self.btn_del.clicked.connect(self.on_delete)
        self.load()

    def _fill_table(self, headers, rows):
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(val if val is not None else "")))

    def selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def load(self):
        self._fill_table(self.HEADERS, [])

    def on_add(self): pass
    def on_edit(self): pass
    def on_delete(self): pass


# ----------------------------------------------------------------------
# ProductsTab
# ----------------------------------------------------------------------
class ProductsTab(BaseTab):
    HEADERS = ["ID", "\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435", "\u0410\u0440\u0442\u0438\u043a\u0443\u043b", "\u0426\u0435\u043d\u0430", "\u041e\u0441\u0442\u0430\u0442\u043e\u043a", "\u0417\u0430\u0440\u0435\u0437\u0435\u0440\u0432.", "\u0421\u0432\u043e\u0431\u043e\u0434\u043d\u043e", "\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f", "\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a"]

    def load(self):
        rows = self.db.fetchall(
            "SELECT p.id, p.name, p.sku, p.price, p.stock, "
            "COALESCE((SELECT SUM(oi.qty) FROM order_items oi WHERE oi.product_id=p.id),0) AS reserved, "
            "p.stock - COALESCE((SELECT SUM(oi.qty) FROM order_items oi WHERE oi.product_id=p.id),0) AS free_stock, "
            "COALESCE(c.name, '') AS cat, COALESCE(s.name, '') AS sup "
            "FROM products p "
            "LEFT JOIN categories c ON c.id = p.category_id "
            "LEFT JOIN suppliers s ON s.id = p.supplier_id "
            "ORDER BY p.name"
        )
        self._fill_table(self.HEADERS, rows)

    def on_add(self):
        dlg = ProductDialog(self.db)
        if dlg.exec():
            self.load()

    def on_edit(self):
        rid = self.selected_id()
        if rid is None:
            return
        row = self.db.fetchone("SELECT * FROM products WHERE id = ?", (rid,))
        if row:
            dlg = ProductDialog(self.db, row)
            if dlg.exec():
                self.load()

    def on_delete(self):
        rid = self.selected_id()
        if rid is None:
            return
        reserved = self.db.get_reserved_stock(rid)
        if reserved > 0:
            QMessageBox.warning(
                self, "\u041d\u0435\u043b\u044c\u0437\u044f \u0443\u0434\u0430\u043b\u0438\u0442\u044c",
                f"\u0422\u043e\u0432\u0430\u0440 #\u200b{rid} \u0437\u0430\u0440\u0435\u0437\u0435\u0440\u0432\u0438\u0440\u043e\u0432\u0430\u043d \u0432 {reserved} \u0448\u0442. \u0432 \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0445 \u0437\u0430\u043a\u0430\u0437\u0430\u0445.\n"
                f"\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0443\u0434\u0430\u043b\u0438\u0442\u0435 \u0438\u043b\u0438 \u0437\u0430\u0432\u0435\u0440\u0448\u0438\u0442\u0435 \u0441\u0432\u044f\u0437\u0430\u043d\u043d\u044b\u0435 \u0437\u0430\u043a\u0430\u0437\u044b."
            )
            return
        if QMessageBox.question(
            self, "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0442\u043e\u0432\u0430\u0440",
            f"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0442\u043e\u0432\u0430\u0440 #{rid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM products WHERE id = ?", (rid,))
            self.load()


# ----------------------------------------------------------------------
# OrdersTab
# ----------------------------------------------------------------------
class OrdersTab(QWidget):
    HEADERS = ["ID", "\u041a\u043b\u0438\u0435\u043d\u0442", "\u0414\u0430\u0442\u0430", "\u0421\u0442\u0430\u0442\u0443\u0441", "\u0421\u0443\u043c\u043c\u0430", "\u041f\u043e\u0437\u0438\u0446\u0438\u0439"]

    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        btn_bar = QHBoxLayout()
        self.btn_add  = QPushButton("+ \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c")
        self.btn_edit = QPushButton("\u270e \u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c")
        self.btn_del  = QPushButton("- \u0423\u0434\u0430\u043b\u0438\u0442\u044c")
        self.btn_view = QPushButton("\U0001f441 \u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440")
        for b in (self.btn_add, self.btn_edit, self.btn_del, self.btn_view):
            btn_bar.addWidget(b)
        btn_bar.addStretch()
        layout.addLayout(btn_bar)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.btn_add.clicked.connect(self.on_add)
        self.btn_edit.clicked.connect(self.on_edit)
        self.btn_del.clicked.connect(self.on_delete)
        self.btn_view.clicked.connect(self.on_view)
        self.table.doubleClicked.connect(self.on_view)
        self.load()

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def load(self):
        rows = self.db.fetchall(
            "SELECT o.id, COALESCE(c.name,'') AS client, "
            "o.date, o.status, o.total, "
            "(SELECT COUNT(*) FROM order_items oi WHERE oi.order_id=o.id) AS items "
            "FROM orders o "
            "LEFT JOIN clients c ON c.id = o.client_id "
            "ORDER BY o.date DESC, o.id DESC"
        )
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(val if val is not None else "")))

    def on_add(self):
        dlg = OrderDialog(self.db)
        if dlg.exec():
            self.load()

    def on_edit(self):
        rid = self._selected_id()
        if rid is None:
            return
        row = self.db.fetchone("SELECT * FROM orders WHERE id = ?", (rid,))
        if row:
            dlg = OrderDialog(self.db, row)
            if dlg.exec():
                self.load()

    def on_delete(self):
        rid = self._selected_id()
        if rid is None:
            return
        if QMessageBox.question(
            self, "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437",
            f"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437 #{rid}? \u041e\u0441\u0442\u0430\u0442\u043e\u043a \u0442\u043e\u0432\u0430\u0440\u043e\u0432 \u0431\u0443\u0434\u0435\u0442 \u0432\u043e\u0441\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.db.delete_order(rid)   # restores stock automatically
            self.load()

    def on_view(self):
        rid = self._selected_id()
        if rid is None:
            return
        dlg = ViewOrderDialog(self.db, rid, self)
        dlg.exec()


# ----------------------------------------------------------------------
# ClientsTab
# ----------------------------------------------------------------------
class ClientsTab(BaseTab):
    HEADERS = ["ID", "\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435", "\u041a\u043e\u043d\u0442\u0430\u043a\u0442", "\u0422\u0435\u043b\u0435\u0444\u043e\u043d", "\u0410\u0434\u0440\u0435\u0441"]

    def load(self):
        rows = self.db.fetchall("SELECT id, name, contact, phone, address FROM clients ORDER BY name")
        self._fill_table(self.HEADERS, rows)

    def on_add(self):
        dlg = ClientDialog(self.db)
        if dlg.exec(): self.load()

    def on_edit(self):
        rid = self.selected_id()
        if rid is None: return
        row = self.db.fetchone("SELECT * FROM clients WHERE id = ?", (rid,))
        if row:
            dlg = ClientDialog(self.db, row)
            if dlg.exec(): self.load()

    def on_delete(self):
        rid = self.selected_id()
        if rid is None: return
        if QMessageBox.question(
            self, "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043a\u043b\u0438\u0435\u043d\u0442\u0430",
            f"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043a\u043b\u0438\u0435\u043d\u0442\u0430 #{rid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM clients WHERE id = ?", (rid,))
            self.load()


# ----------------------------------------------------------------------
# SuppliersTab
# ----------------------------------------------------------------------
class SuppliersTab(BaseTab):
    HEADERS = ["ID", "\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435", "\u041a\u043e\u043d\u0442\u0430\u043a\u0442", "\u0422\u0435\u043b\u0435\u0444\u043e\u043d", "\u0410\u0434\u0440\u0435\u0441"]

    def load(self):
        rows = self.db.fetchall("SELECT id, name, contact, phone, address FROM suppliers ORDER BY name")
        self._fill_table(self.HEADERS, rows)

    def on_add(self):
        dlg = SupplierDialog(self.db)
        if dlg.exec(): self.load()

    def on_edit(self):
        rid = self.selected_id()
        if rid is None: return
        row = self.db.fetchone("SELECT * FROM suppliers WHERE id = ?", (rid,))
        if row:
            dlg = SupplierDialog(self.db, row)
            if dlg.exec(): self.load()

    def on_delete(self):
        rid = self.selected_id()
        if rid is None: return
        if QMessageBox.question(
            self, "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0430",
            f"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0430 #{rid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM suppliers WHERE id = ?", (rid,))
            self.load()


# ----------------------------------------------------------------------
# CategoriesTab
# ----------------------------------------------------------------------
class CategoriesTab(BaseTab):
    HEADERS = ["ID", "\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435"]

    def load(self):
        rows = self.db.fetchall("SELECT id, name FROM categories ORDER BY name")
        self._fill_table(self.HEADERS, rows)

    def on_add(self):
        dlg = CategoryDialog(self.db)
        if dlg.exec(): self.load()

    def on_edit(self):
        rid = self.selected_id()
        if rid is None: return
        row = self.db.fetchone("SELECT * FROM categories WHERE id = ?", (rid,))
        if row:
            dlg = CategoryDialog(self.db, row)
            if dlg.exec(): self.load()

    def on_delete(self):
        rid = self.selected_id()
        if rid is None: return
        if QMessageBox.question(
            self, "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044e",
            f"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044e #{rid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM categories WHERE id = ?", (rid,))
            self.load()
