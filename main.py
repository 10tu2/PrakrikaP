import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout,
    QLineEdit, QTextEdit, QSpinBox, QComboBox, QMessageBox, QDialog,
    QDateEdit, QLabel, QFrame, QGroupBox, QFileDialog, QSplitter
)
from PyQt6.QtCore import Qt, QDate, QDateTime
from PyQt6.QtGui import QColor, QBrush

DB_FILE = "trade_store.db"


class Database:
    def __init__(self, path=DB_FILE):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.init_db()

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
        self.execute("""
        CREATE TABLE IF NOT EXISTS categories(
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT ''
        )""")
        self.execute("""
        CREATE TABLE IF NOT EXISTS suppliers(
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            address TEXT DEFAULT ''
        )""")
        self.execute("""
        CREATE TABLE IF NOT EXISTS customers(
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            address TEXT DEFAULT ''
        )""")
        self.execute("""
        CREATE TABLE IF NOT EXISTS products(
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT NOT NULL UNIQUE,
            category_id INTEGER,
            supplier_id INTEGER,
            unit TEXT DEFAULT 'шт',
            price REAL NOT NULL DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0,
            min_stock INTEGER NOT NULL DEFAULT 0,
            description TEXT DEFAULT '',
            FOREIGN KEY(category_id) REFERENCES categories(category_id) ON DELETE SET NULL,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL
        )""")
        self.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'NEW',
            total REAL NOT NULL DEFAULT 0,
            note TEXT DEFAULT '',
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL
        )""")
        self.execute("""
        CREATE TABLE IF NOT EXISTS order_items(
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(product_id) ON DELETE SET NULL
        )""")
        self.execute("""
        CREATE TABLE IF NOT EXISTS actions_log(
            action_id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_time TEXT NOT NULL,
            user_name TEXT NOT NULL,
            action TEXT NOT NULL,
            section TEXT NOT NULL,
            details TEXT DEFAULT ''
        )""")
        self.seed()

    def seed(self):
        if self.fetchone("SELECT COUNT(*) c FROM categories")["c"] == 0:
            self.execute("INSERT INTO categories(name,description) VALUES (?,?)", ("Крепёж", "Болты, гайки, шайбы"))
            self.execute("INSERT INTO categories(name,description) VALUES (?,?)", ("Сантехника", "Трубы, фитинги, арматура"))
            self.execute("INSERT INTO categories(name,description) VALUES (?,?)", ("Отопление", "Радиаторы, краны, узлы"))
        if self.fetchone("SELECT COUNT(*) c FROM suppliers")["c"] == 0:
            self.execute("INSERT INTO suppliers(name,phone,email,address) VALUES (?,?,?,?)", ("ООО СтройПоставка", "+7 900 000-00-01", "info@stroy.ru", "Москва"))
            self.execute("INSERT INTO suppliers(name,phone,email,address) VALUES (?,?,?,?)", ("ИП СантехМаркет", "+7 900 000-00-02", "sales@santeh.ru", "Подольск"))
        if self.fetchone("SELECT COUNT(*) c FROM customers")["c"] == 0:
            self.execute("INSERT INTO customers(name,phone,email,address) VALUES (?,?,?,?)", ("ООО МонтажСервис", "+7 900 111-11-11", "order@montazh.ru", "Тверь"))
            self.execute("INSERT INTO customers(name,phone,email,address) VALUES (?,?,?,?)", ("ИП РемСнаб", "+7 900 222-22-22", "office@remsnab.ru", "Владимир"))
        if self.fetchone("SELECT COUNT(*) c FROM products")["c"] == 0:
            self.execute("INSERT INTO products(name,sku,category_id,supplier_id,unit,price,stock,min_stock,description) VALUES (?,?,?,?,?,?,?,?,?)", ("Болт М8x30", "SKU-0001", 1, 1, "шт", 6.5, 1200, 200, "Оцинкованный"))
            self.execute("INSERT INTO products(name,sku,category_id,supplier_id,unit,price,stock,min_stock,description) VALUES (?,?,?,?,?,?,?,?,?)", ("Труба ППР 25", "SKU-0002", 2, 2, "м", 38.0, 450, 100, "Для водоснабжения"))
            self.execute("INSERT INTO products(name,sku,category_id,supplier_id,unit,price,stock,min_stock,description) VALUES (?,?,?,?,?,?,?,?,?)", ("Радиатор 10 секций", "SKU-0003", 3, 1, "шт", 4200.0, 35, 10, "Алюминиевый"))
        if self.fetchone("SELECT COUNT(*) c FROM orders")["c"] == 0:
            self.execute("INSERT INTO orders(customer_id,order_date,status,total,note) VALUES (?,?,?,?,?)", (1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "NEW", 0, ""))
            self.execute("INSERT INTO order_items(order_id,product_id,quantity,price) VALUES (?,?,?,?)", (1, 1, 10, 6.5))
            self.execute("INSERT INTO order_items(order_id,product_id,quantity,price) VALUES (?,?,?,?)", (1, 2, 5, 38.0))
            self.recalc_total(1)
        if self.fetchone("SELECT COUNT(*) c FROM actions_log")["c"] == 0:
            self.log("System", "Init", "Создана база и загружены тестовые данные")

    def recalc_total(self, order_id):
        cur = self.execute("""
            UPDATE orders SET total = (
                SELECT COALESCE(SUM(quantity * price), 0)
                FROM order_items WHERE order_id = ?
            ) WHERE order_id = ?
        """, (order_id, order_id))
        return cur.lastrowid or order_id

    def log(self, user_name, action, section, details=""):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.execute("""
            INSERT INTO actions_log(action_time, user_name, action, section, details)
            VALUES (?, ?, ?, ?, ?)
        """, (now, user_name, action, section, details))

    def close(self):
        self.conn.close()

class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Практика П - Торговый склад")
        self.setGeometry(100, 100, 1000, 600)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        tabs.addTab(self.products_tab(), "Товары")
        tabs.addTab(self.orders_tab(), "Заказы")
        tabs.addTab(self.products_catalog_tab(), "Каталог")
        tabs.addTab(self.clients_tab(), "Клиенты")
        tabs.addTab(self.suppliers_tab(), "Поставщики")
        tabs.addTab(self.logs_tab(), "Журнал")

        tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        tab = self.centralWidget().widget(index)
        if hasattr(tab, "refresh"):
            tab.refresh()

    def products_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        # Поиск
        search_layout = QHBoxLayout()
        self.prod_search = QLineEdit()
        self.prod_search.setPlaceholderText("Поиск по названию или SKU...")
        self.prod_search.textChanged.connect(self.refresh_products)
        search_layout.addWidget(self.prod_search)

        self.prod_category = QComboBox()
        self.prod_category.addItem("Все категории", 0)
        self.refresh_categories()
        self.prod_category.currentIndexChanged.connect(self.refresh_products)
        search_layout.addWidget(self.prod_category)

        btn_add = QPushButton("Добавить товар")
        btn_add.clicked.connect(lambda: self.open_product_dialog())
        search_layout.addWidget(btn_add)

        btn_import = QPushButton("Импорт")
        btn_import.clicked.connect(self.import_products)
        search_layout.addWidget(btn_import)

        btn_export = QPushButton("Экспорт")
        btn_export.clicked.connect(self.export_products)
        search_layout.addWidget(btn_export)

        layout.addLayout(search_layout)

        # Таблица
        self.prod_table = QTableWidget()
        headers = ["ID", "Название", "SKU", "Категория", "Поставщик", "Ед.", "Цена", "Остаток", "Мин. остаток", "Описание"]
        self.prod_table.setColumnCount(len(headers))
        self.prod_table.setHorizontalHeaderLabels(headers)
        self.prod_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.prod_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.prod_table)

        # Нижние кнопки
        btn_bar = QHBoxLayout()
        btn_view = QPushButton("Просмотр")
        btn_view.clicked.connect(self.view_product)
        btn_bar.addWidget(btn_view)

        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self.edit_product)
        btn_bar.addWidget(btn_edit)

        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self.delete_product)
        btn_bar.addWidget(btn_del)

        btn_stock = QPushButton("Приход на склад")
        btn_stock.clicked.connect(self.stock_movement)
        btn_bar.addWidget(btn_stock)

        btn_bar.addStretch()
        layout.addLayout(btn_bar)

        self.refresh_products()
        return w

    def refresh_categories(self):
        self.prod_category.clear()
        self.prod_category.addItem("Все категории", 0)
        cats = self.db.fetchall("SELECT category_id, name FROM categories ORDER BY name")
        for c in cats:
            self.prod_category.addItem(c["name"], c["category_id"])

    def refresh_products(self):
        txt = self.prod_search.text().strip().lower()
        cat_id = self.prod_category.currentData()
        sql = "SELECT * FROM products WHERE 1=1"
        params = []
        if cat_id != 0:
            sql += " AND category_id = ?"
            params.append(cat_id)
        if txt:
            sql += " AND (LOWER(name) LIKE ? OR LOWER(sku) LIKE ?)"
            params.extend([f"%{txt}%", f"%{txt}%"])
        sql += " ORDER BY name"

        rows = self.db.fetchall(sql, params)
        cats = {r["category_id"]: r["name"] for r in self.db.fetchall("SELECT category_id, name FROM categories")}
        sups = {r["supplier_id"]: r["name"] for r in self.db.fetchall("SELECT supplier_id, name FROM suppliers")}

        self.prod_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.prod_table.setItem(i, 0, QTableWidgetItem(str(r["product_id"])))
            self.prod_table.setItem(i, 1, QTableWidgetItem(r["name"]))
            self.prod_table.setItem(i, 2, QTableWidgetItem(r["sku"]))
            self.prod_table.setItem(i, 3, QTableWidgetItem(cats.get(r["category_id"], "")))
            self.prod_table.setItem(i, 4, QTableWidgetItem(sups.get(r["supplier_id"], "")))
            self.prod_table.setItem(i, 5, QTableWidgetItem(r["unit"]))
            self.prod_table.setItem(i, 6, QTableWidgetItem(f"{r['price']:.2f}"))
            item = QTableWidgetItem(str(r["stock"]))
            if r["stock"] <= r["min_stock"]:
                item.setBackground(QBrush(QColor(255, 200, 200)))
            self.prod_table.setItem(i, 7, item)
            self.prod_table.setItem(i, 8, QTableWidgetItem(str(r["min_stock"])))
            self.prod_table.setItem(i, 9, QTableWidgetItem(r["description"]))

    def get_selected_product_id(self):
        row = self.prod_table.currentRow()
        if row < 0:
            return None
        return int(self.prod_table.item(row, 0).text())

    def view_product(self):
        pid = self.get_selected_product_id()
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return
        r = self.db.fetchone("SELECT * FROM products WHERE product_id = ?", (pid,))
        if r:
            cats = {row["category_id"]: row["name"] for row in self.db.fetchall("SELECT category_id, name FROM categories")}
            sups = {row["supplier_id"]: row["name"] for row in self.db.fetchall("SELECT supplier_id, name FROM suppliers")}
            info = f"ID: {r['product_id']}\nНазвание: {r['name']}\nSKU: {r['sku']}\nКатегория: {cats.get(r['category_id'], '')}\nПоставщик: {sups.get(r['supplier_id'], '')}\nЕд.: {r['unit']}\nЦена: {r['price']:.2f}\nОстаток: {r['stock']}\nМин. остаток: {r['min_stock']}\nОписание: {r['description']}"
            QMessageBox.information(self, "Товар", info)

    def edit_product(self):
        pid = self.get_selected_product_id()
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return
        self.open_product_dialog(product_id=pid)

    def open_product_dialog(self, product_id=None):
        d = ProductDialog(self.db, product_id, self)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh_products()
            self.refresh_categories()

    def delete_product(self):
        pid = self.get_selected_product_id()
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return
        if QMessageBox.question(self, "Подтверждение", "Удалить товар?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM products WHERE product_id = ?", (pid,))
            self.db.log("Admin", "DELETE", "Products", f"Удалён товар ID={pid}")
            self.refresh_products()

    def stock_movement(self):
        pid = self.get_selected_product_id()
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return
        r = self.db.fetchone("SELECT * FROM products WHERE product_id = ?", (pid,))
        d = QDialog(self)
        d.setWindowTitle(f"Приход на склад: {r['name']}")
        layout = QFormLayout(d)
        qty = QSpinBox()
        qty.setRange(1, 100000)
        layout.addRow("Количество:", qty)
        note = QTextEdit()
        note.setPlaceholderText("Комментарий")
        layout.addRow(note)
        btn_ok = QPushButton("Приход")
        layout.addRow(btn_ok)
        btn_ok.clicked.connect(d.accept)
        if d.exec() == QDialog.DialogCode.Accepted:
            new_stock = r["stock"] + qty.value()
            self.db.execute("UPDATE products SET stock = ? WHERE product_id = ?", (new_stock, pid))
            self.db.log("Admin", "STOCK_IN", "Products", f"Товар ID={pid} +{qty.value()} -> {new_stock}")
            self.refresh_products()

    def import_products(self):
        path, _ = QFileDialog.getOpenFileName(self, "Импорт товаров", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            import csv
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    try:
                        self.db.execute("""
                            INSERT INTO products(name, sku, category_id, supplier_id, unit, price, stock, min_stock, description)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(sku) DO UPDATE SET
                            name=excluded.name, price=excluded.price, stock=excluded.stock
                        """, (row.get("name",""), row.get("sku",""), row.get("category_id", 1),
                              row.get("supplier_id", 1), row.get("unit","шт"),
                              float(row.get("price", 0)), int(row.get("stock", 0)),
                              int(row.get("min_stock", 0)), row.get("description","")))
                        count += 1
                    except Exception:
                        pass
            self.db.log("Admin", "IMPORT", "Products", f"Импортировано {count} товаров")
            QMessageBox.information(self, "Импорт", f"Импортировано {count} товаров")
            self.refresh_products()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def export_products(self):
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт товаров", "products.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            import csv
            rows = self.db.fetchall("SELECT * FROM products ORDER BY name")
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["product_id", "name", "sku", "category_id", "supplier_id", "unit", "price", "stock", "min_stock", "description"])
                writer.writeheader()
                writer.writerows(rows)
            QMessageBox.information(self, "Экспорт", f"Экспортировано {len(rows)} товаров")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def orders_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        bar = QHBoxLayout()
        self.order_search = QLineEdit()
        self.order_search.setPlaceholderText("Поиск по номеру или клиенту...")
        self.order_search.textChanged.connect(self.refresh_orders)
        bar.addWidget(self.order_search)

        self.order_status = QComboBox()
        self.order_status.addItem("Все", "")
        for s in ["NEW", "PROCESS", "SHIPPED", "DONE", "CANCELLED"]:
            self.order_status.addItem(s, s)
        self.order_status.currentIndexChanged.connect(self.refresh_orders)
        bar.addWidget(self.order_status)

        btn_new = QPushButton("Новый заказ")
        btn_new.clicked.connect(self.create_order)
        bar.addWidget(btn_new)

        layout.addLayout(bar)

        self.order_table = QTableWidget()
        headers = ["ID", "Клиент", "Дата", "Статус", "Сумма", "Примечание"]
        self.order_table.setColumnCount(len(headers))
        self.order_table.setHorizontalHeaderLabels(headers)
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.order_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.order_table.doubleClicked.connect(selected=self.open_order_dialog)
        layout.addWidget(self.order_table)

        btn_row = QHBoxLayout()
        btn_open = QPushButton("Открыть")
        btn_open.clicked.connect(self.open_order_dialog)
        btn_row.addWidget(btn_open)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.refresh_orders()
        return w

    def refresh_orders(self):
        txt = self.order_search.text().strip().lower()
        status = self.order_status.currentData()
        sql = """
            SELECT o.*, c.name as customer_name
            FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id
            WHERE 1=1
        """
        params = []
        if status:
            sql += " AND o.status = ?"
            params.append(status)
        if txt:
            sql += " AND (LOWER(o.order_id) LIKE ? OR LOWER(c.name) LIKE ?)"
            params.extend([f"%{txt}%", f"%{txt}%"])
        sql += " ORDER BY o.order_date DESC"
        rows = self.db.fetchall(sql, params)

        self.order_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.order_table.setItem(i, 0, QTableWidgetItem(str(r["order_id"])))
            self.order_table.setItem(i, 1, QTableWidgetItem(r["customer_name"] or ""))
            self.order_table.setItem(i, 2, QTableWidgetItem(r["order_date"]))
            status_item = QTableWidgetItem(r["status"])
            if r["status"] == "NEW":
                status_item.setBackground(QBrush(QColor(200, 255, 200)))
            elif r["status"] == "CANCELLED":
                status_item.setBackground(QBrush(QColor(255, 200, 200)))
            self.order_table.setItem(i, 3, status_item)
            self.order_table.setItem(i, 4, QTableWidgetItem(f"{r['total']:.2f}"))
            self.order_table.setItem(i, 5, QTableWidgetItem(r["note"] or ""))

    def create_order(self):
        d = OrderDialog(self.db, None, self)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh_orders()

    def get_selected_order_id(self):
        row = self.order_table.currentRow()
        if row < 0:
            return None
        return int(self.order_table.item(row, 0).text())

    def open_order_dialog(self):
        oid = self.get_selected_order_id()
        if not oid:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ")
            return
        d = OrderDialog(self.db, oid, self)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh_orders()

    def products_catalog_tab(self):
        w = QWidget()
        w.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        layout = QVBoxLayout(w)

        bar = QHBoxLayout()
        cat_box = QComboBox()
        cat_box.addItem("Все категории", 0)
        cats = self.db.fetchall("SELECT category_id, name FROM categories ORDER BY name")
        for c in cats:
            cat_box.addItem(c["name"], c["category_id"])
        bar.addWidget(QLabel("Категория:"))
        bar.addWidget(cat_box)
        bar.addStretch()
        layout.addLayout(bar)

        self.catalog_table = QTableWidget()
        headers = ["Название", "SKU", "Категория", "Поставщик", "Цена", "Остаток"]
        self.catalog_table.setColumnCount(len(headers))
        self.catalog_table.setHorizontalHeaderLabels(headers)
        self.catalog_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.catalog_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.catalog_table)

        def show_catalog(cat_id):
            sql = """
                SELECT p.name, p.sku, c.name as cat_name, s.name as sup_name, p.price, p.stock
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.category_id
                LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
                WHERE ? = 0 OR p.category_id = ?
                ORDER BY p.name
            """
            rows = self.db.fetchall(sql, (cat_id, cat_id))
            self.catalog_table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                self.catalog_table.setItem(i, 0, QTableWidgetItem(r["name"]))
                self.catalog_table.setItem(i, 1, QTableWidgetItem(r["sku"]))
                self.catalog_table.setItem(i, 2, QTableWidgetItem(r["cat_name"] or ""))
                self.catalog_table.setItem(i, 3, QTableWidgetItem(r["sup_name"] or ""))
                self.catalog_table.setItem(i, 4, QTableWidgetItem(f"{r['price']:.2f}"))
                self.catalog_table.setItem(i, 5, QTableWidgetItem(str(r["stock"])))

        cat_box.currentIndexChanged.connect(lambda: show_catalog(cat_box.currentData()))
        show_catalog(0)
        return w

    def clients_tab(self):
        w = self.generic_list_tab("clients", "Клиенты", "client_id", ["name", "phone", "email", "address"],
                                   ["Имя", "Телефон", "E-mail", "Адрес"],
                                   "customers", lambda: "name, phone, email, address")
        return w

    def suppliers_tab(self):
        w = self.generic_list_tab("suppliers", "Поставщики", "supplier_id", ["name", "phone", "email", "address"],
                                   ["Название", "Телефон", "E-mail", "Адрес"],
                                   "suppliers", lambda: "name, phone, email, address")
        return w

    def generic_list_tab(self, attr_name, title, pk, cols, headers, table_name, cols_sql):
        w = QWidget()
        layout = QVBoxLayout(w)

        bar = QHBoxLayout()
        search = QLineEdit()
        search.setPlaceholderText("Поиск...")
        bar.addWidget(search)
        btn_add = QPushButton(f"Добавить {title[:-1]}")
        bar.addWidget(btn_add)
        layout.addLayout(bar)

        tbl = QTableWidget()
        tbl.setColumnCount(len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(tbl)

        def refresh():
            txt = search.text().strip().lower()
            sql = f"SELECT {cols_sql()} FROM {table_name}"
            params = []
            if txt:
                sql += " WHERE LOWER(name) LIKE ?"
                params.append(f"%{txt}%")
            sql += " ORDER BY name"
            rows = self.db.fetchall(sql, params)
            tbl.setRowCount(len(rows))
            for i, r in enumerate(rows):
                for j, col in enumerate(cols):
                    tbl.setItem(i, j, QTableWidgetItem(str(r[col] or "")))

        def add_item():
            d = QDialog(self)
            d.setWindowTitle(f"Добавить {title[:-1]}")
            form = QFormLayout(d)
            fields = {}
            for col in cols:
                le = QLineEdit()
                form.addRow(col, le)
                fields[col] = le
            btn = QPushButton("Сохранить")
            form.addRow(btn)
            btn.clicked.connect(d.accept)
            if d.exec() == QDialog.DialogCode.Accepted:
                vals = tuple(fields[col].text() for col in cols)
                placeholders = ",".join(["?"] * len(cols))
                self.db.execute(f"INSERT INTO {table_name}({','.join(cols)}) VALUES ({placeholders})", vals)
                self.db.log("Admin", "INSERT", title.rstrip("ы"), f"Добавлен {', '.join(vals)}")
                refresh()

        search.textChanged.connect(refresh)
        btn_add.clicked.connect(add_item)
        refresh()
        return w

    def logs_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        bar = QHBoxLayout()
        self.log_search = QLineEdit()
        self.log_search.setPlaceholderText("Поиск в журнале...")
        self.log_search.textChanged.connect(self.refresh_logs)
        bar.addWidget(self.log_search)
        layout.addLayout(bar)

        tbl = QTableWidget()
        headers = ["ID", "Время", "Пользователь", "Действие", "Раздел", "Детали"]
        tbl.setColumnCount(len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(tbl)

        def refresh():
            txt = self.log_search.text().strip().lower()
            sql = "SELECT * FROM actions_log"
            params = []
            if txt:
                sql += " WHERE LOWER(user_name) LIKE ? OR LOWER(action) LIKE ? OR LOWER(section) LIKE ? OR LOWER(details) LIKE ?"
                params.extend([f"%{txt}%"] * 4)
            sql += " ORDER BY action_time DESC"
            rows = self.db.fetchall(sql, params)
            tbl.setRowCount(len(rows))
            for i, r in enumerate(rows):
                tbl.setItem(i, 0, QTableWidgetItem(str(r["action_id"])))
                tbl.setItem(i, 1, QTableWidgetItem(r["action_time"]))
                tbl.setItem(i, 2, QTableWidgetItem(r["user_name"]))
                tbl.setItem(i, 3, QTableWidgetItem(r["action"]))
                tbl.setItem(i, 4, QTableWidgetItem(r["section"]))
                tbl.setItem(i, 5, QTableWidgetItem(r["details"]))

        self.db.log("System", "OPEN", "Logs", "Открыт журнал действий")
        refresh()
        return w

    def refresh_logs(self):
        # The log tab widget has its own refresh captured in closure
        # We trigger it by calling textChanged connected handler
        pass

class ProductDialog(QDialog):
    def __init__(self, db, product_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.product_id = product_id
        if product_id:
            self.setWindowTitle("Редактировать товар")
        else:
            self.setWindowTitle("Добавить товар")
        self.resize(400, 300)

        layout = QFormLayout(self)

        self.le_name = QLineEdit()
        self.le_sku = QLineEdit()

        self.cb_category = QComboBox()
        cats = db.fetchall("SELECT category_id, name FROM categories ORDER BY name")
        for c in cats:
            self.cb_category.addItem(c["name"], c["category_id"])

        self.cb_supplier = QComboBox()
        sups = db.fetchall("SELECT supplier_id, name FROM suppliers ORDER BY name")
        for s in sups:
            self.cb_supplier.addItem(s["name"], s["supplier_id"])

        self.le_unit = QLineEdit()
        self.le_unit.setText("шт")

        self.sb_price = QSpinBox()
        self.sb_price.setRange(0, 10**9)

        self.sb_stock = QSpinBox()
        self.sb_stock.setRange(0, 10**6)

        self.sb_minstock = QSpinBox()
        self.sb_minstock.setRange(0, 10**6)

        self.le_desc = QTextEdit()

        if product_id:
            r = db.fetchone("SELECT * FROM products WHERE product_id = ?", (product_id,))
            if r:
                self.le_name.setText(r["name"])
                self.le_sku.setText(r["sku"])
                idx = self.cb_category.findData(r["category_id"])
                if idx >= 0:
                    self.cb_category.setCurrentIndex(idx)
                idx = self.cb_supplier.findData(r["supplier_id"])
                if idx >= 0:
                    self.cb_supplier.setCurrentIndex(idx)
                self.le_unit.setText(r["unit"])
                self.sb_price.setValue(int(r["price"]))
                self.sb_stock.setValue(r["stock"])
                self.sb_minstock.setValue(r["min_stock"])
                self.le_desc.setText(r["description"])

        layout.addRow("Название:", self.le_name)
        layout.addRow("SKU:", self.le_sku)
        layout.addRow("Категория:", self.cb_category)
        layout.addRow("Поставщик:", self.cb_supplier)
        layout.addRow("Ед. изм.:", self.le_unit)
        layout.addRow("Цена:", self.sb_price)
        layout.addRow("Остаток:", self.sb_stock)
        layout.addRow("Мин. остаток:", self.sb_minstock)
        layout.addRow("Описание:", self.le_desc)

        btn_ok = QPushButton("Сохранить")
        layout.addRow(btn_ok)
        btn_ok.clicked.connect(self.save)

    def save(self):
        cat_id = self.cb_category.currentData()
        sup_id = self.cb_supplier.currentData()
        if not self.le_name.text().strip():
            QMessageBox.warning(self, "Ошибка", "Название обязательно")
            return
        if not self.le_sku.text().strip():
            QMessageBox.warning(self, "Ошибка", "SKU обязательно")
            return

        try:
            if self.product_id:
                self.db.execute("""
                    UPDATE products SET name=?, sku=?, category_id=?, supplier_id=?,
                    unit=?, price=?, stock=?, min_stock=?, description=? WHERE product_id=?
                """, (self.le_name.text(), self.le_sku.text(), cat_id, sup_id,
                      self.le_unit.text(), self.sb_price.value(), self.sb_stock.value(),
                      self.sb_minstock.value(), self.le_desc.toPlainText(), self.product_id))
                self.db.log("Admin", "UPDATE", "Products", f"Обновлён товар ID={self.product_id}")
            else:
                self.db.execute("""
                    INSERT INTO products(name, sku, category_id, supplier_id, unit, price, stock, min_stock, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (self.le_name.text(), self.le_sku.text(), cat_id, sup_id,
                      self.le_unit.text(), self.sb_price.value(), self.sb_stock.value(),
                      self.sb_minstock.value(), self.le_desc.toPlainText()))
                self.db.log("Admin", "INSERT", "Products", f"Добавлен товар {self.le_name.text()}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class OrderDialog(QDialog):
    def __init__(self, db, order_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.order_id = order_id
        self.setWindowTitle("Заказ" if not order_id else f"Заказ #{order_id}")
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Верхняя часть: клиент, дата, статус
        form = QWidget()
        forml = QFormLayout(form)

        self.cb_client = QComboBox()
        clients = db.fetchall("SELECT customer_id, name FROM customers ORDER BY name")
        for c in clients:
            self.cb_client.addItem(c["name"], c["customer_id"])

        self.de_date = QDateEdit()
        self.de_date.setCalendarPopup(True)
        self.de_date.setDate(QDate.currentDate())

        self.cb_status = QComboBox()
        for s in ["NEW", "PROCESS", "SHIPPED", "DONE", "CANCELLED"]:
            self.cb_status.addItem(s)

        self.le_note = QLineEdit()

        if order_id:
            r = db.fetchone("SELECT * FROM orders WHERE order_id = ?", (order_id,))
            if r:
                idx = self.cb_client.findData(r["customer_id"])
                if idx >= 0:
                    self.cb_client.setCurrentIndex(idx)
                self.de_date.setDate(QDate.fromString(r["order_date"].split()[0], "yyyy-MM-dd"))
                self.cb_status.setCurrentText(r["status"])
                self.le_note.setText(r["note"] or "")

        forml.addRow("Клиент:", self.cb_client)
        forml.addRow("Дата:", self.de_date)
        forml.addRow("Статус:", self.cb_status)
        forml.addRow("Примечание:", self.le_note)
        layout.addWidget(form)

        # Таблица позиций
        self.items_table = QTableWidget()
        headers = ["Товар", "Кол-во", "Цена", "Сумма"]
        self.items_table.setColumnCount(len(headers))
        self.items_table.setHorizontalHeaderLabels(headers)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.items_table)

        # Кнопки позиций
        items_bar = QHBoxLayout()
        btn_add_item = QPushButton("Добавить позицию")
        btn_add_item.clicked.connect(self.add_item)
        btn_del_item = QPushButton("Удалить позицию")
        btn_del_item.clicked.connect(self.delete_item)
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.save)
        items_bar.addWidget(btn_add_item)
        items_bar.addWidget(btn_del_item)
        items_bar.addStretch()
        items_bar.addWidget(btn_save)
        layout.addLayout(items_bar)

        if order_id:
            self.refresh_items()

    def refresh_items(self):
        rows = self.db.fetchall("""
            SELECT oi.*, p.name as product_name
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = ?
        """, (self.order_id,))
        self.items_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.items_table.setItem(i, 0, QTableWidgetItem(r["product_name"] or "Unknown"))
            self.items_table.setItem(i, 1, QTableWidgetItem(str(r["quantity"])))
            self.items_table.setItem(i, 2, QTableWidgetItem(f"{r['price']:.2f}"))
            self.items_table.setItem(i, 3, QTableWidgetItem(f"{r['quantity'] * r['price']:.2f}"))

    def add_item(self):
        d = QDialog(self)
        d.setWindowTitle("Добавить позицию")
        layout = QFormLayout(d)

        cb_prod = QComboBox()
        prods = self.db.fetchall("SELECT product_id, name FROM products ORDER BY name")
        for p in prods:
            cb_prod.addItem(p["name"], p["product_id"])

        sb_qty = QSpinBox()
        sb_qty.setRange(1, 100000)
        sb_price = QDoubleSpinBox()
        sb_price.setRange(0, 10**9)

        layout.addRow("Товар:", cb_prod)
        layout.addRow("Кол-во:", sb_qty)
        layout.addRow("Цена:", sb_price)

        btn = QPushButton("Добавить")
        layout.addRow(btn)
        btn.clicked.connect(d.accept)

        if d.exec() == QDialog.DialogCode.Accepted:
            pid = cb_prod.currentData()
            qty = sb_qty.value()
            price = sb_price.value()
            if self.order_id:
                self.db.execute("INSERT INTO order_items(order_id, product_id, quantity, price) VALUES (?,?,?,?)",
                                (self.order_id, pid, qty, price))
                self.db.recalc_total(self.order_id)
                self.db.log("Admin", "ADD_ITEM", "Orders", f"Заказ #{self.order_id} + позиция {pid}")
            else:
                # Запомнить позицию для нового заказа
                if not hasattr(self, "pending_items"):
                    self.pending_items = []
                self.pending_items.append((pid, qty, price))
            self.refresh_items()

    def delete_item(self):
        if not self.order_id:
            return
        row = self.items_table.currentRow()
        if row < 0:
            return
        # Get product_id from the order_items
        rows = self.db.fetchall("SELECT item_id FROM order_items WHERE order_id = ?", (self.order_id,))
        if row < len(rows):
            item_id = rows[row]["item_id"]
            self.db.execute("DELETE FROM order_items WHERE item_id = ?", (item_id,))
            self.db.recalc_total(self.order_id)
            self.refresh_items()

    def save(self):
        client_id = self.cb_client.currentData()
        if not client_id:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента")
            return

        date_str = self.de_date.date().toString("yyyy-MM-dd") + " 12:00:00"
        status = self.cb_status.currentText()
        note = self.le_note.text()

        try:
            if self.order_id:
                self.db.execute("UPDATE orders SET customer_id=?, order_date=?, status=?, note=? WHERE order_id=?",
                                (client_id, date_str, status, note, self.order_id))
                self.db.log("Admin", "UPDATE", "Orders", f"Обновлён заказ #{self.order_id}")
            else:
                cur = self.db.execute("INSERT INTO orders(customer_id, order_date, status, note) VALUES (?,?,?,?)",
                                      (client_id, date_str, status, note))
                self.order_id = cur.lastrowid
                if hasattr(self, "pending_items"):
                    for pid, qty, price in self.pending_items:
                        self.db.execute("INSERT INTO order_items(order_id, product_id, quantity, price) VALUES (?,?,?,?)",
                                        (self.order_id, pid, qty, price))
                    self.db.recalc_total(self.order_id)
                self.db.log("Admin", "INSERT", "Orders", f"Создан заказ #{self.order_id}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

def main():
    import sys
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    db = Database()
    w = MainWindow(db)
    w.show()
    try:
        sys.exit(app.exec())
    finally:
        db.close()


if __name__ == "__main__":
    main()
