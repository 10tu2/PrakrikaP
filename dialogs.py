""" Dialogs module for PrakrikaP warehouse management app.
    Reusable QDialog classes for CRUD operations on all entities.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTextEdit, QSpinBox, QComboBox, QMessageBox,
    QDateEdit, QLabel
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
            field = self._create_field(col, label)
            self.fields[col] = field
            form.addRow(label, field)

        layout.addLayout(form)
        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self._on_ok)
        btns.addWidget(btn_ok)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)
        self._load_data()

    def _create_field(self, col, label):
        """Create appropriate widget based on column name."""
        col_lower = col.lower()
        if ("text" in col_lower or "name" in col_lower or
                col in ("sku", "phone", "email", "address", "unit", "status", "notes", "description")):
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
        elif "date" in col_lower:
            field = QDateEdit()
            field.setCalendarPopup(True)
            field.setDate(QDate.currentDate())
        else:
            field = QLineEdit()
            field.setPlaceholderText(label)
        return field

    def _load_data(self):
        """Load existing row data into form fields."""
        if not self.row_data:
            return
        for col in self.col_list:
            val = self.row_data.get(col)
            field = self.fields.get(col)
            if field is None:
                continue
            try:
                self._set_field_value(field, val, col)
            except Exception:
                pass

    def _set_field_value(self, field, val, col):
        """Set value into a field, handling type conversion."""
        if val is None or val == "":
            if isinstance(field, QSpinBox):
                field.setValue(0)
            elif isinstance(field, QDateEdit):
                field.setDate(QDate.currentDate())
            else:
                field.setText("")
        elif isinstance(field, QSpinBox):
            field.setValue(int(val))
        elif isinstance(field, QDateEdit):
            try:
                field.setDate(QDate.fromString(str(val), "yyyy-MM-dd"))
            except Exception:
                field.setDate(QDate.currentDate())
        else:
            field.setText(str(val))

    def _get_field_value(self, field, col):
        """Get value from a field, handling type conversion."""
        if isinstance(field, (QLineEdit, QTextEdit)):
            return field.text().strip() if isinstance(field, QLineEdit) else field.toPlainText().strip()
        elif isinstance(field, QSpinBox):
            return str(field.value())
        elif isinstance(field, QDateEdit):
            return field.date().toString("yyyy-MM-dd")
        elif isinstance(field, QComboBox):
            return field.currentText()
        return ""

    def get_values(self):
        """Extract values from all form fields."""
        values = []
        for col in self.col_list:
            field = self.fields.get(col)
            if field is not None:
                try:
                    values.append(self._get_field_value(field, col))
                except Exception:
                    values.append("")
            else:
                values.append("")
        return values

    def _validate_values(self, values):
        """Validate that at least one non-empty value exists."""
        for val in values:
            if val and val.strip():
                return True
        return False

    def get_first_column_label(self):
        """Get the label of the first column for error messages."""
        if self.col_list:
            return self.col_labels.get(self.col_list[0], self.col_list[0])
        return "Поле"

    def save(self):
        """Save form data to database."""
        values = self.get_values()
        if not self._validate_values(values):
            field_label = self.get_first_column_label()
            QMessageBox.warning(self, "Ошибка", f"Заполните поле '{field_label}'")
            return False
        try:
            pk_id = self.row_data.get(self.pk_col) if self.row_data else None
            if pk_id:
                set_clause = ", ".join([f"{col} = ?" for col in self.col_list])
                self.db.execute(f"UPDATE {self.table_name} SET {set_clause} WHERE {self.pk_col} = ?",
                                values + [pk_id])
                QMessageBox.information(self, "Успех", "Запись обновлена")
            else:
                placeholders = ", ".join(["?" for _ in self.col_list])
                self.db.execute(
                    f"INSERT INTO {self.table_name} ({', '.join(self.col_list)}) VALUES ({placeholders})",
                    values)
                QMessageBox.information(self, "Успех", "Запись добавлена")
            self.accept()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")
            return False

    def _on_ok(self):
        """Handle OK button click."""
        self.save()


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

        order = None
        try:
            order = self.db.fetchone("SELECT * FROM orders WHERE order_id = ?", (self.order_id,))
        except Exception:
            pass

        if not order:
            QMessageBox.warning(self, "Ошибка", "Заказ не найден")
            self.reject()
            return

        customer_name = "Не указан"
        try:
            customer = self.db.fetchone("SELECT name FROM customers WHERE customer_id = ?",
                                        (order["customer_id"],))
            if customer:
                customer_name = customer.get("name", "Не указан")
        except Exception:
            pass

        info = QFormLayout()
        info.addRow("ID:", QLabel(str(order["order_id"])))
        info.addRow("Клиент:", QLabel(customer_name))
        info.addRow("Дата:", QLabel(order.get("order_date", "") or ""))
        status_map = {"NEW": "Новый", "PROCESSING": "В обработке",
                      "COMPLETED": "Завершён", "CANCELLED": "Отменён"}
        status = order.get("status", "")
        info.addRow("Статус:", QLabel(status_map.get(status, status)))
        info.addRow("Сумма:", QLabel(f"{order.get('total', 0):.2f}"))
        if order.get("notes"):
            info.addRow("Заметки:", QLabel(order["notes"]))
        layout.addLayout(info)

        items = None
        try:
            items = self.db.fetchall(
                """SELECT oi.quantity, oi.price, p.name as product_name
                   FROM order_items oi
                   JOIN products p ON oi.product_id = p.product_id
                   WHERE oi.order_id = ?""",
                (self.order_id,)
            )
        except Exception:
            pass

        if items:
            items_lines = []
            for i in items:
                try:
                    qty = i.get("quantity", 0)
                    price = i.get("price", 0)
                    name = i.get("product_name", "?")
                    items_lines.append(f"  {name}: {qty} x {price:.2f}")
                except Exception:
                    pass
            items_label = QLabel("Товары:\n" + "\n".join(items_lines))
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
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def get_text(self):
        """Return trimmed text from input, or None if empty."""
        text = self.field.text().strip()
        return text if text else None
