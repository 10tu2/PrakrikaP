"""UI Tabs module for PrakrikaP warehouse management app.
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
        bar_widget = QWidget()
        bar = QHBoxLayout(bar_widget)
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
        col_list = self.columns.split(", ")
        table.setColumnCount(len(col_list))
        table.setHorizontalHeaderLabels([self.col_labels.get(c, c) for c in col_list])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        self.table = table
        self.refresh()
        return table

    def _get_selected_row(self):
        rows = self.table.selectedItems()
        return int(self.table.item(rows[0].row(), 0).text()) if rows else None

    def _get_col_index(self, col_name):
        col_list = self.columns.split(", ")
        try:
            return col_list.index(col_name)
        except ValueError:
            return -1

    def _open_entity_dialog(self, row_data=None):
        try:
            dlg = EntityDialog(self.parent_win, self.db, self.table_name,
                self.columns, self.col_labels, self.pk_col, row_data)
            if dlg.exec() == EntityDialog.DialogCode.Accepted and dlg.save():
                self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть диалог: {e}")

    def refresh(self):
        try:
            rows = self.db.fetchall(f"SELECT {self.columns} FROM {self.table_name}")
        except Exception:
            rows = []
        self.table.setRowCount(0)
        col_list = self.columns.split(", ")
        for r, row in enumerate(rows):
            self.table.insertRow(r)
            for c, col in enumerate(col_list):
                val = row[col] if row[col] is not None else ""
                item = QTableWidgetItem(str(val))
                self.table.setItem(r, c, item)

    def add(self):
        self._open_entity_dialog()

    def view(self):
        pid = self._get_selected_row()
        if not pid:
            QMessageBox.warning(self, "Ошибка", f"Выберите {self.prefix}")
            return
        try:
            row = self.db.fetchone(f"SELECT {self.columns} FROM {self.table_name} WHERE {self.pk_col} = ?", (pid,))
        except Exception:
            row = None
        if row:
            try:
                dlg = EntityDialog(self.parent_win, self.db, self.table_name,
                    self.columns, self.col_labels, self.pk_col, row)
                for field in dlg.fields.values():
                    field.setReadOnly(True)
                for btn in dlg.findChildren(QPushButton):
                    btn.setText("Закрыть" if btn.text() == "OK" else btn.text())
                    try:
                        btn.clicked.disconnect()
                    except Exception:
                        pass
                    btn.clicked.connect(dlg.reject)
                dlg.setWindowTitle(f"Просмотр: {self.prefix}")
                dlg.exec()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def edit(self):
        pid = self._get_selected_row()
        if not pid:
            QMessageBox.warning(self, "Ошибка", f"Выберите {self.prefix}")
            return
        try:
            row = self.db.fetchone(f"SELECT {self.columns} FROM {self.table_name} WHERE {self.pk_col} = ?", (pid,))
        except Exception:
            row = None
        if row:
            self._open_entity_dialog(row)

    def delete(self):
        pid = self._get_selected_row()
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Выберите запись")
            return
        if QMessageBox.question(self, "Подтверждение", f"Удалить {self.prefix} #{pid}?") == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute(f"DELETE FROM {self.table_name} WHERE {self.pk_col} = ?", (pid,))
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
                return
            self.refresh()
            QMessageBox.information(self, "Успех", "Запись удалена")

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
                    self.db.execute(f"INSERT INTO {self.table_name} ({', '.join(col_list)}) VALUES ({placeholders})", vals)
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
                rows = self.db.fetchall(f"SELECT {self.columns} FROM {self.table_name}")
                for row in rows:
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
            stock_col = self._get_col_index("stock")
            min_stock_col = self._get_col_index("min_stock")
            if stock_col >= 0 and min_stock_col >= 0:
                stock_item = self.table.item(r, stock_col)
                min_item = self.table.item(r, min_stock_col)
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
        self.current_order_id = None
        layout = QVBoxLayout(self)
        layout.addWidget(self._build_top_bar())
        layout.addWidget(self._build_splitter())

    def _build_top_bar(self):
        bar_widget = QWidget()
        bar = QHBoxLayout(bar_widget)
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
        self.orders_table.clicked.connect(self.on_order_selected)
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
        if not rows:
            return None
        try:
            return int(self.orders_table.item(rows[0].row(), 0).text())
        except (ValueError, IndexError):
            return None

    def on_order_selected(self):
        self.refresh_items()

    def refresh(self):
        try:
            rows = self.db.fetchall(
                "SELECT o.order_id, c.name as customer, o.order_date, "
                "o.status, o.total, o.notes FROM orders o "
                "LEFT JOIN customers c ON o.customer_id = c.customer_id "
                "ORDER BY o.order_id DESC")
        except Exception:
            rows = []
        self.orders_table.setRowCount(0)
        for r, row in enumerate(rows):
            self.orders_table.insertRow(r)
            for c, val in enumerate([
                    row["order_id"], row["customer"], row["order_date"],
                    row["status"], str(row["total"]) if row["total"] else "0",
                    row["notes"]]):
                self.orders_table.setItem(r, c, QTableWidgetItem(str(val) if val else ""))
        self.refresh_items()

    def refresh_items(self):
        self.items_table.setRowCount(0)
        oid = self._get_selected_order_id()
        self.current_order_id = oid
        if oid:
            try:
                rows = self.db.fetchall(
                    "SELECT oi.item_id, p.name, oi.quantity, oi.price "
                    "FROM order_items oi "
                    "JOIN products p ON oi.product_id = p.product_id "
                    "WHERE oi.order_id = ?", (oid,))
            except Exception:
                rows = []
            for r, row in enumerate(rows):
                self.items_table.insertRow(r)
                for c, val in enumerate([
                        row["item_id"], row["name"], row["quantity"],
                        str(row["price"]) if row["price"] else "0"]):
                    self.items_table.setItem(r, c, QTableWidgetItem(str(val)))

    def add(self):
        cols = "customer_id, order_date, status, notes"
        labels = {"customer_id": "Клиент ID", "order_date": "Дата",
                  "status": "Статус", "notes": "Заметки"}
        try:
            now_res = self.db.fetchone("SELECT date('now')")
            row_data = {"order_date": now_res[0] if now_res else ""}
        except Exception:
            row_data = {"order_date": ""}
        try:
            dlg = EntityDialog(self.parent_win, self.db, "orders",
                cols, labels, "order_id", row_data)
            if dlg.exec() == EntityDialog.DialogCode.Accepted and dlg.save():
                self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

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
        try:
            row = self.db.fetchone(
                "SELECT * FROM orders WHERE order_id = ?", (oid,))
        except Exception:
            row = None
        if row:
            cols = "customer_id, order_date, status, total, notes"
            labels = {"customer_id": "Клиент ID", "order_date": "Дата",
                      "status": "Статус", "total": "Сумма", "notes": "Заметки"}
            try:
                dlg = EntityDialog(self.parent_win, self.db, "orders",
                    cols, labels, "order_id", row)
                if dlg.exec() == EntityDialog.DialogCode.Accepted and dlg.save():
                    self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def delete(self):
        oid = self._get_selected_order_id()
        if not oid:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ")
            return
        if QMessageBox.question(self, "Подтверждение", f"Удалить заказ #{oid}?") == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute("DELETE FROM orders WHERE order_id = ?", (oid,))
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
                return
            self.refresh()
            QMessageBox.information(self, "Успех", "Заказ удалён")

    def edit_items(self):
        oid = self._get_selected_order_id()
        if not oid:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ")
            return
        try:
            products = self.db.fetchall("SELECT product_id, name FROM products")
        except Exception:
            products = []
        if not products:
            QMessageBox.warning(self, "Ошибка", "Нет продуктов в базе. Добавьте продукты.")
            return
        product_ids = ", ".join(str(p["product_id"]) for p in products)
        pid_dlg = SimpleInputDialog(
            self, "Добавить товар", f"ID продукта ({product_ids}):", "Введите ID товара")
        if pid_dlg.exec() != pid_dlg.DialogCode.Accepted:
            return
        try:
            product_id = int(pid_dlg.get_text())
            prod = self.db.fetchone(
                "SELECT name FROM products WHERE product_id = ?", (product_id,))
            if not prod:
                QMessageBox.warning(self, "Ошибка", "Продукт не найден")
                return
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Ошибка", "Некорректный ID товара")
            return
        qty_dlg = SimpleInputDialog(
            self, "Кол-во", "Количество:", "Введите количество")
        if qty_dlg.exec() != qty_dlg.DialogCode.Accepted:
            return
        try:
            quantity = int(qty_dlg.get_text())
            if quantity <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Ошибка", "Некорректное количество")
            return
        price_dlg = SimpleInputDialog(
            self, "Цена", "Цена за единицу:", "Введите цену")
        if price_dlg.exec() != price_dlg.DialogCode.Accepted:
            return
        try:
            price = float(price_dlg.get_text())
            if price < 0:
                raise ValueError()
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Ошибка", "Некорректная цена")
            return
        try:
            self.db.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price) "
                "VALUES (?, ?, ?, ?)", (oid, product_id, quantity, price))
            self.db.recalc_total(oid)
            self.refresh()
            QMessageBox.information(self, "Успех", "Товар добавлен")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def add_item(self):
        self.edit_items()

    def del_item(self):
        rows = self.items_table.selectedItems()
        iid = int(self.items_table.item(rows[0].row(), 0).text()) if rows else None
        if not iid:
            QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return
        oid = self._get_selected_order_id()
        if QMessageBox.question(self, "Подтверждение", "Удалить товар из заказа?") == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute(
                    "DELETE FROM order_items WHERE item_id = ?", (iid,))
                if oid:
                    self.db.recalc_total(oid)
                    self.refresh()
                QMessageBox.information(self, "Успех", "Товар удалён")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Импорт заказы", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        now_res = self.db.fetchone("SELECT date('now')")
                        default_date = now_res[0] if now_res else ""
                    except Exception:
                        default_date = ""
                    vals = [
                        row.get("customer_id", "1"),
                        row.get("order_date", default_date),
                        row.get("status", "NEW"),
                        row.get("notes", "")
                    ]
                    self.db.execute(
                        "INSERT INTO orders (customer_id, order_date, status, notes) "
                        "VALUES (?,?,?,?)", vals)
            QMessageBox.information(self, "Успех", "Импорт завершён")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт заказы", "orders.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["Order_id", "Customer_id", "Order_date", "Status", "Total", "Notes"])
                try:
                    rows = self.db.fetchall("SELECT * FROM orders")
                except Exception:
                    rows = []
                for row in rows:
                    writer.writerow([
                        row["order_id"], row["customer_id"], row["order_date"],
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
