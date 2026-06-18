""" PrakrikaP - Warehouse Management App
    Entry point that wires all modules together.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox
from database import Database
from ui_tabs import (
    ProductsTab, OrdersTab, CustomersTab,
    SuppliersTab, CategoriesTab
)


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Практика П - Управление складом")
        self.resize(1000, 700)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self._create_tabs()

        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _create_tabs(self):
        """Create and add all tabs with unified top bar."""
        tabs_config = [
            (ProductsTab, "Товары"),
            (OrdersTab, "Заказы"),
            (CustomersTab, "Клиенты"),
            (SuppliersTab, "Поставщики"),
            (CategoriesTab, "Категории"),
        ]
        try:
            self.products_tab = ProductsTab(self.db, self)
            self.orders_tab = OrdersTab(self.db, self)
            self.clients_tab = CustomersTab(self.db, self)
            self.suppliers_tab = SuppliersTab(self.db, self)
            self.categories_tab = CategoriesTab(self.db, self)
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка",
                f"Не удалось инициализировать вкладки:\n{e}"
            )
            raise

        try:
            self.tabs.addTab(self.products_tab, "Товары")
            self.tabs.addTab(self.orders_tab, "Заказы")
            self.tabs.addTab(self.clients_tab, "Клиенты")
            self.tabs.addTab(self.suppliers_tab, "Поставщики")
            self.tabs.addTab(self.categories_tab, "Категории")
        except Exception:
            pass

    def _on_tab_changed(self, index):
        """Refresh tab when switching to it."""
        tab = self.tabs.widget(index)
        if tab is not None:
            try:
                tab.refresh()
            except Exception:
                pass

    def closeEvent(self, event):
        """Confirm exit and close database connection."""
        try:
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                "Вы точно хотите выйти?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.db.close()
                except Exception:
                    pass
                event.accept()
            else:
                event.ignore()
        except Exception:
            event.accept()


if __name__ == "__main__":
    db = None
    try:
        db = Database()
    except Exception as e:
        print(f"Critical error: could not initialize database: {e}")
        sys.exit(1)

    app = QApplication(sys.argv)
    try:
        app.setStyle("Fusion")
    except Exception:
        pass

    try:
        win = MainWindow(db)
        win.show()
        rc = app.exec()
        sys.exit(rc)
    except Exception as e:
        print(f"Critical error: could not start application: {e}")
        try:
            if db:
                db.close()
        except Exception:
            pass
        sys.exit(1)
