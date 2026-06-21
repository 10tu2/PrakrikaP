import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from database import Database
from ui_tabs import (
    ProductsTab,
    OrdersTab,
    ClientsTab,
    SuppliersTab,
    CategoriesTab,
)


APP_TITLE = "ПракрикаП — Оптовая торговля"
DB_PATH = "trade_store.db"


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle(APP_TITLE)
        self.resize(1100, 700)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        products_tab = ProductsTab(db)
        # Передаём колбэк обновления таба Товаров в таб Заказов
        orders_tab = OrdersTab(db, on_products_changed=products_tab.load)

        tabs.addTab(products_tab,          "Товары")
        tabs.addTab(orders_tab,            "Заказы")
        tabs.addTab(ClientsTab(db),        "Клиенты")
        tabs.addTab(SuppliersTab(db),      "Поставщики")
        tabs.addTab(CategoriesTab(db),     "Категории")

    def closeEvent(self, event):
        self.db.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    db = Database(DB_PATH)
    w = MainWindow(db)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
