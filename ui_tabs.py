"""
UI Tabs module for PrakrikaP warehouse management app.
Contains all tab widgets: Products, Orders, Customers, Suppliers, Categories.
Each tab has a unified top action bar.
"""
import csv
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox, QSplitter
)
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt
from dialogs import EntityDialog, OrderViewDialog, SimpleInputDialog


class BaseTab(QWidget):
    """Base class for all tabs with unified top bar and common methods."""
    
    def __init__(self, db, table_name, columns, col_labels, pk_col, pk_name, prefix, parent_win):
        super().__init__()
        self.db = db
        self.table_name = table_name
        self.columns = columns
        self.col_labels = col_labels
        self.pk_col = pk_col
        self.pk_name = pk_name
        self.prefix = prefix
        self.parent_win = parent_win
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self._build_top_bar())
        layout.addWidget(self._build_table())
    
    def _build_top_bar(self):
        bar_widget = QWidget(); bar = QHBoxLayout(bar_widget)
        btn_add = QPushButton(f"Добавить {self.prefix}")
        btn_add.clicked.connect(self.add)
        bar.addWidget(btn_add)
        btn_view = QPushButton(f"Просмотр {self.prefix}")
        btn_view.clicked.connect(self.view)
        bar.addWidget(btn_view)
        btn_edit = QPushButton(f"Изменить {self.prefix}")
        btn_edit.clicked.connect(self.edit)
        bar.addWidget(btn_edit)
        btn_del = QPushButton(f"Удалить {self.prefix}")
        btn_del.clicked.connect(self.delete)
        bar.addWidget(btn_del)
        bar.addStretch()
        btn_imp = QPushButton("Импорт CSV")
        btn_imp.clicked.connect(self.import_csv)
        bar.addWidget(btn_imp)
        btn_exp = QPushButton("Экспорт CSV")
        btn_exp.clicked.connect(self.export_csv)
        bar.addWidget(btn_exp)
        return bar_widget
    
    def _build_table(self):
        table = QTableWidget()
        table.setColumnCount(len(self.columns.split(", ")))
        table.setHorizontalHeaderLabels([self.col_labels.get(c, c) for c in self.columns.split(", ")])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        self.table = table
        self.refresh()
        return table
    
    def _get_selected_row(self):
        rows = self.table.selectedItems()
        return int(self.table.item(rows[0].row(), 0).text()) if rows else None
    
    def _open_entity_dialog(self, row_data=None):
        dlg = EntityDialog(self.parent_win, self.db, self.table_name,
                          self.columns, self.col_labels, self.pk_col, row_data)
        if dlg.exec() == EntityDialog.DialogCode.Accepted and dlg.save():
            self.refresh()
    
    def refresh(self):
        rows = self.db.fetchall(f"SELECT {self.columns} FROM {self.table_name}")
        self.table.setRowCount(0)
        col_list = self.columns.split(", ")
        for r, row in enumerate(rows):
            self.table.insertRow(r)
            for c, col in enumerate(col_list):
                item = QTableWidgetItem(str(row[col]) if row[col] is not None else "")
                self.table.setItem(r, c, item)
    
    def add(self):
        self._open_entity_dialog()
    
    def view(self):
        pid = self._get_selected_row()
        if not pid:
            QMessageBox.warning(self, "Ошибка", f"Выберите {self.prefix}")
            return
        row = self.db.fetchone(f"SELECT {self.columns} FROM {self.table_name} WHERE {self.pk_col} = ?", (pid,))
        if row:
            dlg = EntityDialog(self.parent_win, self.db, self.table_name,
                              self.columns, self.col_labels, self.pk_col, row)
            for field in dlg.fields.values():
                field.setReadOnly(True)
            for btn in dlg.findChildren(QPushButton):
                btn.setText("Закрыть" if btn.text() == "OK" else btn.text())
                btn.clicked.disconnect()
                btn.clicked.connect(dlg.reject)
            dlg.setWindowTitle(f"Просмотр: {self.prefix}")
            dlg.exec()
    
    def edit(self):
        pid = self._get_selected_row()
        if not pid:
            QMessageBox.warning(self, "Ошибка", f"Выберите {self.prefix}")
            return
        row = self.db.fetchone(f"SELECT {self.columns} FROM {self.table_name} WHERE {self.pk_col} = ?", (pid,))
        if row:
            self._open_entity_dialog(row)
    
    def delete(self):
        pid = self._get_selected_row()
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Выберите запись")
            return
        if QMessageBox.question(self, "Подтверждение", f"Удалить {self.prefix} #{pid}?") == QMessageBox.StandardButton.Yes:
            self.db.execute(f"DELETE FROM {self.table_name} WHERE {self.pk_col} = ?", (pid,))
            self.table.model().layoutChanged.emit()
            QMessageBox.information(self, "Успех", "Запись удалена")
            self.refresh()
    
    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, f"Импорт {self.prefix}", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                col_list = self.columns.split(", ")
                for row in reader:
                    vals = [row.get(c.strip(), "") for c in col_list]
                    placeholders = ", ".join(["?" for _ in col_list])
                    self.db.execute(f"INSERT OR IGNORE INTO {self.table_name} ({', '.join(col_list)}) VALUES ({placeholders})", vals)
            QMessageBox.information(self, "Успех", "Импорт завершён")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, f"Экспорт {self.prefix}", f"{self.table_name}.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                col_list = self.columns.split(", ")
                writer.writerow([c.capitalize() for c in col_list])
                for row in self.db.fetchall(f"SELECT {self.columns} FROM {self.table_name}"):
                    writer.writerow([row[c] for c in col_list])
            QMessageBox.information(self, "Успех", "Экспорт завершён")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class ProductsTab(BaseTab):
    """Products tab with stock low coloring."""
    
    def __init__(self, db, parent_win):
        super().__init__(db, "products",
            "product_id, name, sku, category_id, supplier_id, unit, price, stock, min_stock, description",
            {"product_id": "ID", "name": "Название", "sku": "Артикул", "category_id": "Категория",
             "supplier_id": "Поставщик", "unit": "Ед.", "price": "Цена", "stock": "Остаток",
             "min_stock": "Мин. остаток", "description": "Описание"},
            "product_id", "товар", "товар", parent_win)
    
    def refresh(self):
        super().refresh()
        for r in range(self.table.rowCount()):
            stock_item = self.table.item(r, 7)
            min_item = self.table.item(r, 8)
            if stock_item and min_item:
                try:
                    if int(stock_item.text()) <= int(min_item.text()):
                        stock_item.setBackground(QBrush(QColor(255, 200, 200)))
                except ValueError:
                    pass


class OrdersTab(QWidget):
    """Orders tab with top bar and items management."""
    
    def __init__(self, db, parent_win):
        super().__init__()
        self.db = db
        self.parent_win = parent_win
        layout = QVBoxLayout(self)
        layout.addWidget(self._build_top_bar())
        layout.addWidget(self._build_splitter())
    
    def _build_top_bar(self):
                bar_widget = QWidget(); bar = QHBoxLayout(bar_widget)
        btn_add = QPushButton("Добавить заказ")
        btn_add.clicked.connect(self.add)
        bar.addWidget(btn_add)
        btn_view = QPushButton("Просмотр заказа")
        btn_view.clicked.connect(self.view)
        bar.addWidget(btn_view)
        btn_edit = QPushButton("Изменить заказ")
        btn_edit.clicked.connect(self.edit)
        bar.addWidget(btn_edit)
        btn_del = QPushButton("Удалить заказ")
        btn_del.clicked.connect(self.delete)
        bar.addWidget(btn_del)
        btn_items = QPushButton("Товары заказа")
        btn_items.clicked.connect(self.edit_items)
        bar.addWidget(btn_items)
        bar.addStretch()
        btn_imp = QPushButton("Импорт CSV")
        btn_imp.clicked.connect(self.import_csv)
        bar.addWidget(btn_imp)
        btn_exp = QPushButton("Экспорт CSV")
        btn_exp.clicked.connect(self.export_csv)
        bar.addWidget(btn_exp)
                return bar_widget
    
    def _build_splitter(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Клиент", "Дата", "Статус", "Сумма", "Заметки"])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.orders_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.orders_table.setAlternatingRowColors(True)
        self.orders_table.doubleClicked.connect(self.view)
        left_layout.addWidget(self.orders_table)
        
        right = QWidget()
        right_layout = QVBoxLayout(right)
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["ID", "Товар", "Кол-во", "Цена"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.items_table.setAlternatingRowColors(True)
        items_bar = QHBoxLayout()
        btn_add_item = QPushButton("Добавить товар")
        btn_add_item.clicked.connect(self.add_item)
        items_bar.addWidget(btn_add_item)
        btn_del_item = QPushButton("Удалить товар")
        btn_del_item.clicked.connect(self.del_item)
        items_bar.addWidget(btn_del_item)
        right_layout.addLayout(items_bar)
        right_layout.addWidget(self.items_table)
        
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([400, 300])
        return splitter
    
    def _get_selected_order_id(self):
        rows = self.orders_table.selectedItems()
        return int(self.orders_table.item(rows[0].row(), 0).text()) if rows else None
    
    def refresh(self):
        rows = self.db.fetchall("""SELECT o.order_id, c.name as customer, o.order_date, o.status,
            o.total, o.notes FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.customer_id
            ORDER BY o.order_id DESC""")
        self.orders_table.setRowCount(0)
        for r, row in enumerate(rows):
            self.orders_table.insertRow(r)
            for c, val in enumerate([row["order_id"], row["customer"], row["order_date"],
                                     row["status"], str(row["total"]), row["notes"]]):
                self.orders_table.setItem(r, c, QTableWidgetItem(str(val) if val else ""))
        self.refresh_items()
    
    def refresh_items(self):
        oid = self._get_selected_order_id()
        self.items_table.setRowCount(0)
        if oid:
            rows = self.db.fetchall("""SELECT oi.item_id, p.name, oi.quantity, oi.price
                FROM order_items oi JOIN products p ON oi.product_id = p.product_id
                WHERE oi.order_id = ?""", (oid,))
            for r, row in enumerate(rows):
                self.items_table.insertRow(r)
                for c, val in enumerate([row["item_id"], row["name"], row["quantity"], str(row["price"])]):
                    self.items_table.setItem(r, c, QTableWidgetItem(str(val)))
    
    def add(self):
        cols = "customer_id, order_date, status, total, notes"
        labels = {"customer_id": "Клиент ID", "order_date": "Дата", "status": "Статус",
                  "total": "Сумма", "notes": "Заметки"}
        dlg = EntityDialog(self.parent_win, self.db, "orders", cols, labels, "order_id")
        if dlg.exec() == EntityDialog.DialogCode.Accepted and dlg.save():
            self.refresh()
    
    def view(self):
        oid = self._get_selected_order_id()
        if not oid:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ")
            return
        try:
            dlg = OrderViewDialog(self.parent_win, self.db, oid)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def edit(self):
        oid = self._get_selected_order_id()
        if not oid:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ")
            return
        row = self.db.fetchone("SELECT * FROM orders WHERE order_id = ?", (oid,))
        if row:
            cols = "customer_id, order_date, status, total, notes"
            labels = {"customer_id": "Клиент ID", "order_date": "Дата", "status": "Статус",
                      "total": "Сумма", "notes": "Заметки"}
            dlg = EntityDialog(self.parent_win, self.db, "orders", cols, labels, "order_id", row)
            if dlg.exec() == EntityDialog.DialogCode.Accepted and dlg.save():
                self.refresh()
    
    def delete(self):
        oid = self._get_selected_order_id()
        if not oid:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ")
            return
        if QMessageBox.question(self, "Подтверждение", f"Удалить заказ #{oid}?") == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM orders WHERE order_id = ?", (oid,))
            self.orders_table.model().layoutChanged.emit()
            QMessageBox.information(self, "Успех", "Заказ удалён")
            self.refresh()
    
    def edit_items(self):
        oid = self._get_selected_order_id()
        if not oid:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ")
            return
        cols = "order_id, product_id, quantity, price"
        labels = {"order_id": "Заказ ID", "product_id": "Товар ID", "quantity": "Кол-во", "price": "Цена"}
        dlg = EntityDialog(self.parent_win, self.db, "order_items", cols, labels, "item_id")
        if dlg.exec() == EntityDialog.DialogCode.Accepted and dlg.save():
            self.db.recalc_total(oid)
            self.refresh()
    
    def add_item(self):
        oid = self._get_selected_order_id()
        if not oid:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ")
            return
        cols = "order_id, product_id, quantity, price"
        labels = {"order_id": "Заказ ID", "product_id": "Товар ID", "quantity": "Кол-во", "price": "Цена"}
        row_data = {"order_id": oid, "product_id": 1, "quantity": 1, "price": 0}
        dlg = EntityDialog(self.parent_win, self.db, "order_items", cols, labels, "item_id", row_data)
        if dlg.exec() == EntityDialog.DialogCode.Accepted and dlg.save():
            self.db.recalc_total(oid)
            self.refresh()
    
    def del_item(self):
        rows = self.items_table.selectedItems()
        iid = int(self.items_table.item(rows[0].row(), 0).text()) if rows else None
        if not iid:
            QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return
        oid = self._get_selected_order_id()
        if QMessageBox.question(self, "Подтверждение", f"Удалить товар из заказа?") == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM order_items WHERE item_id = ?", (iid,))
            self.db.recalc_total(oid) if oid else None
            self.items_table.model().layoutChanged.emit()
            QMessageBox.information(self, "Успех", "Товар удалён")
            self.refresh()
    
    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Импорт заказы", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    vals = [row.get("order_id", ""), row.get("customer_id", ""),
                            row.get("order_date", ""), row.get("status", "NEW"),
                            row.get("total", "0"), row.get("notes", "")]
                    self.db.execute("INSERT OR IGNORE INTO orders (order_id, customer_id, order_date, status, total, notes) VALUES (?,?,?,?,?,?)", vals)
            QMessageBox.information(self, "Успех", "Импорт завершён")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт заказы", "orders.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Order_id", "Customer_id", "Order_date", "Status", "Total", "Notes"])
                for row in self.db.fetchall("SELECT * FROM orders"):
                    writer.writerow([row["order_id"], row["customer_id"], row["order_date"],
                                     row["status"], row["total"], row["notes"]])
            QMessageBox.information(self, "Успех", "Экспорт завершён")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class CustomersTab(BaseTab):
    """Customers tab."""
    
    def __init__(self, db, parent_win):
        super().__init__(db, "customers",
            "customer_id, name, phone, email, address",
            {"customer_id": "ID", "name": "Имя", "phone": "Телефон",
             "email": "Email", "address": "Адрес"},
            "customer_id", "клиента", "клиент", parent_win)


class SuppliersTab(BaseTab):
    """Suppliers tab."""
    
    def __init__(self, db, parent_win):
        super().__init__(db, "suppliers",
            "supplier_id, name, phone, email, address",
            {"supplier_id": "ID", "name": "Имя", "phone": "Телефон",
             "email": "Email", "address": "Адрес"},
            "supplier_id", "поставщика", "поставщик", parent_win)


class CategoriesTab(BaseTab):
    """Categories tab."""
    
    def __init__(self, db, parent_win):
        super().__init__(db, "categories",
            "category_id, name",
            {"category_id": "ID", "name": "Название"},
            "category_id", "категорию", "категория", parent_win)
