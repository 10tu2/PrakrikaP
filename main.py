import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QLabel,
    QStatusBar, QPushButton, QWidget, QHBoxLayout
)
from PyQt6.QtCore import Qt
from database import Database, ROLE_ADMIN
from dialogs import LoginDialog, LOGIN_EXIT_CODE
from ui_tabs import (
    ProductsTab, OrdersTab, ClientsTab,
    SuppliersTab, CategoriesTab, UsersTab,
)
from theme import LIGHT_THEME

APP_TITLE = "ПракрикаП — Оптовая торговля"
DB_PATH   = "trade_store.db"


class MainWindow(QMainWindow):
    def __init__(self, db: Database, user, on_logout=None):
        super().__init__()
        self.db         = db
        self.user       = user
        self._on_logout = on_logout
        is_admin        = (user["role"] == ROLE_ADMIN)

        self.setWindowTitle(
            f"{APP_TITLE}  —  {user['full_name'] or user['username']} "
            f"({'Администратор' if is_admin else 'Сотрудник'})"
        )
        self.resize(1100, 700)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        products_tab = ProductsTab(db)
        orders_tab   = OrdersTab(db, on_products_changed=products_tab.load)

        tabs.addTab(products_tab,       "🛒  Товары")
        tabs.addTab(orders_tab,         "📋  Заказы")
        tabs.addTab(ClientsTab(db),     "👥  Клиенты")
        tabs.addTab(SuppliersTab(db),   "🏭  Поставщики")
        tabs.addTab(CategoriesTab(db),  "🗂  Категории")

        if is_admin:
            tabs.addTab(UsersTab(db, current_user_id=user["id"]), "👤  Пользователи")

        # --- Строка статуса с кнопкой «Выйти» ---
        bar = QStatusBar()
        role_str = 'Администратор' if is_admin else 'Сотрудник'
        bar.addWidget(QLabel(f"  👤 {user['full_name'] or user['username']}   |   {role_str}"))

        btn_logout = QPushButton("🚪  Выйти")
        btn_logout.setObjectName("btn_logout")
        btn_logout.setFixedHeight(24)
        btn_logout.clicked.connect(self._logout)
        bar.addPermanentWidget(btn_logout)

        self.setStatusBar(bar)

    def _logout(self):
        self.hide()
        if self._on_logout:
            self._on_logout()

    def closeEvent(self, event):
        self.db.close()
        event.accept()


def _run_app(app: QApplication, db: Database):
    """Показывает LoginDialog, затем MainWindow. При выходе возвращает к LoginDialog."""
    while True:
        login = LoginDialog(db)
        result = login.exec()

        # Пользователь нажал «Выход» — закрываем приложение
        if result == LOGIN_EXIT_CODE:
            break

        # Закрыл окно крестиком (Rejected) или не вошёл
        if result != LoginDialog.DialogCode.Accepted or login.user is None:
            break

        logged_out = False

        def on_logout():
            nonlocal logged_out
            logged_out = True
            w.close()

        w = MainWindow(db, login.user, on_logout=on_logout)
        w.show()
        app.exec()

        if not logged_out:
            # Пользователь закрыл окно крестиком — выходим полностью
            break
        # Иначе (logged_out=True) — цикл повторяется, показывается окно входа


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(LIGHT_THEME)

    db = Database(DB_PATH)
    _run_app(app, db)
    db.close()
    sys.exit(0)


if __name__ == "__main__":
    main()
