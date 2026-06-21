"""
theme.py — светлая тема для ПракрикаП.
Подключается один раз в main.py: app.setStyleSheet(LIGHT_THEME)
"""

LIGHT_THEME = """
/* ───────────────────────── Общий фон ───────────────────────── */
QWidget {
    background-color: #F5F7FA;
    color: #1E2230;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}

/* ─────────────────────── Главное окно ──────────────────────── */
QMainWindow {
    background-color: #EEF1F6;
}

/* ──────────────────────── Вкладки ──────────────────────────── */
QTabWidget::pane {
    border: 1px solid #D0D5DF;
    border-top: none;
    background: #F5F7FA;
    border-radius: 0 0 6px 6px;
}
QTabBar::tab {
    background: #DDE3EE;
    color: #4A5270;
    padding: 8px 20px;
    border: 1px solid #C8CDD8;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
    font-weight: 500;
}
QTabBar::tab:selected {
    background: #F5F7FA;
    color: #1E2230;
    border-bottom: 2px solid #F5F7FA;
    font-weight: 600;
}
QTabBar::tab:hover:!selected {
    background: #C8D0E0;
}

/* ──────────────────────── Таблицы ──────────────────────────── */
QTableWidget {
    background-color: #FFFFFF;
    alternate-background-color: #F0F4FA;
    gridline-color: #DDE3EE;
    border: 1px solid #D0D5DF;
    border-radius: 6px;
    selection-background-color: #D0E8FF;
    selection-color: #1A3A6B;
}
QTableWidget::item {
    padding: 4px 8px;
    border: none;
}
QHeaderView::section {
    background-color: #E4EAF5;
    color: #3A4260;
    padding: 6px 8px;
    border: none;
    border-right: 1px solid #C8CDD8;
    border-bottom: 2px solid #B0BAD0;
    font-weight: 600;
    font-size: 12px;
}
QHeaderView::section:first {
    border-left: none;
}

/* ──────────────────── Кнопки — база ────────────────────────── */
QPushButton {
    padding: 6px 16px;
    border-radius: 5px;
    border: none;
    font-weight: 500;
    font-size: 13px;
    min-height: 28px;
}

/* Зелёная — «Добавить» */
QPushButton[role="add"],
QPushButton#btn_add {
    background-color: #2ECC71;
    color: #FFFFFF;
}
QPushButton[role="add"]:hover,
QPushButton#btn_add:hover  { background-color: #27AE60; }
QPushButton[role="add"]:pressed,
QPushButton#btn_add:pressed { background-color: #1E8449; }

/* Синяя — «Изменить» / «Просмотр» */
QPushButton[role="edit"],
QPushButton#btn_edit,
QPushButton[role="view"],
QPushButton#btn_view {
    background-color: #3498DB;
    color: #FFFFFF;
}
QPushButton[role="edit"]:hover,
QPushButton#btn_edit:hover,
QPushButton[role="view"]:hover,
QPushButton#btn_view:hover  { background-color: #2980B9; }
QPushButton[role="edit"]:pressed,
QPushButton#btn_edit:pressed,
QPushButton[role="view"]:pressed,
QPushButton#btn_view:pressed { background-color: #1A6FA0; }

/* Красная — «Удалить» */
QPushButton[role="delete"],
QPushButton#btn_del {
    background-color: #E74C3C;
    color: #FFFFFF;
}
QPushButton[role="delete"]:hover,
QPushButton#btn_del:hover  { background-color: #C0392B; }
QPushButton[role="delete"]:pressed,
QPushButton#btn_del:pressed { background-color: #962D22; }

/* Синяя — OK / диалоги */
QPushButton[role="primary"],
QPushButton#btn_primary,
QDialogButtonBox QPushButton {
    background-color: #4A6FD4;
    color: #FFFFFF;
}
QPushButton[role="primary"]:hover,
QPushButton#btn_primary:hover,
QDialogButtonBox QPushButton:hover { background-color: #3B5FBF; }
QDialogButtonBox QPushButton[text="Cancel"],
QDialogButtonBox QPushButton[text="Отмена"] {
    background-color: #BDC3CF;
    color: #2C3448;
}
QDialogButtonBox QPushButton[text="Cancel"]:hover,
QDialogButtonBox QPushButton[text="Отмена"]:hover { background-color: #A8B0BF; }
QDialogButtonBox QPushButton[text="Close"] {
    background-color: #BDC3CF;
    color: #2C3448;
}
QDialogButtonBox QPushButton[text="Close"]:hover { background-color: #A8B0BF; }

/* Оранжевая — «+ Добавить товар» внутри OrderDialog */
QPushButton#btn_add_item {
    background-color: #F39C12;
    color: #FFFFFF;
}
QPushButton#btn_add_item:hover  { background-color: #D68910; }
QPushButton#btn_del_item {
    background-color: #E74C3C;
    color: #FFFFFF;
}
QPushButton#btn_del_item:hover  { background-color: #C0392B; }

/* Кнопка «Войти» в LoginDialog */
QPushButton#btn_login {
    background-color: #4A6FD4;
    color: #FFFFFF;
    font-size: 14px;
    padding: 8px 0;
    font-weight: 600;
    border-radius: 6px;
}
QPushButton#btn_login:hover   { background-color: #3B5FBF; }
QPushButton#btn_login:pressed { background-color: #2D4A9E; }

/* Кнопка «Выйти» в строке статуса */
QPushButton#btn_logout {
    background-color: #E74C3C;
    color: #FFFFFF;
    padding: 2px 12px;
    border-radius: 4px;
    font-size: 12px;
    min-height: 22px;
    font-weight: 500;
}
QPushButton#btn_logout:hover   { background-color: #C0392B; }
QPushButton#btn_logout:pressed { background-color: #962D22; }

/* Кнопка «Выход» в LoginDialog */
QPushButton#btn_exit {
    background-color: #BDC3CF;
    color: #2C3448;
    font-size: 13px;
    padding: 6px 0;
    border-radius: 6px;
    font-weight: 500;
}
QPushButton#btn_exit:hover   { background-color: #A8B0BF; }
QPushButton#btn_exit:pressed { background-color: #8090A0; }

/* ──────────────────── Поля ввода ────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #C0C8D8;
    border-radius: 5px;
    padding: 4px 8px;
    min-height: 24px;
    color: #1E2230;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1.5px solid #4A6FD4;
    background-color: #F8FBFF;
}
QLineEdit:disabled {
    background-color: #E8ECF2;
    color: #7A8099;
}
QComboBox::drop-down  { border: none; width: 22px; }
QComboBox::down-arrow { width: 10px; height: 10px; }
QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #C0C8D8;
    selection-background-color: #D0E8FF;
    selection-color: #1A3A6B;
    border-radius: 4px;
}

/* ──────────────────── Диалоги ───────────────────────────────── */
QDialog { background-color: #F5F7FA; }

/* ──────────────────── Метки ─────────────────────────────────── */
QLabel { background: transparent; color: #1E2230; }

/* ──────────────────── Строка статуса ───────────────────────── */
QStatusBar {
    background-color: #DDE3EE;
    color: #4A5270;
    border-top: 1px solid #C8CDD8;
}

/* ──────────────────── Скроллбар ────────────────────────────── */
QScrollBar:vertical {
    background: #EEF1F6; width: 10px; border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #B0BAD0; border-radius: 5px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #8090B8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #EEF1F6; height: 10px; border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #B0BAD0; border-radius: 5px; min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #8090B8; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ──────────────────── Тултипы ──────────────────────────────── */
QToolTip {
    background-color: #2C3448;
    color: #FFFFFF;
    border: 1px solid #4A5270;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
}
"""
