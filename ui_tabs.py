from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QLabel
)
from dialogs import (
    ProductDialog, OrderDialog, ClientDialog,
    SupplierDialog, CategoryDialog, ViewOrderDialog, UserDialog
)
from database import ACTIVE_STATUSES, ROLE_ADMIN


class BaseTab(QWidget):
    HEADERS = ["ID"]

    def __init__(self, db, title: str = ""):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        if title:
            layout.addWidget(QLabel(f"<b>{title}</b>"))
        btn_bar = QHBoxLayout()
        self.btn_add  = QPushButton("+ Добавить")
        self.btn_edit = QPushButton("✎ Изменить")
        self.btn_del  = QPushButton("- Удалить")
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
    HEADERS = ["ID", "Название", "Артикул", "Цена", "Остаток (физ.)",
               "Зарезерв. (акт.)", "Категория", "Поставщик"]

    def load(self):
        active_ph = ','.join(f"'{s}'" for s in ACTIVE_STATUSES)
        rows = self.db.fetchall(
            f"SELECT p.id, p.name, p.sku, p.price, p.stock, "
            f"COALESCE((SELECT SUM(oi.qty) FROM order_items oi "
            f"          JOIN orders o ON o.id=oi.order_id "
            f"          WHERE oi.product_id=p.id AND o.status IN ({active_ph})),0) AS reserved, "
            f"COALESCE(c.name,'') AS cat, COALESCE(s.name,'') AS sup "
            f"FROM products p "
            f"LEFT JOIN categories c ON c.id=p.category_id "
            f"LEFT JOIN suppliers s ON s.id=p.supplier_id "
            f"ORDER BY p.name"
        )
        self._fill_table(self.HEADERS, rows)

    def on_add(self):
        if ProductDialog(self.db).exec():
            self.load()

    def on_edit(self):
        rid = self.selected_id()
        if rid is None:
            return
        row = self.db.fetchone("SELECT * FROM products WHERE id=?", (rid,))
        if row and ProductDialog(self.db, row).exec():
            self.load()

    def on_delete(self):
        rid = self.selected_id()
        if rid is None:
            return
        reserved = self.db.get_reserved_stock(rid)
        if reserved > 0:
            QMessageBox.warning(self, "Нельзя удалить",
                f"Товар #{rid} зарезервирован ({reserved} шт.) в активных заказах.")
            return
        if QMessageBox.question(self, "Удалить товар", f"Удалить товар #{rid}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM products WHERE id=?", (rid,))
            self.load()


# ----------------------------------------------------------------------
# OrdersTab
# ----------------------------------------------------------------------
class OrdersTab(QWidget):
    HEADERS = ["ID", "Клиент", "Дата", "Статус", "Сумма", "Позиций"]

    def __init__(self, db, on_products_changed=None):
        super().__init__()
        self.db = db
        self._on_products_changed = on_products_changed or (lambda: None)
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
            "FROM orders o LEFT JOIN clients c ON c.id=o.client_id "
            "ORDER BY o.date DESC, o.id DESC"
        )
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(val if val is not None else "")))

    def _refresh_all(self):
        self.load()
        self._on_products_changed()

    def on_add(self):
        if OrderDialog(self.db).exec():
            self._refresh_all()

    def on_edit(self):
        rid = self._selected_id()
        if rid is None:
            return
        row = self.db.fetchone("SELECT * FROM orders WHERE id=?", (rid,))
        if row and OrderDialog(self.db, row).exec():
            self._refresh_all()

    def on_delete(self):
        rid = self._selected_id()
        if rid is None:
            return
        if QMessageBox.question(self, "Удалить заказ",
                f"Удалить заказ #{rid}? Остаток товаров будет восстановлен (если заказ активный).",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.db.delete_order(rid)
            self._refresh_all()

    def on_view(self):
        rid = self._selected_id()
        if rid is None:
            return
        ViewOrderDialog(self.db, rid, self).exec()


# ----------------------------------------------------------------------
# ClientsTab
# ----------------------------------------------------------------------
class ClientsTab(BaseTab):
    HEADERS = ["ID", "Название", "Контакт", "Телефон", "Адрес"]

    def load(self):
        rows = self.db.fetchall("SELECT id, name, contact, phone, address FROM clients ORDER BY name")
        self._fill_table(self.HEADERS, rows)

    def on_add(self):
        if ClientDialog(self.db).exec(): self.load()

    def on_edit(self):
        rid = self.selected_id()
        if rid is None: return
        row = self.db.fetchone("SELECT * FROM clients WHERE id=?", (rid,))
        if row and ClientDialog(self.db, row).exec(): self.load()

    def on_delete(self):
        rid = self.selected_id()
        if rid is None: return
        if QMessageBox.question(self, "Удалить клиента", f"Удалить клиента #{rid}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM clients WHERE id=?", (rid,))
            self.load()


# ----------------------------------------------------------------------
# SuppliersTab
# ----------------------------------------------------------------------
class SuppliersTab(BaseTab):
    HEADERS = ["ID", "Название", "Контакт", "Телефон", "Адрес"]

    def load(self):
        rows = self.db.fetchall("SELECT id, name, contact, phone, address FROM suppliers ORDER BY name")
        self._fill_table(self.HEADERS, rows)

    def on_add(self):
        if SupplierDialog(self.db).exec(): self.load()

    def on_edit(self):
        rid = self.selected_id()
        if rid is None: return
        row = self.db.fetchone("SELECT * FROM suppliers WHERE id=?", (rid,))
        if row and SupplierDialog(self.db, row).exec(): self.load()

    def on_delete(self):
        rid = self.selected_id()
        if rid is None: return
        if QMessageBox.question(self, "Удалить поставщика", f"Удалить поставщика #{rid}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM suppliers WHERE id=?", (rid,))
            self.load()


# ----------------------------------------------------------------------
# CategoriesTab
# ----------------------------------------------------------------------
class CategoriesTab(BaseTab):
    HEADERS = ["ID", "Название"]

    def load(self):
        rows = self.db.fetchall("SELECT id, name FROM categories ORDER BY name")
        self._fill_table(self.HEADERS, rows)

    def on_add(self):
        if CategoryDialog(self.db).exec(): self.load()

    def on_edit(self):
        rid = self.selected_id()
        if rid is None: return
        row = self.db.fetchone("SELECT * FROM categories WHERE id=?", (rid,))
        if row and CategoryDialog(self.db, row).exec(): self.load()

    def on_delete(self):
        rid = self.selected_id()
        if rid is None: return
        if QMessageBox.question(self, "Удалить категорию", f"Удалить категорию #{rid}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM categories WHERE id=?", (rid,))
            self.load()


# ----------------------------------------------------------------------
# UsersTab  (только для администратора)
# ----------------------------------------------------------------------
class UsersTab(BaseTab):
    HEADERS = ["ID", "Логин", "Полное имя", "Роль"]

    def __init__(self, db, current_user_id: int):
        self._current_user_id = current_user_id
        super().__init__(db, title="")

    def load(self):
        role_labels = {'admin': 'Администратор', 'employee': 'Сотрудник'}
        raw = self.db.get_users()
        rows = [(r["id"], r["username"], r["full_name"],
                 role_labels.get(r["role"], r["role"])) for r in raw]
        self._fill_table(self.HEADERS, rows)

    def on_add(self):
        if UserDialog(self.db).exec(): self.load()

    def on_edit(self):
        rid = self.selected_id()
        if rid is None: return
        row = self.db.fetchone("SELECT * FROM users WHERE id=?", (rid,))
        if row and UserDialog(self.db, row).exec(): self.load()

    def on_delete(self):
        rid = self.selected_id()
        if rid is None: return
        if rid == self._current_user_id:
            QMessageBox.warning(self, "Нельзя удалить", "Нельзя удалить собственную учётную запись.")
            return
        # Убеждаемся, что останется хотя бы один администратор
        row = self.db.fetchone("SELECT role FROM users WHERE id=?", (rid,))
        if row and row["role"] == ROLE_ADMIN:
            count = self.db.fetchone(
                "SELECT COUNT(*) AS c FROM users WHERE role=?", (ROLE_ADMIN,)
            )["c"]
            if count <= 1:
                QMessageBox.warning(self, "Нельзя удалить",
                    "В системе должен оставаться хотя бы один администратор.")
                return
        if QMessageBox.question(self, "Удалить пользователя", f"Удалить пользователя #{rid}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.db.delete_user(rid)
            self.load()
