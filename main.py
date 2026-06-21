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


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle(APP_TITLE)
        self.resize(1100, 700)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        tabs.addTab(ProductsTab(db), "Товары")
        tabs.addTab(OrdersTab(db),   "Заказы")
        tabs.addTab(ClientsTab(db),  "Клиенты")
        tabs.addTab(SuppliersTab(db), "Поставщики")
        tabs.addTab(CategoriesTab(db), "Категории")

    def closeEvent(self, event):
        self.db.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    db = Database()          # настройки читаются из DB_CONFIG в database.py
    w = MainWindow(db)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
