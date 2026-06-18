"""
PrakrikaP - Warehouse Management App
Entry point that wires all modules together.
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox

from database import Database
from ui_tabs import ProductsTab, OrdersTab, CustomersTab, SuppliersTab, CategoriesTab


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Практика П - Управление складом")
        self.resize(1000, 700)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create tabs with unified top bar
        self.products_tab = ProductsTab(db, self)
        self.orders_tab = OrdersTab(db, self)
        self.clients_tab = CustomersTab(db, self)
        self.suppliers_tab = SuppliersTab(db, self)
        self.categories_tab = CategoriesTab(db, self)

        self.tabs.addTab(self.products_tab, "Товары")
        self.tabs.addTab(self.orders_tab, "Заказы")
        self.tabs.addTab(self.clients_tab, "Клиенты")
        self.tabs.addTab(self.suppliers_tab, "Поставщики")
        self.tabs.addTab(self.categories_tab, "Категории")

        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        """Refresh tab when switching to it."""
        tab = self.tabs.widget(index)
        if hasattr(tab, "refresh"):
            tab.refresh()

    def closeEvent(self, event):
        """Confirm exit and close database connection."""
        if QMessageBox.question(
            self, "Подтверждение", "Вы точно хотите выйти?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.db.close()
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    db = Database()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow(db)
    win.show()
    rc = app.exec()
    sys.exit(rc)
