import re
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
    QSpinBox, QComboBox, QDialogButtonBox, QVBoxLayout,
    QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from database import ACTIVE_STATUSES

_FORBIDDEN_RE = re.compile(r'[\x00-\x1f<>"\\]')


def _validate_text(value: str, field_label: str, required: bool = True) -> str | None:
    stripped = value.strip()
    if required and not stripped:
        return f'Поле «{field_label}» не может быть пустым.'
    if stripped and _FORBIDDEN_RE.search(stripped):
        return (f'Поле «{field_label}» содержит недопустимые символы.\n'
                f'Запрещены: управляющие символы, < > " \\')
    return None


def _validate_date(value: str) -> str | None:
    stripped = value.strip()
    if not stripped:
        return 'Поле «Дата» не может быть пустым.'
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', stripped):
        return 'Поле «Дата» должно быть в формате ГГГГ-ММ-ДД (например, 2025-06-21).'
    return None


def _show_error(parent, message: str):
    QMessageBox.warning(parent, 'Ошибка ввода', message)


def _make_phone_field() -> QLineEdit:
    """QLineEdit с валидатором для телефонного номера."""
    f = QLineEdit()
    f.setPlaceholderText("+7 (999) 123-45-67")
    f.setMaxLength(20)
    validator = QRegularExpressionValidator(
        QRegularExpression(r'[\d\s\+\-\(\)\.]*')
    )
    f.setValidator(validator)
    return f


def _make_sku_field() -> QLineEdit:
    """QLineEdit для артикула — латиница, цифры, дефис, точка, слэш."""
    f = QLineEdit()
    f.setPlaceholderText("ABC-001")
    f.setMaxLength(50)
    validator = QRegularExpressionValidator(
        QRegularExpression(r'[A-Za-z0-9\-_\./ ]*')
    )
    f.setValidator(validator)
    return f


def _make_date_field() -> QLineEdit:
    """QLineEdit с маской даты ГГГГ-ММ-ДД."""
    f = QLineEdit()
    f.setInputMask("9999-99-99;_")
    f.setPlaceholderText("ГГГГ-ММ-ДД")
    f.setMaxLength(10)
    return f


def _make_name_field(max_length: int = 150) -> QLineEdit:
    """Обычное текстовое поле с ограничением длины."""
    f = QLineEdit()
    f.setMaxLength(max_length)
    return f


class _BaseDialog(QDialog):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.form = QFormLayout()
        layout = QVBoxLayout(self)
        layout.addLayout(self.form)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)


# ----------------------------------------------------------------------
# ProductDialog
# ----------------------------------------------------------------------
class ProductDialog(_BaseDialog):
    def __init__(self, db, row=None):
        super().__init__("Товар")
        self.db = db
        self.row = row
        self.f_name = _make_name_field()
        self.f_sku = _make_sku_field()
        self.f_price = QDoubleSpinBox()
        self.f_price.setDecimals(2)
        self.f_price.setMaximum(9999999.99)
        self.f_price.setGroupSeparatorShown(True)
        self.f_stock = QSpinBox()
        self.f_stock.setMaximum(999999)
        self.f_stock.setGroupSeparatorShown(True)

        self._reserved = 0
        if row is not None:
            self._reserved = db.get_reserved_stock(row["id"])
            self.f_stock.setMinimum(self._reserved)
            tip = (f"Минимально допустимый остаток: {self._reserved} "
                   f"(зарезервировано в активных заказах)")
            self.f_stock.setToolTip(tip)

        self.f_cat = QComboBox()
        cats = db.fetchall("SELECT id, name FROM categories ORDER BY name")
        self._cat_ids = [r[0] for r in cats]
        self.f_cat.addItems([r[1] for r in cats])
        if not self._cat_ids:
            self.f_cat.setEnabled(False)
        self.f_sup = QComboBox()
        sups = db.fetchall("SELECT id, name FROM suppliers ORDER BY name")
        self._sup_ids = [r[0] for r in sups]
        self.f_sup.addItems([r[1] for r in sups])
        if not self._sup_ids:
            self.f_sup.setEnabled(False)
        self.form.addRow("Название", self.f_name)
        self.form.addRow("Артикул", self.f_sku)
        self.form.addRow("Цена", self.f_price)
        self.form.addRow("Остаток", self.f_stock)
        self.form.addRow("Категория", self.f_cat)
        self.form.addRow("Поставщик", self.f_sup)
        self._fill_form(row)

    def _fill_form(self, row):
        if row is None:
            return
        self.f_name.setText(row["name"] or "")
        self.f_sku.setText(row["sku"] or "")
        self.f_price.setValue(float(row["price"]) if row["price"] else 0.0)
        self.f_stock.setValue(int(row["stock"]) if row["stock"] else 0)
        if self._cat_ids and row["category_id"] is not None:
            try:
                self.f_cat.setCurrentIndex(self._cat_ids.index(row["category_id"]))
            except ValueError:
                pass
        if self._sup_ids and row["supplier_id"] is not None:
            try:
                self.f_sup.setCurrentIndex(self._sup_ids.index(row["supplier_id"]))
            except ValueError:
                pass

    def accept(self):
        for err in [
            _validate_text(self.f_name.text(), 'Название'),
            _validate_text(self.f_sku.text(), 'Артикул'),
        ]:
            if err:
                _show_error(self, err)
                return

        new_stock = self.f_stock.value()
        if new_stock < self._reserved:
            _show_error(
                self,
                f'Нельзя установить остаток меньше {self._reserved} — '
                f'это количество уже зарезервировано в активных заказах.'
            )
            return

        cat_id = None
        if self._cat_ids and self.f_cat.currentIndex() >= 0:
            cat_id = self._cat_ids[self.f_cat.currentIndex()]
        sup_id = None
        if self._sup_ids and self.f_sup.currentIndex() >= 0:
            sup_id = self._sup_ids[self.f_sup.currentIndex()]
        if self.row:
            self.db.execute(
                "UPDATE products SET name=?,sku=?,price=?,stock=?,category_id=?,supplier_id=? WHERE id=?",
                (self.f_name.text().strip(), self.f_sku.text().strip(),
                 self.f_price.value(), new_stock,
                 cat_id, sup_id, self.row["id"]),
            )
        else:
            self.db.execute(
                "INSERT INTO products(name,sku,price,stock,category_id,supplier_id) VALUES(?,?,?,?,?,?)",
                (self.f_name.text().strip(), self.f_sku.text().strip(),
                 self.f_price.value(), new_stock, cat_id, sup_id),
            )
        super().accept()


# ----------------------------------------------------------------------
# ClientDialog
# ----------------------------------------------------------------------
class ClientDialog(_BaseDialog):
    def __init__(self, db, row=None):
        super().__init__("Клиент")
        self.db = db
        self.row = row
        self.f_name = _make_name_field()
        self.f_contact = _make_name_field(100)
        self.f_phone = _make_phone_field()
        self.f_address = _make_name_field(250)
        self.form.addRow("Название", self.f_name)
        self.form.addRow("Контактное лицо", self.f_contact)
        self.form.addRow("Телефон", self.f_phone)
        self.form.addRow("Адрес", self.f_address)
        self._fill_form(row)

    def _fill_form(self, row):
        if row is None:
            return
        self.f_name.setText(row["name"] or "")
        self.f_contact.setText(row["contact"] or "")
        self.f_phone.setText(row["phone"] or "")
        self.f_address.setText(row["address"] or "")

    def accept(self):
        for err in [
            _validate_text(self.f_name.text(), 'Название'),
            _validate_text(self.f_contact.text(), 'Контактное лицо', required=False),
            _validate_text(self.f_phone.text(), 'Телефон', required=False),
            _validate_text(self.f_address.text(), 'Адрес', required=False),
        ]:
            if err:
                _show_error(self, err)
                return
        phone = self.f_phone.text().strip()
        if phone and not re.fullmatch(r'[\d\s\+\-\(\)\.]+', phone):
            _show_error(self, 'Поле «Телефон» содержит недопустимые символы.\n'
                              'Допустимы: цифры, пробелы, + - ( ) .')
            return
        if self.row:
            self.db.execute(
                "UPDATE clients SET name=?,contact=?,phone=?,address=? WHERE id=?",
                (self.f_name.text().strip(), self.f_contact.text().strip(),
                 phone, self.f_address.text().strip(), self.row["id"]),
            )
        else:
            self.db.execute(
                "INSERT INTO clients(name,contact,phone,address) VALUES(?,?,?,?)",
                (self.f_name.text().strip(), self.f_contact.text().strip(),
                 phone, self.f_address.text().strip()),
            )
        super().accept()


# ----------------------------------------------------------------------
# SupplierDialog
# ----------------------------------------------------------------------
class SupplierDialog(_BaseDialog):
    def __init__(self, db, row=None):
        super().__init__("Поставщик")
        self.db = db
        self.row = row
        self.f_name = _make_name_field()
        self.f_contact = _make_name_field(100)
        self.f_phone = _make_phone_field()
        self.f_address = _make_name_field(250)
        self.form.addRow("Название", self.f_name)
        self.form.addRow("Контактное лицо", self.f_contact)
        self.form.addRow("Телефон", self.f_phone)
        self.form.addRow("Адрес", self.f_address)
        self._fill_form(row)

    def _fill_form(self, row):
        if row is None:
            return
        self.f_name.setText(row["name"] or "")
        self.f_contact.setText(row["contact"] or "")
        self.f_phone.setText(row["phone"] or "")
        self.f_address.setText(row["address"] or "")

    def accept(self):
        for err in [
            _validate_text(self.f_name.text(), 'Название'),
            _validate_text(self.f_contact.text(), 'Контактное лицо', required=False),
            _validate_text(self.f_phone.text(), 'Телефон', required=False),
            _validate_text(self.f_address.text(), 'Адрес', required=False),
        ]:
            if err:
                _show_error(self, err)
                return
        phone = self.f_phone.text().strip()
        if phone and not re.fullmatch(r'[\d\s\+\-\(\)\.]+', phone):
            _show_error(self, 'Поле «Телефон» содержит недопустимые символы.\n'
                              'Допустимы: цифры, пробелы, + - ( ) .')
            return
        if self.row:
            self.db.execute(
                "UPDATE suppliers SET name=?,contact=?,phone=?,address=? WHERE id=?",
                (self.f_name.text().strip(), self.f_contact.text().strip(),
                 phone, self.f_address.text().strip(), self.row["id"]),
            )
        else:
            self.db.execute(
                "INSERT INTO suppliers(name,contact,phone,address) VALUES(?,?,?,?)",
                (self.f_name.text().strip(), self.f_contact.text().strip(),
                 phone, self.f_address.text().strip()),
            )
        super().accept()


# ----------------------------------------------------------------------
# CategoryDialog
# ----------------------------------------------------------------------
class CategoryDialog(_BaseDialog):
    def __init__(self, db, row=None):
        super().__init__("Категория")
        self.db = db
        self.row = row
        self.f_name = _make_name_field()
        self.form.addRow("Название", self.f_name)
        self._fill_form(row)

    def _fill_form(self, row):
        if row is None:
            return
        self.f_name.setText(row["name"] or "")

    def accept(self):
        err = _validate_text(self.f_name.text(), 'Название')
        if err:
            _show_error(self, err)
            return
        if self.row:
            self.db.execute(
                "UPDATE categories SET name=? WHERE id=?",
                (self.f_name.text().strip(), self.row["id"]),
            )
        else:
            self.db.execute(
                "INSERT INTO categories(name) VALUES(?)",
                (self.f_name.text().strip(),),
            )
        super().accept()


# ----------------------------------------------------------------------
# OrderDialog
# ----------------------------------------------------------------------
class OrderDialog(QDialog):
    """Dialog for creating or editing an order with product line items."""

    _ITEM_HEADERS = ["ID позиции", "Товар", "Кол-во", "Цена за ед.", "Сумма"]
    _STATUSES = ['новый', 'в обработке', 'выполнен', 'отменён']

    def __init__(self, db, row=None):
        super().__init__()
        self.db = db
        self.row = row
        self.setWindowTitle("Заказ")
        self.setMinimumWidth(680)

        prods = db.fetchall("SELECT id, name, price, stock FROM products ORDER BY name")
        self._prod_ids = [p[0] for p in prods]
        self._prod_names = [p[1] for p in prods]
        self._prod_price = {p[0]: float(p[2] or 0) for p in prods}
        self._prod_avail = {p[0]: int(p[3] or 0) for p in prods}
        if row is not None:
            existing = db.get_order_items(row["id"])
            for it in existing:
                pid = it["product_id"]
                if pid is not None and pid in self._prod_avail:
                    self._prod_avail[pid] += int(it["qty"])

        clients = db.fetchall("SELECT id, name FROM clients ORDER BY name")
        self._client_ids = [c[0] for c in clients]

        main = QVBoxLayout(self)

        form = QFormLayout()
        self.f_client = QComboBox()
        self.f_client.addItems([c[1] for c in clients])
        if not self._client_ids:
            self.f_client.setEnabled(False)

        self.f_date = _make_date_field()

        self.f_status = QComboBox()
        self.f_status.addItems(self._STATUSES)

        form.addRow("Клиент", self.f_client)
        form.addRow("Дата",   self.f_date)
        form.addRow("Статус", self.f_status)
        main.addLayout(form)

        main.addWidget(QLabel("<b>Товары в заказе:</b>"))

        add_row = QHBoxLayout()
        self.cb_product = QComboBox()
        self.cb_product.addItems(self._prod_names)
        self.cb_product.setMinimumWidth(200)
        if not self._prod_ids:
            self.cb_product.setEnabled(False)
        self.cb_product.currentIndexChanged.connect(self._update_qty_max)

        self.sp_qty = QSpinBox()
        self.sp_qty.setMinimum(1)
        self.sp_qty.setMaximum(99999)
        self.sp_qty.setValue(1)

        self.lbl_avail = QLabel()
        self._update_qty_max()

        self.btn_add_item = QPushButton("+ Добавить товар")
        self.btn_del_item = QPushButton("− Убрать")

        add_row.addWidget(QLabel("Товар:"))
        add_row.addWidget(self.cb_product, 1)
        add_row.addWidget(QLabel("Кол-во:"))
        add_row.addWidget(self.sp_qty)
        add_row.addWidget(self.lbl_avail)
        add_row.addWidget(self.btn_add_item)
        add_row.addWidget(self.btn_del_item)
        main.addLayout(add_row)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(len(self._ITEM_HEADERS))
        self.items_table.setHorizontalHeaderLabels(self._ITEM_HEADERS)
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.items_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.items_table.setColumnHidden(0, True)
        self.items_table.setMinimumHeight(180)
        main.addWidget(self.items_table)

        total_row = QHBoxLayout()
        total_row.addStretch()
        self.lbl_total = QLabel("Итого: 0.00")
        self.lbl_total.setStyleSheet("font-weight: bold; font-size: 14px;")
        total_row.addWidget(self.lbl_total)
        main.addLayout(total_row)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main.addWidget(btns)

        self.btn_add_item.clicked.connect(self._on_add_item)
        self.btn_del_item.clicked.connect(self._on_del_item)

        self._pending: list[dict] = []
        self._tmp_counter = 0

        self._fill_form(row)

    def _update_qty_max(self):
        if not self._prod_ids:
            self.lbl_avail.setText("")
            return
        idx = self.cb_product.currentIndex()
        if idx < 0:
            return
        pid = self._prod_ids[idx]
        avail = self._prod_avail.get(pid, 0)
        self.sp_qty.setMaximum(max(avail, 1))
        self.lbl_avail.setText(f"(дост.: {avail})")

    def _fill_form(self, row):
        if row is None:
            return
        if self._client_ids and row["client_id"] is not None:
            try:
                self.f_client.setCurrentIndex(self._client_ids.index(row["client_id"]))
            except ValueError:
                pass
        self.f_date.setText(row["date"] or "")
        idx = self.f_status.findText(row["status"] or "новый")
        if idx >= 0:
            self.f_status.setCurrentIndex(idx)
        items = self.db.get_order_items(row["id"])
        for it in items:
            self._append_item_row(
                item_id=it["id"],
                prod_id=it["product_id"],
                prod_name=it["product"],
                qty=it["qty"],
                price=it["price"],
            )
        self._refresh_total()
        self._update_qty_max()

    def _append_item_row(self, item_id, prod_id, prod_name, qty, price):
        r = self.items_table.rowCount()
        self.items_table.insertRow(r)
        subtotal = qty * price
        for c, val in enumerate([str(item_id), prod_name, str(qty), f"{price:.2f}", f"{subtotal:.2f}"]):
            self.items_table.setItem(r, c, QTableWidgetItem(val))
        self.items_table.item(r, 0).setData(Qt.ItemDataRole.UserRole, prod_id)

    def _refresh_total(self):
        total = 0.0
        for r in range(self.items_table.rowCount()):
            try:
                total += float(self.items_table.item(r, 4).text())
            except (AttributeError, ValueError):
                pass
        self.lbl_total.setText(f"Итого: {total:.2f}")

    def _on_add_item(self):
        if not self._prod_ids:
            _show_error(self, "Нет доступных товаров. Сначала добавьте товары.")
            return
        idx = self.cb_product.currentIndex()
        prod_id = self._prod_ids[idx]
        prod_name = self._prod_names[idx]
        price = self._prod_price[prod_id]
        qty = self.sp_qty.value()
        avail = self._prod_avail.get(prod_id, 0)

        if qty > avail:
            _show_error(self, f'Недостаточно товара «{prod_name}». Доступно: {avail}.')
            return

        if self.row is not None:
            try:
                self.db.add_order_item(self.row["id"], prod_id, qty, price)
            except ValueError as e:
                _show_error(self, str(e))
                return
            item_id = self.db.fetchone(
                "SELECT id FROM order_items WHERE order_id=? ORDER BY id DESC LIMIT 1",
                (self.row["id"],)
            )["id"]
        else:
            self._tmp_counter += 1
            item_id = -self._tmp_counter
            self._pending.append({"tmp_id": item_id, "product_id": prod_id, "qty": qty, "price": price})

        self._prod_avail[prod_id] = avail - qty
        self._append_item_row(item_id, prod_id, prod_name, qty, price)
        self._refresh_total()
        self._update_qty_max()

    def _on_del_item(self):
        sel = self.items_table.currentRow()
        if sel < 0:
            return
        item_id = int(self.items_table.item(sel, 0).text())
        prod_id = self.items_table.item(sel, 0).data(Qt.ItemDataRole.UserRole)
        qty = int(self.items_table.item(sel, 2).text())

        if self.row is not None and item_id > 0:
            self.db.delete_order_item(item_id, self.row["id"])
        else:
            self._pending = [p for p in self._pending if p["tmp_id"] != item_id]

        if prod_id is not None:
            self._prod_avail[prod_id] = self._prod_avail.get(prod_id, 0) + qty

        self.items_table.removeRow(sel)
        self._refresh_total()
        self._update_qty_max()

    def accept(self):
        if not self._client_ids:
            _show_error(self, "Нет доступных клиентов. Сначала добавьте клиента.")
            return
        err = _validate_date(self.f_date.text().replace('_', '').strip())
        if err:
            _show_error(self, err)
            return
        if self.items_table.rowCount() == 0:
            _show_error(self, "Добавьте хотя бы один товар в заказ.")
            return

        client_id = self._client_ids[self.f_client.currentIndex()]
        date = self.f_date.text().strip()
        new_status = self.f_status.currentText()

        if self.row:
            old_status = self.row["status"]
            if old_status != new_status:
                try:
                    self.db.update_order_status(self.row["id"], new_status)
                except ValueError as e:
                    _show_error(self, str(e))
                    return
            self.db.execute(
                "UPDATE orders SET client_id=?,date=? WHERE id=?",
                (client_id, date, self.row["id"]),
            )
            self.db._recalc_order(self.row["id"])
        else:
            order_id = self.db.execute(
                "INSERT INTO orders(client_id,date,status,total) VALUES(?,?,?,0)",
                (client_id, date, new_status),
            )
            for p in self._pending:
                stock = self.db.get_product_stock(p["product_id"])
                if p["qty"] > stock:
                    self.db.execute("DELETE FROM orders WHERE id=?", (order_id,))
                    prod_name = self._prod_names[self._prod_ids.index(p["product_id"])]
                    _show_error(self, f'Недостаточно товара «{prod_name}» на складе. Доступно: {stock}.')
                    return
                self.db.add_order_item(order_id, p["product_id"], p["qty"], p["price"])
            self.db._recalc_order(order_id)
        super().accept()


# ----------------------------------------------------------------------
# ViewOrderDialog
# ----------------------------------------------------------------------
class ViewOrderDialog(QDialog):
    _ITEM_HEADERS = ["Товар", "Кол-во", "Цена за ед.", "Сумма"]

    def __init__(self, db, order_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Просмотр заказа #{order_id}")
        self.setMinimumWidth(560)

        order = db.fetchone(
            "SELECT o.id, COALESCE(c.name,'') AS client, o.date, o.status, o.total "
            "FROM orders o LEFT JOIN clients c ON c.id=o.client_id WHERE o.id=?",
            (order_id,),
        )
        items = db.get_order_items(order_id)

        layout = QVBoxLayout(self)
        info = QFormLayout()
        info.addRow("Номер заказа:",  QLabel(str(order["id"])))
        info.addRow("Клиент:",        QLabel(order["client"]))
        info.addRow("Дата:",          QLabel(order["date"] or "—"))
        info.addRow("Статус:",        QLabel(order["status"] or "—"))
        layout.addLayout(info)

        layout.addWidget(QLabel("<b>Состав заказа:</b>"))
        tbl = QTableWidget(len(items), len(self._ITEM_HEADERS))
        tbl.setHorizontalHeaderLabels(self._ITEM_HEADERS)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.setMinimumHeight(160)
        for r, it in enumerate(items):
            tbl.setItem(r, 0, QTableWidgetItem(it["product"]))
            tbl.setItem(r, 1, QTableWidgetItem(str(it["qty"])))
            tbl.setItem(r, 2, QTableWidgetItem(f"{float(it['price']):.2f}"))
            tbl.setItem(r, 3, QTableWidgetItem(f"{float(it['subtotal']):.2f}"))
        layout.addWidget(tbl)

        total_row = QHBoxLayout()
        total_row.addStretch()
        lbl = QLabel(f"<b>Итого: {float(order['total']):.2f}</b>")
        lbl.setStyleSheet("font-size: 14px;")
        total_row.addWidget(lbl)
        layout.addLayout(total_row)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
