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


# ----------------------------------------------------------------------
# BaseTab
# ----------------------------------------------------------------------

class BaseTab(QWidget):
    """Base tab widget with a table and Add / Edit / Delete buttons."""

    HEADERS = ["ID"]

    def __init__(self, db, title: str = ""):
        super().__init__()
        self.db = db

        layout = QVBoxLayout(self)

        if title:
            layout.addWidget(QLabel(f"<b>{title}</b>"))

        btn_bar = QHBoxLayout()
        self.btn_add = QPushButton("+ Добавить")
        self.btn_edit = QPushButton("✎ Изменить")
        self.btn_del = QPushButton("- Удалить")
        for b in (self.btn_add, self.btn_edit, self.btn_del):
            btn_bar.addWidget(b)
        btn_bar.addStretch()
        layout.addLayout(btn_bar)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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

    def selected_row(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).text()

    def load(self):
        self._fill_table(self.HEADERS, [])

    def on_add(self):
        pass

    def on_edit(self):
        pass

    def on_delete(self):
        pass


# ----------------------------------------------------------------------
# ProductsTab
# ----------------------------------------------------------------------

class ProductsTab(BaseTab):
    HEADERS = ["ID", "Название", "Артикул", "Цена", "Остаток", "Категория", "Поставщик"]

    def load(self):
        rows = self.db.fetchall(
            "SELECT p.id, p.name, p.sku, p.price, p.stock, "
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
        if QMessageBox.question(
            self, "Удалить товар",
            f"Удалить товар #{rid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM products WHERE id = ?", (rid,))
            self.load()


# ----------------------------------------------------------------------
# OrdersTab
# ----------------------------------------------------------------------

class OrdersTab(QWidget):
    """Orders tab with Add / Edit / Delete / View buttons."""

    HEADERS = ["ID", "Клиент", "Дата", "Статус", "Сумма", "Позиций"]

    def __init__(self, db):
        super().__init__()
        self.db = db

        layout = QVBoxLayout(self)

        btn_bar = QHBoxLayout()
        self.btn_add  = QPushButton("+ Добавить")
        self.btn_edit = QPushButton("✎ Изменить")
        self.btn_del  = QPushButton("- Удалить")
        self.btn_view = QPushButton("👁 Просмотр")
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
            self, "Удалить заказ",
            f"Удалить заказ #{rid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM order_items WHERE order_id = ?", (rid,))
            self.db.execute("DELETE FROM orders WHERE id = ?", (rid,))
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
    HEADERS = ["ID", "Название", "Контакт", "Телефон", "Адрес"]

    def load(self):
        rows = self.db.fetchall(
            "SELECT id, name, contact, phone, address "
            "FROM clients ORDER BY name"
        )
        self._fill_table(self.HEADERS, rows)

    def on_add(self):
        dlg = ClientDialog(self.db)
        if dlg.exec():
            self.load()

    def on_edit(self):
        rid = self.selected_id()
        if rid is None:
            return
        row = self.db.fetchone("SELECT * FROM clients WHERE id = ?", (rid,))
        if row:
            dlg = ClientDialog(self.db, row)
            if dlg.exec():
                self.load()

    def on_delete(self):
        rid = self.selected_id()
        if rid is None:
            return
        if QMessageBox.question(
            self, "Удалить клиента",
            f"Удалить клиента #{rid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM clients WHERE id = ?", (rid,))
            self.load()


# ----------------------------------------------------------------------
# SuppliersTab
# ----------------------------------------------------------------------

class SuppliersTab(BaseTab):
    HEADERS = ["ID", "Название", "Контакт", "Телефон", "Адрес"]

    def load(self):
        rows = self.db.fetchall(
            "SELECT id, name, contact, phone, address "
            "FROM suppliers ORDER BY name"
        )
        self._fill_table(self.HEADERS, rows)

    def on_add(self):
        dlg = SupplierDialog(self.db)
        if dlg.exec():
            self.load()

    def on_edit(self):
        rid = self.selected_id()
        if rid is None:
            return
        row = self.db.fetchone("SELECT * FROM suppliers WHERE id = ?", (rid,))
        if row:
            dlg = SupplierDialog(self.db, row)
            if dlg.exec():
                self.load()

    def on_delete(self):
        rid = self.selected_id()
        if rid is None:
            return
        if QMessageBox.question(
            self, "Удалить поставщика",
            f"Удалить поставщика #{rid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM suppliers WHERE id = ?", (rid,))
            self.load()


# ----------------------------------------------------------------------
# CategoriesTab
# ----------------------------------------------------------------------

class CategoriesTab(BaseTab):
    HEADERS = ["ID", "Название"]

    def load(self):
        rows = self.db.fetchall(
            "SELECT id, name FROM categories ORDER BY name"
        )
        self._fill_table(self.HEADERS, rows)

    def on_add(self):
        dlg = CategoryDialog(self.db)
        if dlg.exec():
            self.load()

    def on_edit(self):
        rid = self.selected_id()
        if rid is None:
            return
        row = self.db.fetchone("SELECT * FROM categories WHERE id = ?", (rid,))
        if row:
            dlg = CategoryDialog(self.db, row)
            if dlg.exec():
                self.load()

    def on_delete(self):
        rid = self.selected_id()
        if rid is None:
            return
        if QMessageBox.question(
            self, "Удалить категорию",
            f"Удалить категорию #{rid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM categories WHERE id = ?", (rid,))
            self.load()
