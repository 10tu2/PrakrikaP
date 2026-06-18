"""
Dialogs module for PrakrikaP warehouse management app.
Reusable QDialog classes for CRUD operations on all entities.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QSpinBox, QComboBox,
    QMessageBox, QDateEdit, QLabel, QSplitter
)
from PyQt6.QtCore import Qt, QDate


class EntityDialog(QDialog):
    """Generic dialog for editing/adding any entity."""
    
    def __init__(self, parent, db, table_name, columns, col_labels, pk_col, row_data=None):
        super().__init__(parent)
        self.db = db
        self.table_name = table_name
        self.columns = columns
        self.col_labels = col_labels
        self.pk_col = pk_col
        self.row_data = row_data
        self.fields = {}
        self.col_list = columns.split(", ")
        self._init_ui()
    
    def _init_ui(self):
        title = "Добавить" if self.row_data is None else "Редактировать"
        self.setWindowTitle(f"{title} запись")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        for col in self.col_list:
            label = self.col_labels.get(col, col)
            if "text" in col.lower() or "name" in col.lower() or col in ("sku", "phone", "email", "address", "unit", "status", "notes", "description"):
                field = QLineEdit()
                field.setPlaceholderText(label)
            elif col.endswith("_id"):
                field = QSpinBox()
                field.setRange(1, 999999)
            elif col in ("price", "total"):
                field = QSpinBox()
                field.setRange(0, 9999999)
            elif col in ("stock", "min_stock", "quantity"):
                field = QSpinBox()
                field.setRange(0, 999999)
            elif "date" in col.lower():
                field = QDateEdit()
                field.setCalendarPopup(True)
                field.setDate(QDate.currentDate())
            else:
                field = QLineEdit()
                field.setPlaceholderText(label)
            
            self.fields[col] = field
            form.addRow(label, field)
        
        layout.addLayout(form)
        
        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btns.addWidget(btn_ok)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)
        
        self._load_data()
    
    def _load_data(self):
        if self.row_data:
            for col in self.col_list:
                val = self.row_data.get(col)
                field = self.fields.get(col)
                if field:
                    if isinstance(field, QSpinBox):
                        field.setValue(int(val) if val else 0)
                    elif isinstance(field, QDateEdit):
                        field.setDate(QDate.fromString(val, "yyyy-MM-dd") if val else QDate.currentDate())
                    else:
                        field.setText(str(val) if val else "")
    
    def get_values(self):
        return [self.fields[col].text() if isinstance(self.fields[col], (QLineEdit, QTextEdit))
                else str(self.fields[col].value()) if isinstance(self.fields[col], QSpinBox)
                else self.fields[col].date().toString("yyyy-MM-dd") if isinstance(self.fields[col], QDateEdit)
                else str(self.fields[col].currentText()) if isinstance(self.fields[col], QComboBox)
                else "" for col in self.col_list]
    
    def save(self):
        values = self.get_values()
        if not values[0].strip():
            QMessageBox.warning(self, "Ошибка", "Укажите название")
            return False
        pk_id = self.row_data.get(self.pk_col) if self.row_data else None
        if pk_id:
            set_clause = ", ".join([f"{col} = ?" for col in self.col_list])
            self.db.execute(f"UPDATE {self.table_name} SET {set_clause} WHERE {self.pk_col} = ?", values + [pk_id])
            QMessageBox.information(self, "Успех", "Запись обновлена")
        else:
            placeholders = ", ".join(["?" for _ in self.col_list])
            self.db.execute(f"INSERT INTO {self.table_name} ({', '.join(self.col_list)}) VALUES ({placeholders})", values)
            QMessageBox.information(self, "Успех", "Запись добавлена")
        return True


class OrderViewDialog(QDialog):
    """Read-only dialog to view order details with items."""
    
    def __init__(self, parent, db, order_id):
        super().__init__(parent)
        self.db = db
        self.order_id = order_id
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle("Просмотр заказа")
        self.setMinimumSize(500, 400)
        layout = QVBoxLayout(self)
        
        order = self.db.fetchone("SELECT * FROM orders WHERE order_id = ?", (self.order_id,))
        if not order:
            QMessageBox.warning(self, "Ошибка", "Заказ не найден")
            self.reject()
            return
        
        customer = self.db.fetchone("SELECT name FROM customers WHERE customer_id = ?", (order["customer_id"],))
        customer_name = customer["name"] if customer else "Не указан"
        
        info = QFormLayout()
        info.addRow("ID:", QLabel(str(order["order_id"])))
        info.addRow("Клиент:", QLabel(customer_name))
        info.addRow("Дата:", QLabel(order["order_date"]))
        status_map = {"NEW": "Новый", "PROCESSING": "В обработке", "COMPLETED": "Завершён", "CANCELLED": "Отменён"}
        info.addRow("Статус:", QLabel(status_map.get(order["status"], order["status"])))
        info.addRow("Сумма:", QLabel(f"{order['total']:.2f}"))
        if order["notes"]:
            info.addRow("Заметки:", QLabel(order["notes"]))
        layout.addLayout(info)
        
        items = self.db.fetchall("""SELECT oi.quantity, oi.price, p.name as product_name
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = ?""", (self.order_id,))
        
        if items:
            items_text = "\n".join([f"  {i['product_name']}: {i['quantity']} x {i['price']:.2f}" for i in items])
            items_label = QLabel("Товары:\n" + items_text)
            items_label.setWordWrap(True)
            layout.addWidget(items_label)
        else:
            layout.addWidget(QLabel("Нет товаров в заказе"))
        
        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)


class SimpleInputDialog(QDialog):
    """Simple dialog with a single text input field."""
    
    def __init__(self, parent, title, label_text, placeholder=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.field = QLineEdit()
        self.field.setPlaceholderText(placeholder)
        form.addRow(label_text, self.field)
        layout.addLayout(form)
        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btns.addWidget(btn_ok)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)
    
    def get_text(self):
        return self.field.text().strip()
