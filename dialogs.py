from PyQt6.QtWidgets import (
  QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
  QSpinBox, QComboBox, QDialogButtonBox, QVBoxLayout
)


class _BaseDialog(QDialog):
  def __init__(self, title, parent=None):
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


class ProductDialog(_BaseDialog):
  def __init__(self, db, row=None):
    super().__init__("Товар")
    self.db = db
    self.row = row
    self.f_name = QLineEdit()
    self.f_sku = QLineEdit()
    self.f_price = QDoubleSpinBox(); self.f_price.setMaximum(9_999_999)
    self.f_stock = QSpinBox(); self.f_stock.setMaximum(999_999)
    self.f_cat = QComboBox()
    self.f_sup = QComboBox()
    cats = db.fetchall("SELECT id,name FROM categories", ())
    self._cat_ids = [r[0] for r in cats]
    self.f_cat.addItems([r[1] for r in cats])
    sups = db.fetchall("SELECT id,name FROM suppliers", ())
    self._sup_ids = [r[0] for r in sups]
    self.f_sup.addItems([r[1] for r in sups])
    self.form.addRow("Название", self.f_name)
    self.form.addRow("Артикул", self.f_sku)
    self.form.addRow("Цена", self.f_price)
    self.form.addRow("Остаток", self.f_stock)
    self.form.addRow("Категория", self.f_cat)
    self.form.addRow("Поставщик", self.f_sup)
    if row:
      self.f_name.setText(row["name"])
      self.f_sku.setText(row["sku"] or "")
      self.f_price.setValue(row["price"])
      self.f_stock.setValue(row["stock"])

  def accept(self):
    cat_id = self._cat_ids[self.f_cat.currentIndex()] if self._cat_ids else None
    sup_id = self._sup_ids[self.f_sup.currentIndex()] if self._sup_ids else None
    if self.row:
      self.db.execute(
        "UPDATE products SET name=?,sku=?,price=?,stock=?,category_id=?,supplier_id=? WHERE id=?",
        (self.f_name.text(), self.f_sku.text(), self.f_price.value(),
         self.f_stock.value(), cat_id, sup_id, self.row["id"]))
    else:
      self.db.execute(
        "INSERT INTO products(name,sku,price,stock,category_id,supplier_id) VALUES(?,?,?,?,?,?)",
        (self.f_name.text(), self.f_sku.text(), self.f_price.value(),
         self.f_stock.value(), cat_id, sup_id))
    super().accept()


class ClientDialog(_BaseDialog):
  def __init__(self, db, row=None):
    super().__init__("Клиент")
    self.db = db; self.row = row
    self.f_name = QLineEdit()
    self.f_contact = QLineEdit()
    self.f_phone = QLineEdit()
    self.f_address = QLineEdit()
    self.form.addRow("Название", self.f_name)
    self.form.addRow("Контакт", self.f_contact)
    self.form.addRow("Телефон", self.f_phone)
    self.form.addRow("Адрес", self.f_address)
    if row:
      self.f_name.setText(row["name"])
      self.f_contact.setText(row["contact"] or "")
      self.f_phone.setText(row["phone"] or "")
      self.f_address.setText(row["address"] or "")

  def accept(self):
    if self.row:
      self.db.execute(
        "UPDATE clients SET name=?,contact=?,phone=?,address=? WHERE id=?",
        (self.f_name.text(), self.f_contact.text(),
         self.f_phone.text(), self.f_address.text(), self.row["id"]))
    else:
      self.db.execute(
        "INSERT INTO clients(name,contact,phone,address) VALUES(?,?,?,?)",
        (self.f_name.text(), self.f_contact.text(),
         self.f_phone.text(), self.f_address.text()))
    super().accept()


class SupplierDialog(_BaseDialog):
  def __init__(self, db, row=None):
    super().__init__("Поставщик")
    self.db = db; self.row = row
    self.f_name = QLineEdit()
    self.f_contact = QLineEdit()
    self.f_phone = QLineEdit()
    self.f_address = QLineEdit()
    self.form.addRow("Название", self.f_name)
    self.form.addRow("Контакт", self.f_contact)
    self.form.addRow("Телефон", self.f_phone)
    self.form.addRow("Адрес", self.f_address)
    if row:
      self.f_name.setText(row["name"])
      self.f_contact.setText(row["contact"] or "")
      self.f_phone.setText(row["phone"] or "")
      self.f_address.setText(row["address"] or "")

  def accept(self):
    if self.row:
      self.db.execute(
        "UPDATE suppliers SET name=?,contact=?,phone=?,address=? WHERE id=?",
        (self.f_name.text(), self.f_contact.text(),
         self.f_phone.text(), self.f_address.text(), self.row["id"]))
    else:
      self.db.execute(
        "INSERT INTO suppliers(name,contact,phone,address) VALUES(?,?,?,?)",
        (self.f_name.text(), self.f_contact.text(),
         self.f_phone.text(), self.f_address.text()))
    super().accept()


class CategoryDialog(_BaseDialog):
  def __init__(self, db, row=None):
    super().__init__("Категория")
    self.db = db; self.row = row
    self.f_name = QLineEdit()
    self.form.addRow("Название", self.f_name)
    if row:
      self.f_name.setText(row["name"])

  def accept(self):
    if self.row:
      self.db.execute("UPDATE categories SET name=? WHERE id=?",
                      (self.f_name.text(), self.row["id"]))
    else:
      self.db.execute("INSERT INTO categories(name) VALUES(?)",
                      (self.f_name.text(),))
    super().accept()


class OrderDialog(_BaseDialog):
  def __init__(self, db, row=None):
    super().__init__("Заказ")
    self.db = db; self.row = row
    self.f_client = QComboBox()
    self.f_date = QLineEdit()
    self.f_status = QComboBox()
    self.f_status.addItems(["новый", "в обработке", "отгружен", "отменён"])
    clients = db.fetchall("SELECT id,name FROM clients", ())
    self._client_ids = [r[0] for r in clients]
    self.f_client.addItems([r[1] for r in clients])
    self.form.addRow("Клиент", self.f_client)
    self.form.addRow("Дата (YYYY-MM-DD)", self.f_date)
    self.form.addRow("Статус", self.f_status)
    if row:
      self.f_date.setText(row["date"] or "")
      idx = self.f_status.findText(row["status"])
      if idx >= 0:
        self.f_status.setCurrentIndex(idx)

  def accept(self):
    client_id = self._client_ids[self.f_client.currentIndex()] if self._client_ids else None
    if self.row:
      self.db.execute(
        "UPDATE orders SET client_id=?,date=?,status=? WHERE id=?",
        (client_id, self.f_date.text(), self.f_status.currentText(), self.row["id"]))
    else:
      self.db.execute(
        "INSERT INTO orders(client_id,date,status,total) VALUES(?,?,?,0)",
        (client_id, self.f_date.text(), self.f_status.currentText()))
    super().accept()
