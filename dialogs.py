import re
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
    QSpinBox, QComboBox, QDialogButtonBox, QVBoxLayout,
    QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt

_FORBIDDEN_RE = re.compile(r'[\x00-\x1f<>"\\]')


def _validate_text(value: str, field_label: str, required: bool = True) -> str | None:
    stripped = value.strip()
    if required and not stripped:
        return f'\u041f\u043e\u043b\u0435 \u00ab{field_label}\u00bb \u043d\u0435 \u043c\u043e\u0436\u0435\u0442 \u0431\u044b\u0442\u044c \u043f\u0443\u0441\u0442\u044b\u043c.'
    if stripped and _FORBIDDEN_RE.search(stripped):
        return (f'\u041f\u043e\u043b\u0435 \u00ab{field_label}\u00bb \u0441\u043e\u0434\u0435\u0440\u0436\u0438\u0442 \u043d\u0435\u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u044b\u0435 \u0441\u0438\u043c\u0432\u043e\u043b\u044b.\n'
                f'\u0417\u0430\u043f\u0440\u0435\u0449\u0435\u043d\u044b: \u0443\u043f\u0440\u0430\u0432\u043b\u044f\u044e\u0449\u0438\u0435 \u0441\u0438\u043c\u0432\u043e\u043b\u044b, < > " \\')
    return None


def _validate_date(value: str) -> str | None:
    stripped = value.strip()
    if not stripped:
        return '\u041f\u043e\u043b\u0435 \u00ab\u0414\u0430\u0442\u0430\u00bb \u043d\u0435 \u043c\u043e\u0436\u0435\u0442 \u0431\u044b\u0442\u044c \u043f\u0443\u0441\u0442\u044b\u043c.'
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', stripped):
        return '\u041f\u043e\u043b\u0435 \u00ab\u0414\u0430\u0442\u0430\u00bb \u0434\u043e\u043b\u0436\u043d\u043e \u0431\u044b\u0442\u044c \u0432 \u0444\u043e\u0440\u043c\u0430\u0442\u0435 \u0413\u0413\u0413\u0413-\u041c\u041c-\u0414\u0414 (\u043d\u0430\u043f\u0440\u0438\u043c\u0435\u0440, 2025-06-21).'
    return None


def _show_error(parent, message: str):
    QMessageBox.warning(parent, '\u041e\u0448\u0438\u0431\u043a\u0430 \u0432\u0432\u043e\u0434\u0430', message)


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
        super().__init__("\u0422\u043e\u0432\u0430\u0440")
        self.db = db
        self.row = row
        self.f_name = QLineEdit()
        self.f_sku = QLineEdit()
        self.f_price = QDoubleSpinBox()
        self.f_price.setDecimals(2)
        self.f_price.setMaximum(9999999.99)
        self.f_stock = QSpinBox()
        self.f_stock.setMaximum(999999)

        # If editing, compute reserved qty so user can't set stock below it
        self._reserved = 0
        if row is not None:
            self._reserved = db.get_reserved_stock(row["id"])
            self.f_stock.setMinimum(self._reserved)
            tip = (f"\u041c\u0438\u043d\u0438\u043c\u0430\u043b\u044c\u043d\u043e \u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u044b\u0439 \u043e\u0441\u0442\u0430\u0442\u043e\u043a: {self._reserved} "
                   f"(\u0437\u0430\u0440\u0435\u0437\u0435\u0440\u0432\u0438\u0440\u043e\u0432\u0430\u043d\u043e \u0432 \u0437\u0430\u043a\u0430\u0437\u0430\u0445)")
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
        self.form.addRow("\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435", self.f_name)
        self.form.addRow("\u0410\u0440\u0442\u0438\u043a\u0443\u043b", self.f_sku)
        self.form.addRow("\u0426\u0435\u043d\u0430", self.f_price)
        self.form.addRow("\u041e\u0441\u0442\u0430\u0442\u043e\u043a", self.f_stock)
        self.form.addRow("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f", self.f_cat)
        self.form.addRow("\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a", self.f_sup)
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
            _validate_text(self.f_name.text(), '\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435'),
            _validate_text(self.f_sku.text(), '\u0410\u0440\u0442\u0438\u043a\u0443\u043b'),
        ]:
            if err:
                _show_error(self, err)
                return

        new_stock = self.f_stock.value()
        if new_stock < self._reserved:
            _show_error(
                self,
                f'\u041d\u0435\u043b\u044c\u0437\u044f \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c \u043e\u0441\u0442\u0430\u0442\u043e\u043a \u043c\u0435\u043d\u044c\u0448\u0435 {self._reserved} — \u044d\u0442\u043e \u043a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e \u0443\u0436\u0435 \u0437\u0430\u0440\u0435\u0437\u0435\u0440\u0432\u0438\u0440\u043e\u0432\u0430\u043d\u043e \u0432 \u0437\u0430\u043a\u0430\u0437\u0430\u0445.'
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
        super().__init__("\u041a\u043b\u0438\u0435\u043d\u0442")
        self.db = db
        self.row = row
        self.f_name = QLineEdit()
        self.f_contact = QLineEdit()
        self.f_phone = QLineEdit()
        self.f_address = QLineEdit()
        self.form.addRow("\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435", self.f_name)
        self.form.addRow("\u041a\u043e\u043d\u0442\u0430\u043a\u0442\u043d\u043e\u0435 \u043b\u0438\u0446\u043e", self.f_contact)
        self.form.addRow("\u0422\u0435\u043b\u0435\u0444\u043e\u043d", self.f_phone)
        self.form.addRow("\u0410\u0434\u0440\u0435\u0441", self.f_address)
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
            _validate_text(self.f_name.text(), '\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435'),
            _validate_text(self.f_contact.text(), '\u041a\u043e\u043d\u0442\u0430\u043a\u0442\u043d\u043e\u0435 \u043b\u0438\u0446\u043e', required=False),
            _validate_text(self.f_phone.text(), '\u0422\u0435\u043b\u0435\u0444\u043e\u043d', required=False),
            _validate_text(self.f_address.text(), '\u0410\u0434\u0440\u0435\u0441', required=False),
        ]:
            if err:
                _show_error(self, err)
                return
        phone = self.f_phone.text().strip()
        if phone and not re.fullmatch(r'[\d\s\+\-\(\)\.]+', phone):
            _show_error(self, '\u041f\u043e\u043b\u0435 \u00ab\u0422\u0435\u043b\u0435\u0444\u043e\u043d\u00bb \u0441\u043e\u0434\u0435\u0440\u0436\u0438\u0442 \u043d\u0435\u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u044b\u0435 \u0441\u0438\u043c\u0432\u043e\u043b\u044b.\n'
                              '\u0414\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u044b: \u0446\u0438\u0444\u0440\u044b, \u043f\u0440\u043e\u0431\u0435\u043b\u044b, + - ( ) .')
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
        super().__init__("\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a")
        self.db = db
        self.row = row
        self.f_name = QLineEdit()
        self.f_contact = QLineEdit()
        self.f_phone = QLineEdit()
        self.f_address = QLineEdit()
        self.form.addRow("\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435", self.f_name)
        self.form.addRow("\u041a\u043e\u043d\u0442\u0430\u043a\u0442\u043d\u043e\u0435 \u043b\u0438\u0446\u043e", self.f_contact)
        self.form.addRow("\u0422\u0435\u043b\u0435\u0444\u043e\u043d", self.f_phone)
        self.form.addRow("\u0410\u0434\u0440\u0435\u0441", self.f_address)
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
            _validate_text(self.f_name.text(), '\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435'),
            _validate_text(self.f_contact.text(), '\u041a\u043e\u043d\u0442\u0430\u043a\u0442\u043d\u043e\u0435 \u043b\u0438\u0446\u043e', required=False),
            _validate_text(self.f_phone.text(), '\u0422\u0435\u043b\u0435\u0444\u043e\u043d', required=False),
            _validate_text(self.f_address.text(), '\u0410\u0434\u0440\u0435\u0441', required=False),
        ]:
            if err:
                _show_error(self, err)
                return
        phone = self.f_phone.text().strip()
        if phone and not re.fullmatch(r'[\d\s\+\-\(\)\.]+', phone):
            _show_error(self, '\u041f\u043e\u043b\u0435 \u00ab\u0422\u0435\u043b\u0435\u0444\u043e\u043d\u00bb \u0441\u043e\u0434\u0435\u0440\u0436\u0438\u0442 \u043d\u0435\u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u044b\u0435 \u0441\u0438\u043c\u0432\u043e\u043b\u044b.\n'
                              '\u0414\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u044b: \u0446\u0438\u0444\u0440\u044b, \u043f\u0440\u043e\u0431\u0435\u043b\u044b, + - ( ) .')
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
        super().__init__("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f")
        self.db = db
        self.row = row
        self.f_name = QLineEdit()
        self.form.addRow("\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435", self.f_name)
        self._fill_form(row)

    def _fill_form(self, row):
        if row is None:
            return
        self.f_name.setText(row["name"] or "")

    def accept(self):
        err = _validate_text(self.f_name.text(), '\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')
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

    _ITEM_HEADERS = ["ID \u043f\u043e\u0437\u0438\u0446\u0438\u0438", "\u0422\u043e\u0432\u0430\u0440", "\u041a\u043e\u043b-\u0432\u043e", "\u0426\u0435\u043d\u0430 \u0437\u0430 \u0435\u0434.", "\u0421\u0443\u043c\u043c\u0430"]

    def __init__(self, db, row=None):
        super().__init__()
        self.db = db
        self.row = row
        self.setWindowTitle("\u0417\u0430\u043a\u0430\u0437")
        self.setMinimumWidth(680)

        # Load products with stock; in edit mode add back qty already in this order
        prods = db.fetchall("SELECT id, name, price, stock FROM products ORDER BY name")
        self._prod_ids = [p[0] for p in prods]
        self._prod_names = [p[1] for p in prods]
        self._prod_price = {p[0]: float(p[2] or 0) for p in prods}
        # Available = current stock (already has order items subtracted from DB)
        # For EDIT mode we restore the qty from this order so user sees real available
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

        self.f_date = QLineEdit()
        self.f_date.setPlaceholderText("\u0413\u0413\u0413\u0413-\u041c\u041c-\u0414\u0414")

        self.f_status = QComboBox()
        self.f_status.addItems(["\u043d\u043e\u0432\u044b\u0439", "\u0432 \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0435", "\u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d", "\u043e\u0442\u043c\u0435\u043d\u0451\u043d"])

        form.addRow("\u041a\u043b\u0438\u0435\u043d\u0442", self.f_client)
        form.addRow("\u0414\u0430\u0442\u0430",   self.f_date)
        form.addRow("\u0421\u0442\u0430\u0442\u0443\u0441", self.f_status)
        main.addLayout(form)

        main.addWidget(QLabel("<b>\u0422\u043e\u0432\u0430\u0440\u044b \u0432 \u0437\u0430\u043a\u0430\u0437\u0435:</b>"))

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

        self.btn_add_item = QPushButton("+ \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0442\u043e\u0432\u0430\u0440")
        self.btn_del_item = QPushButton("\u2212 \u0423\u0431\u0440\u0430\u0442\u044c")

        add_row.addWidget(QLabel("\u0422\u043e\u0432\u0430\u0440:"))
        add_row.addWidget(self.cb_product, 1)
        add_row.addWidget(QLabel("\u041a\u043e\u043b-\u0432\u043e:"))
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
        self.lbl_total = QLabel("\u0418\u0442\u043e\u0433\u043e: 0.00")
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
        self.lbl_avail.setText(f"(\u0434\u043e\u0441\u0442.: {avail})")

    def _fill_form(self, row):
        if row is None:
            return
        if self._client_ids and row["client_id"] is not None:
            try:
                self.f_client.setCurrentIndex(self._client_ids.index(row["client_id"]))
            except ValueError:
                pass
        self.f_date.setText(row["date"] or "")
        idx = self.f_status.findText(row["status"] or "\u043d\u043e\u0432\u044b\u0439")
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
        # store prod_id in hidden column 0 item's UserRole for easy retrieval
        self.items_table.item(r, 0).setData(Qt.ItemDataRole.UserRole, prod_id)

    def _refresh_total(self):
        total = 0.0
        for r in range(self.items_table.rowCount()):
            try:
                total += float(self.items_table.item(r, 4).text())
            except (AttributeError, ValueError):
                pass
        self.lbl_total.setText(f"\u0418\u0442\u043e\u0433\u043e: {total:.2f}")

    def _on_add_item(self):
        if not self._prod_ids:
            _show_error(self, "\u041d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0445 \u0442\u043e\u0432\u0430\u0440\u043e\u0432. \u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0434\u043e\u0431\u0430\u0432\u044c\u0442\u0435 \u0442\u043e\u0432\u0430\u0440\u044b.")
            return
        idx = self.cb_product.currentIndex()
        prod_id = self._prod_ids[idx]
        prod_name = self._prod_names[idx]
        price = self._prod_price[prod_id]
        qty = self.sp_qty.value()
        avail = self._prod_avail.get(prod_id, 0)

        if qty > avail:
            _show_error(self, f'\u041d\u0435\u0434\u043e\u0441\u0442\u0430\u0442\u043e\u0447\u043d\u043e \u0442\u043e\u0432\u0430\u0440\u0430 \u00ab{prod_name}\u00bb. \u0414\u043e\u0441\u0442\u0443\u043f\u043d\u043e: {avail}.')
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
            _show_error(self, "\u041d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0445 \u043a\u043b\u0438\u0435\u043d\u0442\u043e\u0432. \u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0434\u043e\u0431\u0430\u0432\u044c\u0442\u0435 \u043a\u043b\u0438\u0435\u043d\u0442\u0430.")
            return
        err = _validate_date(self.f_date.text())
        if err:
            _show_error(self, err)
            return
        if self.items_table.rowCount() == 0:
            _show_error(self, "\u0414\u043e\u0431\u0430\u0432\u044c\u0442\u0435 \u0445\u043e\u0442\u044f \u0431\u044b \u043e\u0434\u0438\u043d \u0442\u043e\u0432\u0430\u0440 \u0432 \u0437\u0430\u043a\u0430\u0437.")
            return

        client_id = self._client_ids[self.f_client.currentIndex()]
        date = self.f_date.text().strip()
        status = self.f_status.currentText()

        if self.row:
            self.db.execute(
                "UPDATE orders SET client_id=?,date=?,status=? WHERE id=?",
                (client_id, date, status, self.row["id"]),
            )
            self.db._recalc_order(self.row["id"])
        else:
            order_id = self.db.execute(
                "INSERT INTO orders(client_id,date,status,total) VALUES(?,?,?,0)",
                (client_id, date, status),
            )
            for p in self._pending:
                stock = self.db.get_product_stock(p["product_id"])
                if p["qty"] > stock:
                    self.db.execute("DELETE FROM orders WHERE id=?", (order_id,))
                    prod_name = self._prod_names[self._prod_ids.index(p["product_id"])]
                    _show_error(self, f'\u041d\u0435\u0434\u043e\u0441\u0442\u0430\u0442\u043e\u0447\u043d\u043e \u0442\u043e\u0432\u0430\u0440\u0430 \u00ab{prod_name}\u00bb \u043d\u0430 \u0441\u043a\u043b\u0430\u0434\u0435. \u0414\u043e\u0441\u0442\u0443\u043f\u043d\u043e: {stock}.')
                    return
                self.db.add_order_item(order_id, p["product_id"], p["qty"], p["price"])
            self.db._recalc_order(order_id)
        super().accept()


# ----------------------------------------------------------------------
# ViewOrderDialog
# ----------------------------------------------------------------------
class ViewOrderDialog(QDialog):
    _ITEM_HEADERS = ["\u0422\u043e\u0432\u0430\u0440", "\u041a\u043e\u043b-\u0432\u043e", "\u0426\u0435\u043d\u0430 \u0437\u0430 \u0435\u0434.", "\u0421\u0443\u043c\u043c\u0430"]

    def __init__(self, db, order_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"\u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440 \u0437\u0430\u043a\u0430\u0437\u0430 #{order_id}")
        self.setMinimumWidth(560)

        order = db.fetchone(
            "SELECT o.id, COALESCE(c.name,'') AS client, o.date, o.status, o.total "
            "FROM orders o LEFT JOIN clients c ON c.id=o.client_id WHERE o.id=?",
            (order_id,),
        )
        items = db.get_order_items(order_id)

        layout = QVBoxLayout(self)
        info = QFormLayout()
        info.addRow("\u041d\u043e\u043c\u0435\u0440 \u0437\u0430\u043a\u0430\u0437\u0430:",  QLabel(str(order["id"])))
        info.addRow("\u041a\u043b\u0438\u0435\u043d\u0442:",        QLabel(order["client"]))
        info.addRow("\u0414\u0430\u0442\u0430:",          QLabel(order["date"] or "\u2014"))
        info.addRow("\u0421\u0442\u0430\u0442\u0443\u0441:",        QLabel(order["status"] or "\u2014"))
        layout.addLayout(info)

        layout.addWidget(QLabel("<b>\u0421\u043e\u0441\u0442\u0430\u0432 \u0437\u0430\u043a\u0430\u0437\u0430:</b>"))
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
        lbl = QLabel(f"<b>\u0418\u0442\u043e\u0433\u043e: {float(order['total']):.2f}</b>")
        lbl.setStyleSheet("font-size: 14px;")
        total_row.addWidget(lbl)
        layout.addLayout(total_row)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
