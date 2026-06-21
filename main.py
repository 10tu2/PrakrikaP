import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QLabel,
    QStatusBar, QPushButton, QWidget, QSizePolicy, QToolBar
)
from PyQt6.QtCore import Qt
from database import Database, ROLE_ADMIN
from dialogs import LoginDialog, LOGIN_EXIT_CODE
from ui_tabs import (
    ProductsTab, OrdersTab, ClientsTab,
    SuppliersTab, CategoriesTab, UsersTab,
)
from theme import LIGHT_THEME

APP_TITLE = "ООО Атрикс"
DB_PATH   = "trade_store.db"


class MainWindow(QMainWindow):
    def __init__(self, db: Database, user, on_logout=None):
        super().__init__()
        self.db           = db
        self.user         = user
        self._on_logout   = on_logout
        self._logging_out = False   # флаг: выход через кнопку, а не крестик
        is_admin          = (user["role"] == ROLE_ADMIN)

        self.setWindowTitle(
            f"{APP_TITLE}  —  {user['full_name'] or user['username']} "
            f"({'Администратор' if is_admin else 'Сотрудник'})"
        )
        self.resize(1100, 700)

        # --- Тулбар сверху ---
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)

        role_str = 'Администратор' if is_admin else 'Сотрудник'
        lbl_user = QLabel(f"  👤 {user['full_name'] or user['username']}   |   {role_str}  ")
        toolbar.addWidget(lbl_user)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        btn_logout = QPushButton("🚪  Выйти")
        btn_logout.setObjectName("btn_logout")
        btn_logout.clicked.connect(self._logout)
        toolbar.addWidget(btn_logout)

        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # --- Вкладки ---
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        products_tab = ProductsTab(db)
        orders_tab   = OrdersTab(db, on_products_changed=products_tab.load)

        tabs.addTab(products_tab,      "🛒  Товары")
        tabs.addTab(orders_tab,        "📋  Заказы")
        tabs.addTab(ClientsTab(db),    "👥  Клиенты")
        tabs.addTab(SuppliersTab(db),  "🏭  Поставщики")
        tabs.addTab(CategoriesTab(db), "🗂  Категории")

        if is_admin:
            tabs.addTab(UsersTab(db, current_user_id=user["id"]), "👤  Пользователи")

        self.setStatusBar(QStatusBar())

    def _logout(self):
        """logout — скрываем окно и выходим из event loop."""
        self._logging_out = True
        self.hide()
        QApplication.quit()          # завершает app.exec() в цикле

    def closeEvent(self, event):
        if not self._logging_out:
            # Пользователь закрыл крестиком — помечаем как не logout
            pass
        event.accept()


def _run_app(app: QApplication, db: Database):
    """Показывает LoginDialog, затем MainWindow.
    Кнопка «Выйти» в главном окне → возврат к окну входа.
    Крестик главного окна → выход из приложения.
    Кнопка «Выход» в окне входа → выход из приложения.
    """
    while True:
        login = LoginDialog(db)
        result = login.exec()

        if result == LOGIN_EXIT_CODE:
            # Нажал «Выход» на экране входа
            break

        if result != LoginDialog.DialogCode.Accepted or login.user is None:
            # Закрыл крестиком
            break

        w = MainWindow(db, login.user)
        w.show()
        app.exec()   # блокируется до QApplication.quit() или закрытия окна

        if not w._logging_out:
            # Пользователь закрыл окно крестиком — выходим полностью
            break
        # _logging_out=True — цикл повторяется, показывается окно входа

    db.close()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(LIGHT_THEME)

    db = Database(DB_PATH)
    _run_app(app, db)
    sys.exit(0)


if __name__ == "__main__":
    main()
