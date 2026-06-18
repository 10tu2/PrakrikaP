from PyQt6.QtWidgets import (
  QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
  QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from dialogs import (
  ProductDialog, OrderDialog, ClientDialog,
  SupplierDialog, CategoryDialog
)


class BaseTab(QWidget):
  def __init__(self, db):
    super().__init__()
    self.db = db
    self.layout_ = QVBoxLayout(self)
    btn_bar = QHBoxLayout()
    self.btn_add = QPushButton("Добавить")
    self.btn_edit = QPushButton("Редактировать")
    self.btn_del = QPushButton("Удалить")
    for b in (self.btn_add, self.btn_edit, self.btn_del):
      btn_bar.addWidget(b)
    btn_bar.addStretch()
    self.layout_.addLayout(btn_bar)
    self.table = QTableWidget()
    self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    self.layout_.addWidget(self.table)
    self.btn_add.clicked.connect(self.on_add)
    self.btn_edit.clicked.connect(self.on_edit)
    self.btn_del.clicked.connect(self.on_delete)
    self.load()

  def selected_id(self):
    row = self.table.currentRow()
    if row < 0:
      return None
    return int(self.table.item(row, 0).text())

  def load(self): pass
  def on_add(self): pass
  def on_edit(self): pass
  def on_delete(self): pass


class ProductsTab(BaseTab):
  HEADERS = ["ID", "Название", "Артикул", "Цена", "Остаток", "Категория", "Поставщик"]

  def load(self):
    rows = self.db.fetchall(
      "SELECT p.id, p.name, p.sku, p.price, p.stock, "
      "COALESCE(c.name,''), COALESCE(s.name,'') "
      "FROM products p "
      "LEFT JOIN categories c ON c.id=p.category_id "
      "LEFT JOIN suppliers s ON s.id=p.supplier_id", ())
    self._fill(self.HEADERS, rows)

  def _fill(self, headers, rows):
    self.table.setColumnCount(len(headers))
    self.table.setHorizontalHeaderLabels(headers)
    self.table.setRowCount(len(rows))
    for r, row in enumerate(rows):
      for c, val in enumerate(row):
        self.table.setItem(r, c, QTableWidgetItem(str(val)))

  def on_add(self):
    dlg = ProductDialog(self.db)
    if dlg.exec():
      self.load()

  def on_edit(self):
    rid = self.selected_id()
    if rid is None:
      return
    row = self.db.fetchone("SELECT * FROM products WHERE id=?", (rid,))
    dlg = ProductDialog(self.db, row)
    if dlg.exec():
      self.load()

  def on_delete(self):
    rid = self.selected_id()
    if rid is None:
      return
    if QMessageBox.question(self, "Удалить", "Удалить товар?") == QMessageBox.StandardButton.Yes:
      self.db.execute("DELETE FROM products WHERE id=?", (rid,))
      self.load()


class OrdersTab(BaseTab):
  HEADERS = ["ID", "Клиент", "Дата", "Статус", "Сумма"]

  def load(self):
    rows = self.db.fetchall(
      "SELECT o.id, COALESCE(c.name,''), o.date, o.status, o.total "
      "FROM orders o LEFT JOIN clients c ON c.id=o.client_id", ())
    self.table.setColumnCount(len(self.HEADERS))
    self.table.setHorizontalHeaderLabels(self.HEADERS)
    self.table.setRowCount(len(rows))
    for r, row in enumerate(rows):
      for c, val in enumerate(row):
        self.table.setItem(r, c, QTableWidgetItem(str(val)))

  def on_add(self):
    dlg = OrderDialog(self.db)
    if dlg.exec():
      self.load()

  def on_edit(self):
    rid = self.selected_id()
    if rid is None:
      return
    row = self.db.fetchone("SELECT * FROM orders WHERE id=?", (rid,))
    dlg = OrderDialog(self.db, row)
    if dlg.exec():
      self.load()

  def on_delete(self):
    rid = self.selected_id()
    if rid is None:
      return
    if QMessageBox.question(self, "Удалить", "Удалить заказ?") == QMessageBox.StandardButton.Yes:
      self.db.execute("DELETE FROM orders WHERE id=?", (rid,))
      self.load()


class ClientsTab(BaseTab):
  HEADERS = ["ID", "Название", "Контакт", "Телефон", "Адрес"]

  def load(self):
    rows = self.db.fetchall("SELECT id,name,contact,phone,address FROM clients", ())
    self.table.setColumnCount(len(self.HEADERS))
    self.table.setHorizontalHeaderLabels(self.HEADERS)
    self.table.setRowCount(len(rows))
    for r, row in enumerate(rows):
      for c, val in enumerate(row):
        self.table.setItem(r, c, QTableWidgetItem(str(val)))

  def on_add(self):
    dlg = ClientDialog(self.db)
    if dlg.exec():
      self.load()

  def on_edit(self):
    rid = self.selected_id()
    if rid is None:
      return
    row = self.db.fetchone("SELECT * FROM clients WHERE id=?", (rid,))
    dlg = ClientDialog(self.db, row)
    if dlg.exec():
      self.load()

  def on_delete(self):
    rid = self.selected_id()
    if rid is None:
      return
    if QMessageBox.question(self, "Удалить", "Удалить клиента?") == QMessageBox.StandardButton.Yes:
      self.db.execute("DELETE FROM clients WHERE id=?", (rid,))
      self.load()


class SuppliersTab(BaseTab):
  HEADERS = ["ID", "Название", "Контакт", "Телефон", "Адрес"]

  def load(self):
    rows = self.db.fetchall("SELECT id,name,contact,phone,address FROM suppliers", ())
    self.table.setColumnCount(len(self.HEADERS))
    self.table.setHorizontalHeaderLabels(self.HEADERS)
    self.table.setRowCount(len(rows))
    for r, row in enumerate(rows):
      for c, val in enumerate(row):
        self.table.setItem(r, c, QTableWidgetItem(str(val)))

  def on_add(self):
    dlg = SupplierDialog(self.db)
    if dlg.exec():
      self.load()

  def on_edit(self):
    rid = self.selected_id()
    if rid is None:
      return
    row = self.db.fetchone("SELECT * FROM suppliers WHERE id=?", (rid,))
    dlg = SupplierDialog(self.db, row)
    if dlg.exec():
      self.load()

  def on_delete(self):
    rid = self.selected_id()
    if rid is None:
      return
    if QMessageBox.question(self, "Удалить", "Удалить поставщика?") == QMessageBox.StandardButton.Yes:
      self.db.execute("DELETE FROM suppliers WHERE id=?", (rid,))
      self.load()


class CategoriesTab(BaseTab):
  HEADERS = ["ID", "Название"]

  def load(self):
    rows = self.db.fetchall("SELECT id,name FROM categories", ())
    self.table.setColumnCount(len(self.HEADERS))
    self.table.setHorizontalHeaderLabels(self.HEADERS)
    self.table.setRowCount(len(rows))
    for r, row in enumerate(rows):
      for c, val in enumerate(row):
        self.table.setItem(r, c, QTableWidgetItem(str(val)))

  def on_add(self):
    dlg = CategoryDialog(self.db)
    if dlg.exec():
      self.load()

  def on_edit(self):
    rid = self.selected_id()
    if rid is None:
      return
    row = self.db.fetchone("SELECT * FROM categories WHERE id=?", (rid,))
    dlg = CategoryDialog(self.db, row)
    if dlg.exec():
      self.load()

  def on_delete(self):
    rid = self.selected_id()
    if rid is None:
      return
    if QMessageBox.question(self, "Удалить", "Удалить категорию?") == QMessageBox.StandardButton.Yes:
      self.db.execute("DELETE FROM categories WHERE id=?", (rid,))
      self.load()
