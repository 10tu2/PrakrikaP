import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QLabel, QStatusBar
from PyQt6.QtCore import Qt
from database import Database, ROLE_ADMIN
from dialogs import LoginDialog
from ui_tabs import (
    ProductsTab, OrdersTab, ClientsTab,
    SuppliersTab, CategoriesTab, UsersTab,
)

APP_TITLE = "ПракрикаП — Оптовая торговля"
DB_PATH   = "trade_store.db"


class MainWindow(QMainWindow):
    def __init__(self, db: Database, user):
        super().__init__()
        self.db   = db
        self.user = user
        is_admin  = (user["role"] == ROLE_ADMIN)

        self.setWindowTitle(
            f"{APP_TITLE}  —  {user['full_name'] or user['username']} "
            f"({'Администратор' if is_admin else 'Сотрудник'})"
        )
        self.resize(1100, 700)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        products_tab = ProductsTab(db)
        orders_tab   = OrdersTab(db, on_products_changed=products_tab.load)

        tabs.addTab(products_tab,       "Товары")
        tabs.addTab(orders_tab,         "Заказы")
        tabs.addTab(ClientsTab(db),     "Клиенты")
        tabs.addTab(SuppliersTab(db),   "Поставщики")
        tabs.addTab(CategoriesTab(db),  "Категории")

        if is_admin:
            tabs.addTab(UsersTab(db, current_user_id=user["id"]), "Пользователи")

        # Строка статуса
        bar = QStatusBar()
        role_str = 'Администратор' if is_admin else 'Сотрудник'
        bar.addWidget(QLabel(f"  Пользователь: {user['full_name'] or user['username']}  |  {role_str}"))
        self.setStatusBar(bar)

    def closeEvent(self, event):
        self.db.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    db  = Database(DB_PATH)

    login = LoginDialog(db)
    if login.exec() != LoginDialog.DialogCode.Accepted or login.user is None:
        sys.exit(0)

    w = MainWindow(db, login.user)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
