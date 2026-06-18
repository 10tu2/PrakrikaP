import sqlite3
import csv
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout,
    QLineEdit, QTextEdit, QSpinBox, QComboBox, QMessageBox, QDialog,
    QDateEdit, QLabel, QFrame, QGroupBox, QFileDialog, QSplitter
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QBrush

DB_FILE = "trade_store.db"

class Database:
    def __init__(self, path=DB_FILE):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.init_db()
        self.seed()

    def execute(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()
        return cur

    def fetchall(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def fetchone(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchone()

    def init_db(self):
        self.execute("""CREATE TABLE IF NOT EXISTS categories(
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )""")
        self.execute("""CREATE TABLE IF NOT EXISTS suppliers(
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            address TEXT DEFAULT ''
        )""")
        self.execute("""CREATE TABLE IF NOT EXISTS customers(
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            address TEXT DEFAULT ''
        )""")
        self.execute("""CREATE TABLE IF NOT EXISTS products(
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT UNIQUE,
            category_id INTEGER REFERENCES categories(category_id),
            supplier_id INTEGER REFERENCES suppliers(supplier_id),
            unit TEXT DEFAULT 'шт',
            price REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 0,
            description TEXT DEFAULT ''
        )""")
        self.execute("""CREATE TABLE IF NOT EXISTS orders(
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER REFERENCES customers(customer_id),
            order_date TEXT DEFAULT CURRENT_DATE,
            status TEXT DEFAULT 'NEW',
            total REAL DEFAULT 0,
            notes TEXT DEFAULT ''
        )""")
        self.execute("""CREATE TABLE IF NOT EXISTS order_items(
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(product_id),
            quantity INTEGER DEFAULT 1,
            price REAL DEFAULT 0
        )""")

    def seed(self):
        if not self.fetchone("SELECT 1 FROM categories"):
            self.execute("INSERT INTO categories (name) VALUES ('Общее')")
        if not self.fetchone("SELECT 1 FROM suppliers"):
            self.execute("INSERT INTO suppliers (name) VALUES ('Общий поставщик')")

    def recalc_total(self, order_id):
        res = self.fetchone("""SELECT COALESCE(SUM(quantity * price), 0) as total
                               FROM order_items WHERE order_id = ?""", (order_id,))
        self.execute("UPDATE orders SET total = ? WHERE order_id = ?", (res['total'], order_id))

    def close(self):
        self.conn.close()

class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Практика П - Управление складом")
        self.resize(1000, 700)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.addTab(self.products_tab(), "Товары")
        self.tabs.addTab(self.orders_tab(), "Заказы")
        self.tabs.addTab(self.customers_tab(), "Клиенты")
        self.tabs.addTab(self.suppliers_tab(), "Поставщики")
        self.tabs.addTab(self.categories_tab(), "Категории")
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        tab = self.centralWidget().widget(index)
        if hasattr(tab, 'refresh'):
            tab.refresh()

    def get_selected_row(self, table):
        rows = table.selectedItems()
        return int(table.item(rows[0].row(), 0).text()) if rows else None

    def refresh_categories(self):
        self.prod_category.clear()
        self.prod_category.addItem("Все категории", 0)
        for row in self.db.fetchall("SELECT category_id, name FROM categories ORDER BY name"):
            self.prod_category.addItem(row['name'], row['category_id'])

    def refresh_products(self):
        self.prod_table.setRowCount(0)
        search = self.prod_search.text().strip()
        cat_id = self.prod_category.currentData()
        sql = """SELECT p.product_id, p.name, p.sku, c.name, p.price, p.stock, p.min_stock, p.unit
                 FROM products p LEFT JOIN categories c ON p.category_id = c.category_id WHERE 1=1"""
        params = []
        if search:
            sql += " AND (p.name LIKE ? OR p.sku LIKE ?)"
            params.extend(['%' + search + '%', '%' + search + '%'])
        if cat_id and cat_id != 0:
            sql += " AND p.category_id = ?"
            params.append(cat_id)
        sql += " ORDER BY p.name"
        for row in self.db.fetchall(sql, params):
            r = self.prod_table.rowCount()
            self.prod_table.insertRow(r)
            for c, val in enumerate(row):
                self.prod_table.setItem(r, c, QTableWidgetItem(str(val if val is not None else '')))

    def refresh_categories_combo(self, combo):
        combo.clear()
        combo.addItem("", None)
        for row in self.db.fetchall("SELECT category_id, name FROM categories ORDER BY name"):
            combo.addItem(row['name'], row['category_id'])

    def refresh_suppliers_combo(self, combo):
        combo.clear()
        combo.addItem("", None)
        for row in self.db.fetchall("SELECT supplier_id, name FROM suppliers ORDER BY name"):
            combo.addItem(row['name'], row['supplier_id'])

    def refresh_customers_combo(self, combo):
        combo.clear()
        combo.addItem("", None)
        for row in self.db.fetchall("SELECT customer_id, name FROM customers ORDER BY name"):
            combo.addItem(row['name'], row['customer_id'])

    def refresh_products_combo(self, combo):
        combo.clear()
        combo.addItem("", None)
        for row in self.db.fetchall("SELECT product_id, name, price FROM products ORDER BY name"):
            combo.addItem(f"{row['name']} ({row['price']})", row['product_id'])

    def refresh_orders(self):
        self.order_table.setRowCount(0)
        cust = self.order_customer.currentData()
        sql = """SELECT o.order_id, c.name, o.order_date, o.status, o.total
                 FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id"""
        params = []
        if cust:
            sql += " WHERE o.customer_id = ?"
            params.append(cust)
        sql += " ORDER BY o.order_date DESC"
        for row in self.db.fetchall(sql, params):
            r = self.order_table.rowCount()
            self.order_table.insertRow(r)
            for c, val in enumerate(row):
                self.order_table.setItem(r, c, QTableWidgetItem(str(val if val else '')))

    def refresh_customers(self):
        self.cust_table.setRowCount(0)
        search = self.cust_search.text().strip()
        sql = "SELECT customer_id, name, phone, email, address FROM customers"
        params = []
        if search:
            sql += " WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?"
            params = ['%' + search + '%'] * 3
        sql += " ORDER BY name"
        for row in self.db.fetchall(sql, params):
            r = self.cust_table.rowCount()
            self.cust_table.insertRow(r)
            for c, val in enumerate(row):
                self.cust_table.setItem(r, c, QTableWidgetItem(str(val if val is not None else '')))

    def refresh_suppliers(self):
        self.sup_table.setRowCount(0)
        search = self.sup_search.text().strip()
        sql = "SELECT supplier_id, name, phone, email, address FROM suppliers"
        params = []
        if search:
            sql += " WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?"
            params = ['%' + search + '%'] * 3
        sql += " ORDER BY name"
        for row in self.db.fetchall(sql, params):
            r = self.sup_table.rowCount()
            self.sup_table.insertRow(r)
            for c, val in enumerate(row):
                self.sup_table.setItem(r, c, QTableWidgetItem(str(val if val is not None else '')))

    def _refresh_categories_table(self, table):
        table.setRowCount(0)
        for row in self.db.fetchall("SELECT category_id, name FROM categories ORDER BY name"):
            r = table.rowCount()
            table.insertRow(r)
            table.setItem(r, 0, QTableWidgetItem(str(row['category_id'])))
            table.setItem(r, 1, QTableWidgetItem(row['name']))

    def open_product_dialog(self, product_id=None):
        dlg = QDialog(self)
        dlg.setWindowTitle("Добавить товар" if not product_id else "Редактировать товар")
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        name = QLineEdit()
        sku = QLineEdit()
        cat = QComboBox()
        self.refresh_categories_combo(cat)
        sup = QComboBox()
        self.refresh_suppliers_combo(sup)
        unit = QLineEdit("шт")
        price = QLineEdit("0")
        stock = QLineEdit("0")
        min_stock = QLineEdit("0")
        desc = QTextEdit()
        desc.setMaximumHeight(80)
        form.addRow("Название:", name)
        form.addRow("SKU:", sku)
        form.addRow("Категория:", cat)
        form.addRow("Поставщик:", sup)
        form.addRow("Ед.:", unit)
        form.addRow("Цена:", price)
        form.addRow("Остаток:", stock)
        form.addRow("Мин. остаток:", min_stock)
        form.addRow("Описание:", desc)
        layout.addLayout(form)
        if product_id:
            row = self.db.fetchone("SELECT * FROM products WHERE product_id = ?", (product_id,))
            if row:
                name.setText(row['name'] or '')
                sku.setText(row['sku'] or '')
                cat.setCurrentIndex(cat.findData(row['category_id']))
                sup.setCurrentIndex(sup.findData(row['supplier_id']))
                unit.setText(row['unit'] or '')
                price.setText(str(row['price'] or 0))
                stock.setText(str(row['stock'] or 0))
                min_stock.setText(str(row['min_stock'] or 0))
                desc.setText(row['description'] or '')
        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(dlg.accept)
        btns.addWidget(btn_ok)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(dlg.reject)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if not name.text().strip():
                QMessageBox.warning(self, "Ошибка", "Укажите название")
                return
            try:
                p = float(price.text() or 0)
                s = int(stock.text() or 0)
                ms = int(min_stock.text() or 0)
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Некорректные числовые данные")
                return
            if product_id:
                self.db.execute("""UPDATE products SET name=?, sku=?, category_id=?, supplier_id=?, unit=?, price=?, stock=?, min_stock=?, description=? WHERE product_id=?""",
                                (name.text(), sku.text(), cat.currentData(), sup.currentData(), unit.text(), p, s, ms, desc.toPlainText(), product_id))
                QMessageBox.information(self, "Успех", "Товар обновлён")
            else:
                self.db.execute("""INSERT INTO products (name, sku, category_id, supplier_id, unit, price, stock, min_stock, description) VALUES (?,?,?,?,?,?,?,?,?)""",
                                (name.text(), sku.text(), cat.currentData(), sup.currentData(), unit.text(), p, s, ms, desc.toPlainText()))
                QMessageBox.information(self, "Успех", "Товар добавлен")
            self.refresh_products()

    def view_product(self):
        pid = self.get_selected_row(self.prod_table)
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return
        row = self.db.fetchone("SELECT * FROM products WHERE product_id = ?", (pid,))
        if row:
            info = f"ID: {row['product_id']}\nНазвание: {row['name']}\nSKU: {row['sku']}\nЕд.: {row['unit']}\nЦена: {row['price']}\nОстаток: {row['stock']}\nМин. остаток: {row['min_stock']}\nОписание: {row['description']}"
            QMessageBox.information(self, f"Товар {row['name']}", info)

    def delete_product(self):
        pid = self.get_selected_row(self.prod_table)
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return
        row = self.db.fetchone("SELECT name FROM products WHERE product_id = ?", (pid,))
        if not row: return
        if QMessageBox.question(self, "Подтверждение", f"Удалить '{row['name']}'?") == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM products WHERE product_id = ?", (pid,))
            self.refresh_products()
            QMessageBox.information(self, "Успех", "Товар удалён")

    def stock_movement(self):
        pid = self.get_selected_row(self.prod_table)
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return
        row = self.db.fetchone("SELECT name, stock FROM products WHERE product_id = ?", (pid,))
        if not row: return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Движение: {row['name']}")
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        typ = QComboBox()
        typ.addItem("Приход", 1)
        typ.addItem("Расход", -1)
        qty = QLineEdit()
        form.addRow("Тип:", typ)
        form.addRow("Количество:", qty)
        layout.addLayout(form)
        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(dlg.accept)
        btns.addWidget(btn_ok)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(dlg.reject)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                q = int(qty.text())
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Некорректное число")
                return
            t = typ.currentData()
            new_stock = row['stock'] + (t * q)
            if new_stock < 0:
                QMessageBox.warning(self, "Ошибка", "Недостаточно на складе")
                return
            self.db.execute("UPDATE products SET stock = ? WHERE product_id = ?", (new_stock, pid))
            self.refresh_products()
            QMessageBox.information(self, "Успех", f"Новый остаток: {new_stock}")

    def import_products(self):
        path, _ = QFileDialog.getOpenFileName(self, "Импорт CSV", "", "CSV Files (*.csv)")
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cat_name = row.get('category', 'Общее')
                    cat = self.db.fetchone("SELECT category_id FROM categories WHERE name = ?", (cat_name,))
                    cat_id = cat['category_id'] if cat else None
                    sup_name = row.get('supplier', 'Общий поставщик')
                    sup = self.db.fetchone("SELECT supplier_id FROM suppliers WHERE name = ?", (sup_name,))
                    sup_id = sup['supplier_id'] if sup else None
                    self.db.execute("""INSERT OR IGNORE INTO products (name, sku, category_id, supplier_id, unit, price, stock, min_stock, description)
                                       VALUES (?,?,?,?,?,?,?,?,?)""",
                                    (row.get('name', ''), row.get('sku', ''), cat_id, sup_id, row.get('unit', 'шт'),
                                     float(row.get('price', 0)), int(row.get('stock', 0)), int(row.get('min_stock', 0)), row.get('description', '')))
                self.refresh_products()
                QMessageBox.information(self, "Успех", "Импорт завершён")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def export_products(self):
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт CSV", "products.csv", "CSV Files (*.csv)")
        if not path: return
        try:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Название', 'SKU', 'Категория', 'Поставщик', 'Ед.', 'Цена', 'Остаток', 'Мин. остаток', 'Описание'])
                for row in self.db.fetchall("""SELECT p.product_id, p.name, p.sku, c.name as cat, s.name as sup, p.unit, p.price, p.stock, p.min_stock, p.description
                                               FROM products p LEFT JOIN categories c ON p.category_id = c.category_id LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id"""):
                    writer.writerow([row['product_id'], row['name'], row['sku'], row['cat'], row['sup'], row['unit'], row['price'], row['stock'], row['min_stock'], row['description']])
                QMessageBox.information(self, "Успех", "Экспорт завершён")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _add_category(self, name, field):
        if not name.strip():
            QMessageBox.warning(self, "Ошибка", "Укажите название")
            return
        try:
            self.db.execute("INSERT INTO categories (name) VALUES (?)", (name.strip(),))
            QMessageBox.information(self, "Успех", "Категория добавлена")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Ошибка", "Категория уже существует")
        else:
            field.clear()

    def _del_category(self, table):
        rows = table.selectedItems()
        if not rows:
            QMessageBox.warning(self, "Ошибка", "Выберите категорию")
            return
        cid = int(table.item(rows[0].row(), 0).text())
        name = table.item(rows[0].row(), 1).text()
        cnt = self.db.fetchone("SELECT COUNT(*) as n FROM products WHERE category_id = ?", (cid,))
        if cnt and cnt['n'] > 0:
            QMessageBox.warning(self, "Ошибка", f"Невозможно удалить: используется в {cnt['n']} товарах")
            return
        if QMessageBox.question(self, "Подтверждение", f"Удалить '{name}'?") == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM categories WHERE category_id = ?", (cid,))
            self._refresh_categories_table(table)
            self.refresh_categories()
            QMessageBox.information(self, "Успех", "Категория удалена")

    def manage_categories(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Категории")
        layout = QVBoxLayout(dlg)
        bar = QHBoxLayout()
        name = QLineEdit()
        bar.addWidget(name)
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(lambda: self._add_category(name.text(), name))
        bar.addWidget(btn_add)
        layout.addLayout(bar)
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["ID", "Название"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(table)
        btns = QHBoxLayout()
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(lambda: self._del_category(table))
        btns.addWidget(btn_del)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(dlg.accept)
        btns.addWidget(btn_close)
        layout.addLayout(btns)
        self._refresh_categories_table(table)
        dlg.exec()

    def products_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        # ALL buttons on TOP
        bar = QHBoxLayout()
        self.prod_search = QLineEdit()
        self.prod_search.setPlaceholderText("Поиск по названию или SKU...")
        self.prod_search.textChanged.connect(self.refresh_products)
        bar.addWidget(self.prod_search)
        self.prod_category = QComboBox()
        self.prod_category.addItem("Все категории", 0)
        self.refresh_categories()
        self.prod_category.currentIndexChanged.connect(self.refresh_products)
        bar.addWidget(self.prod_category)
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(lambda: self.open_product_dialog())
        bar.addWidget(btn_add)
        btn_view = QPushButton("Просмотр")
        btn_view.clicked.connect(self.view_product)
        bar.addWidget(btn_view)
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self.edit_product)
        bar.addWidget(btn_edit)
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self.delete_product)
        bar.addWidget(btn_del)
        btn_stock = QPushButton("Движение товара")
        btn_stock.clicked.connect(self.stock_movement)
        bar.addWidget(btn_stock)
        btn_cat = QPushButton("Категории")
        btn_cat.clicked.connect(self.manage_categories)
        bar.addWidget(btn_cat)
        btn_import = QPushButton("Импорт CSV")
        btn_import.clicked.connect(self.import_products)
        bar.addWidget(btn_import)
        btn_export = QPushButton("Экспорт CSV")
        btn_export.clicked.connect(self.export_products)
        bar.addWidget(btn_export)
        layout.addLayout(bar)
        # Table
        self.prod_table = QTableWidget()
        self.prod_table.setColumnCount(8)
        self.prod_table.setHorizontalHeaderLabels(["ID", "Название", "SKU", "Категория", "Цена", "Остаток", "Мин. остаток", "Ед."])
        self.prod_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.prod_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # double-click to edit
        self.prod_table.doubleClicked.connect(self.edit_product)
        layout.addWidget(self.prod_table)
        self.refresh_categories()
        self.refresh_products()
        return w

    def edit_product(self):
        pid = self.get_selected_row(self.prod_table)
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return
        self.open_product_dialog(pid)

    def open_order_dialog(self, order_id=None):
        dlg = QDialog(self)
        dlg.setWindowTitle("Новый заказ" if not order_id else "Заказ")
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        cust = QComboBox()
        self.refresh_customers_combo(cust)
        date = QDateEdit(QDate.currentDate())
        status = QComboBox()
        status.addItem("Новый", "NEW")
        status.addItem("В работе", "WORK")
        status.addItem("Выполнен", "DONE")
        status.addItem("Отменён", "CANCEL")
        notes = QTextEdit()
        notes.setMaximumHeight(60)
        form.addRow("Клиент:", cust)
        form.addRow("Дата:", date)
        form.addRow("Статус:", status)
        form.addRow("Заметки:", notes)
        layout.addLayout(form)
        if order_id:
            row = self.db.fetchone("SELECT * FROM orders WHERE order_id = ?", (order_id,))
            if row:
                cust.setCurrentIndex(cust.findData(row['customer_id']))
                date.setDate(QDate.fromString(row['order_date'], 'yyyy-MM-dd'))
                idx = status.findData(row['status'])
                if idx >= 0: status.setCurrentIndex(idx)
                notes.setText(row['notes'] or '')
        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(dlg.accept)
        btns.addWidget(btn_ok)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(dlg.reject)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)
        if order_id:
            items_btn = QPushButton("Товары заказа")
            items_btn.clicked.connect(lambda: self.edit_order_items(order_id, dlg))
            layout.addWidget(items_btn)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            cust_id = cust.currentData()
            if not cust_id:
                QMessageBox.warning(self, "Ошибка", "Выберите клиента")
                return
            if order_id:
                self.db.execute("""UPDATE orders SET customer_id=?, order_date=?, status=?, notes=? WHERE order_id=?""",
                                (cust_id, date.date().toString('yyyy-MM-dd'), status.currentData(), notes.toPlainText(), order_id))
                QMessageBox.information(self, "Успех", "Заказ обновлён")
            else:
                cur = self.db.execute("""INSERT INTO orders (customer_id, order_date, status, notes) VALUES (?,?,?,?)""",
                                      (cust_id, date.date().toString('yyyy-MM-dd'), status.currentData(), notes.toPlainText()))
                order_id = cur.lastrowid
                QMessageBox.information(self, "Успех", "Заказ создан")
            self.refresh_orders()
            if order_id: self.edit_order_items(order_id, dlg)

    def edit_order_items(self, order_id, parent_dlg):
        dlg = QDialog(parent_dlg)
        dlg.setWindowTitle("Товары заказа")
        layout = QVBoxLayout(dlg)
        bar = QHBoxLayout()
        prod = QComboBox()
        self.refresh_products_combo(prod)
        bar.addWidget(prod)
        qty = QLineEdit("1")
        qty.setMinimumWidth(60)
        bar.addWidget(qty)
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(lambda: self._add_order_item(order_id, prod, qty, table))
        bar.addWidget(btn_add)
        layout.addLayout(bar)
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Товар", "Количество", "Цена", "Сумма"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(table)
        btns = QHBoxLayout()
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(lambda: self._del_order_item(order_id, table))
        btns.addWidget(btn_del)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(dlg.accept)
        btns.addWidget(btn_close)
        layout.addLayout(btns)
        self._refresh_order_items(order_id, table)
        dlg.exec()

    def _refresh_order_items(self, order_id, table):
        table.setRowCount(0)
        for row in self.db.fetchall("""SELECT oi.item_id, p.name, oi.quantity, oi.price, oi.quantity * oi.price as subtotal
                                       FROM order_items oi JOIN products p ON oi.product_id = p.product_id
                                       WHERE oi.order_id = ?""", (order_id,)):
            r = table.rowCount()
            table.insertRow(r)
            table.setItem(r, 0, QTableWidgetItem(row['name']))
            table.setItem(r, 1, QTableWidgetItem(str(row['quantity'])))
            table.setItem(r, 2, QTableWidgetItem(f"{row['price']:.2f}"))
            table.setItem(r, 3, QTableWidgetItem(f"{row['subtotal']:.2f}"))
            table.item(r, 3).setForeground(QBrush(QColor(0, 128, 0)))
        self.db.recalc_total(order_id)
        self.refresh_orders()

    def _add_order_item(self, order_id, prod, qty, table):
        pid = prod.currentData()
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return
        try:
            q = int(qty.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Некорректное количество")
            return
        row = self.db.fetchone("SELECT price, stock FROM products WHERE product_id = ?", (pid,))
        if not row: return
        if q > row['stock']:
            QMessageBox.warning(self, "Ошибка", "Недостаточно на складе")
            return
        self.db.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?,?,?,?)", (order_id, pid, q, row['price']))
        self._refresh_order_items(order_id, table)
        QMessageBox.information(self, "Успех", "Товар добавлен")

    def _del_order_item(self, order_id, table):
        rows = table.selectedItems()
        if not rows:
            QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return
        iid = self.db.fetchone("SELECT item_id FROM order_items WHERE order_id = ? LIMIT 1 OFFSET ?", (order_id, rows[0].row()))
        if iid:
            self.db.execute("DELETE FROM order_items WHERE item_id = ?", (iid['item_id'],))
            self._refresh_order_items(order_id, table)
            QMessageBox.information(self, "Успех", "Товар удалён")

    def view_order(self):
        oid = self.get_selected_row(self.order_table)
        if not oid:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ")
            return
        row = self.db.fetchone("SELECT o.*, c.name FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id WHERE o.order_id = ?", (oid,))
        if row:
            info = f"ID: {row['order_id']}\nКлиент: {row['name']}\nДата: {row['order_date']}\nСтатус: {row['status']}\nСумма: {row['total']:.2f}\nЗаметки: {row['notes']}"
            items = self.db.fetchall("""SELECT p.name, oi.quantity, oi.price, oi.quantity * oi.price as subtotal
                                        FROM order_items oi JOIN products p ON oi.product_id = p.product_id
                                        WHERE oi.order_id = ?""", (oid,))
            if items:
                info += "\n\nТовары:\n"
                for i in items:
                    info += f" {i['name']} x{i['quantity']} = {i['subtotal']:.2f}\n"
            QMessageBox.information(self, f"Заказ #{oid}", info)

    def delete_order(self):
        oid = self.get_selected_row(self.order_table)
        if not oid:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ")
            return
        if QMessageBox.question(self, "Подтверждение", f"Удалить заказ #{oid}?") == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM orders WHERE order_id = ?", (oid,))
            self.refresh_orders()
            QMessageBox.information(self, "Успех", "Заказ удалён")

    def export_orders(self):
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт CSV", "orders.csv", "CSV Files (*.csv)")
        if not path: return
        try:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Клиент', 'Дата', 'Статус', 'Сумма'])
                for row in self.db.fetchall("""SELECT o.order_id, c.name, o.order_date, o.status, o.total
                                               FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id ORDER BY o.order_date DESC"""):
                    writer.writerow([row['order_id'], row['name'], row['order_date'], row['status'], row['total']])
                QMessageBox.information(self, "Успех", "Экспорт завершён")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def orders_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        # ALL buttons on TOP
        bar = QHBoxLayout()
        bar.addWidget(QLabel("Клиент:"))
        self.order_customer = QComboBox()
        self.refresh_customers_combo(self.order_customer)
        bar.addWidget(self.order_customer)
        btn_new = QPushButton("Новый заказ")
        btn_new.clicked.connect(lambda: self.open_order_dialog())
        bar.addWidget(btn_new)
        btn_view = QPushButton("Просмотр")
        btn_view.clicked.connect(self.view_order)
        bar.addWidget(btn_view)
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self.delete_order)
        bar.addWidget(btn_del)
        btn_export = QPushButton("Экспорт CSV")
        btn_export.clicked.connect(self.export_orders)
        bar.addWidget(btn_export)
        layout.addLayout(bar)
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(5)
        self.order_table.setHorizontalHeaderLabels(["ID", "Клиент", "Дата", "Статус", "Сумма"])
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.order_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.order_table.doubleClicked.connect(self.open_order_dialog)
        layout.addWidget(self.order_table)
        self.refresh_orders()
        return w

    def customers_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        # ALL buttons on TOP
        bar = QHBoxLayout()
        self.cust_search = QLineEdit()
        self.cust_search.setPlaceholderText("Поиск...")
        self.cust_search.textChanged.connect(self.refresh_customers)
        bar.addWidget(self.cust_search)
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(lambda: self._open_entity_dialog("customers", "customer_id", "client", None))
        bar.addWidget(btn_add)
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(lambda: self._edit_entity("customers", "customer_id", "customer_id", self.cust_table, "client"))
        bar.addWidget(btn_edit)
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(lambda: self._del_entity("customers", "customer_id", "Клиенты", self.cust_table))
        bar.addWidget(btn_del)
        btn_export = QPushButton("Экспорт CSV")
        btn_export.clicked.connect(lambda: self._export_entity("customers", "name, phone, email, address", "Клиенты"))
        bar.addWidget(btn_export)
        layout.addLayout(bar)
        self.cust_table = QTableWidget()
        self.cust_table.setColumnCount(5)
        self.cust_table.setHorizontalHeaderLabels(["ID", "Название", "Телефон", "Email", "Адрес"])
        self.cust_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cust_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.cust_table)
        self.refresh_customers()
        w.refresh = lambda: self.refresh_customers()
        return w

    def suppliers_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        # ALL buttons on TOP
        bar = QHBoxLayout()
        self.sup_search = QLineEdit()
        self.sup_search.setPlaceholderText("Поиск...")
        self.sup_search.textChanged.connect(self.refresh_suppliers)
        bar.addWidget(self.sup_search)
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(lambda: self._open_entity_dialog("suppliers", "supplier_id", "supplier", None))
        bar.addWidget(btn_add)
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(lambda: self._edit_entity("suppliers", "supplier_id", "supplier_id", self.sup_table, "supplier"))
        bar.addWidget(btn_edit)
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(lambda: self._del_entity("suppliers", "supplier_id", "Поставщики", self.sup_table))
        bar.addWidget(btn_del)
        btn_export = QPushButton("Экспорт CSV")
        btn_export.clicked.connect(lambda: self._export_entity("suppliers", "name, phone, email, address", "Поставщики"))
        bar.addWidget(btn_export)
        layout.addLayout(bar)
        self.sup_table = QTableWidget()
        self.sup_table.setColumnCount(5)
        self.sup_table.setHorizontalHeaderLabels(["ID", "Название", "Телефон", "Email", "Адрес"])
        self.sup_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.sup_table)
        self.refresh_suppliers()
        w.refresh = lambda: self.refresh_suppliers()
        return w

    def categories_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        # ALL buttons on TOP
        bar = QHBoxLayout()
        self.cat_name = QLineEdit()
        self.cat_name.setPlaceholderText("Название категории...")
        bar.addWidget(self.cat_name)
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(lambda: self._add_category(self.cat_name.text(), self.cat_name))
        bar.addWidget(btn_add)
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(lambda: self._del_category(self.cat_table))
        bar.addWidget(btn_del)
        layout.addLayout(bar)
        self.cat_table = QTableWidget()
        self.cat_table.setColumnCount(2)
        self.cat_table.setHorizontalHeaderLabels(["ID", "Название"])
        self.cat_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cat_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.cat_table)
        self._refresh_categories_table(self.cat_table)
        w.refresh = lambda: self._refresh_categories_table(self.cat_table)
        return w

    def _open_entity_dialog(self, table_name, pk_col, prefix, pk_id):
        dlg = QDialog(self)
        is_edit = pk_id is not None
        dlg.setWindowTitle(f"Редактировать {prefix}" if is_edit else f"Добавить {prefix}")
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        fields = {}
        col_list = "name, phone, email, address".split(", ")
        for col in col_list:
            le = QLineEdit()
            form.addRow(col.capitalize() + ":", le)
            fields[col] = le
        layout.addLayout(form)
        if pk_id:
            row = self.db.fetchone(f"SELECT * FROM {table_name} WHERE {pk_col} = ?", (pk_id,))
            if row:
                for col in col_list:
                    fields[col].setText(row[col] or '')
        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(dlg.accept)
        btns.addWidget(btn_ok)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(dlg.reject)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            values = [fields[col].text() for col in col_list]
            if not values[0].strip():
                QMessageBox.warning(self, "Ошибка", "Укажите название")
                return
            if pk_id:
                set_clause = ", ".join([f"{col} = ?" for col in col_list])
                self.db.execute(f"UPDATE {table_name} SET {set_clause} WHERE {pk_col} = ?", values + [pk_id])
                QMessageBox.information(self, "Успех", f"Запись обновлена")
            else:
                placeholders = ", ".join(["?" for _ in col_list])
                self.db.execute(f"INSERT INTO {table_name} ({', '.join(col_list)}) VALUES ({placeholders})", values)
                QMessageBox.information(self, "Успех", f"Запись добавлена")

    def _edit_entity(self, table_name, pk_col, pk_name, table, prefix):
        row = self.get_selected_row(table)
        if not row:
            QMessageBox.warning(self, "Ошибка", f"Выберите {prefix}")
            return
        self._open_entity_dialog(table_name, pk_col, prefix, row)

    def _del_entity(self, table_name, pk_col, title, table):
        pid = self.get_selected_row(table)
        if not pid:
            QMessageBox.warning(self, "Ошибка", f"Выберите запись")
            return
        if QMessageBox.question(self, "Подтверждение", f"Удалить запись #{pid}?") == QMessageBox.StandardButton.Yes:
            self.db.execute(f"DELETE FROM {table_name} WHERE {pk_col} = ?", (pid,))
            table.model().layoutChanged.emit()
            QMessageBox.information(self, "Успех", "Запись удалена")

    def _export_entity(self, table_name, columns, title):
        path, _ = QFileDialog.getSaveFileName(self, f"Экспорт {title}", f"{table_name}.csv", "CSV Files (*.csv)")
        if not path: return
        try:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                col_list = columns.split(", ")
                writer.writerow([c.capitalize() for c in col_list])
                for row in self.db.fetchall(f"SELECT {columns} FROM {table_name}"):
                    writer.writerow([row[c] for c in col_list])
                QMessageBox.information(self, "Успех", "Экспорт завершён")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

if __name__ == "__main__":
    import sys
    db = Database()
    app = QApplication(sys.argv)
    win = MainWindow(db)
    win.show()
    rc = app.exec()
    db.close()
    sys.exit(rc)
