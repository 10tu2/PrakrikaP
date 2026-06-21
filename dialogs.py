from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
    QSpinBox, QComboBox, QDialogButtonBox, QVBoxLayout,
    QMessageBox
)

class _BaseDialog(QDialog):
    """Base dialog with OK / Cancel buttons and a QFormLayout."""
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
        self.f_name = QLineEdit()
        self.f_sku = QLineEdit()
        self.f_price = QDoubleSpinBox()
        self.f_price.setDecimals(2)
        self.f_price.setMaximum(9999999.99)
        self.f_stock = QSpinBox()
        self.f_stock.setMaximum(999999)
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
            idx = self._cat_ids.index(row["category_id"])
            self.f_cat.setCurrentIndex(idx)
        if self._sup_ids and row["supplier_id"] is not None:
            idx = self._sup_ids.index(row["supplier_id"])
            self.f_sup.setCurrentIndex(idx)

    def accept(self):
        cat_id = None
        if self._cat_ids and self.f_cat.currentIndex() >= 0:
            cat_id = self._cat_ids[self.f_cat.currentIndex()]
        sup_id = None
        if self._sup_ids and self.f_sup.currentIndex() >= 0:
            sup_id = self._sup_ids[self.f_sup.currentIndex()]
        if self.row:
            self.db.execute(
                "UPDATE products SET name=?,sku=?,price=?,stock=?,category_id=?,supplier_id=? WHERE id=?",
                (self.f_name.text(), self.f_sku.text(), self.f_price.value(), self.f_stock.value(), cat_id, sup_id, self.row["id"]),
            )
        else:
            self.db.execute(
                "INSERT INTO products(name,sku,price,stock,category_id,supplier_id) VALUES(?,?,?,?,?,?)",
                (self.f_name.text(), self.f_sku.text(), self.f_price.value(), self.f_stock.value(), cat_id, sup_id),
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
        self.f_name = QLineEdit()
        self.f_contact = QLineEdit()
        self.f_phone = QLineEdit()
        self.f_address = QLineEdit()
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
        if self.row:
            self.db.execute(
                "UPDATE clients SET name=?,contact=?,phone=?,address=? WHERE id=?",
                (self.f_name.text(), self.f_contact.text(), self.f_phone.text(), self.f_address.text(), self.row["id"]),
            )
        else:
            self.db.execute(
                "INSERT INTO clients(name,contact,phone,address) VALUES(?,?,?,?)",
                (self.f_name.text(), self.f_contact.text(), self.f_phone.text(), self.f_address.text()),
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
        self.f_name = QLineEdit()
        self.f_contact = QLineEdit()
        self.f_phone = QLineEdit()
        self.f_address = QLineEdit()
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
        if self.row:
            self.db.execute(
                "UPDATE suppliers SET name=?,contact=?,phone=?,address=? WHERE id=?",
                (self.f_name.text(), self.f_contact.text(), self.f_phone.text(), self.f_address.text(), self.row["id"]),
            )
        else:
            self.db.execute(
                "INSERT INTO suppliers(name,contact,phone,address) VALUES(?,?,?,?)",
                (self.f_name.text(), self.f_contact.text(), self.f_phone.text(), self.f_address.text()),
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
        self.f_name = QLineEdit()
        self.form.addRow("Название", self.f_name)
        self._fill_form(row)

    def _fill_form(self, row):
        if row is None:
            return
        self.f_name.setText(row["name"] or "")

    def accept(self):
        if self.row:
            self.db.execute(
                "UPDATE categories SET name=? WHERE id=?",
                (self.f_name.text(), self.row["id"]),
            )
        else:
            self.db.execute(
                "INSERT INTO categories(name) VALUES(?)",
                (self.f_name.text(),),
            )
        super().accept()
        

# ----------------------------------------------------------------------
# OrderDialog
# ----------------------------------------------------------------------
class OrderDialog(_BaseDialog):
    def __init__(self, db, row=None):
        super().__init__("Заказ")
        self.db = db
        self.row = row
        self.f_client = QComboBox()
        clients = db.fetchall("SELECT id, name FROM clients ORDER BY name")
        self._client_ids = [r[0] for r in clients]
        self.f_client.addItems([r[1] for r in clients])
        if not self._client_ids:
            self.f_client.setEnabled(False)
        self.f_date = QLineEdit()
        self.f_status = QComboBox()
        self.f_status.addItems(["новый", "в обработке", "выполнен", "отменён"])
        self.f_total = QDoubleSpinBox()
        self.f_total.setDecimals(2)
        self.f_total.setMaximum(9999999.99)
        self.form.addRow("Клиент", self.f_client)
        self.form.addRow("Дата", self.f_date)
        self.form.addRow("Статус", self.f_status)
        self.form.addRow("Сумма", self.f_total)
        self._fill_form(row)

    def _fill_form(self, row):
        if row is None:
            return
        if self._client_ids and row["client_id"] is not None:
            idx = self._client_ids.index(row["client_id"])
            self.f_client.setCurrentIndex(idx)
        self.f_date.setText(row["date"] or "")
        status = row["status"] or "новый"
        idx = self.f_status.findText(status)
        if idx >= 0:
            self.f_status.setCurrentIndex(idx)
        self.f_total.setValue(float(row["total"]) if row["total"] else 0.0)

    def accept(self):
        client_id = None
        if self._client_ids and self.f_client.currentIndex() >= 0:
            client_id = self._client_ids[self.f_client.currentIndex()]
        if self.row:
            self.db.execute(
                "UPDATE orders SET client_id=?,date=?,status=?,total=? WHERE id=?",
                (client_id, self.f_date.text(), self.f_status.currentText(), self.f_total.value(), self.row["id"]),
            )
        else:
            self.db.execute(
                "INSERT INTO orders(client_id,date,status,total) VALUES(?,?,?,?)",
                (client_id, self.f_date.text(), self.f_status.currentText(), self.f_total.value()),
            )
        super().accept()
