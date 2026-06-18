import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from database import Database
from ui_tabs import ProductsTab, OrdersTab, ClientsTab, SuppliersTab, CategoriesTab


class MainWindow(QMainWindow):
  def __init__(self):
    super().__init__()
    self.setWindowTitle("ПракрикаП — Оптовая торговля")
    self.resize(1000, 650)
    self.db = Database("trade_store.db")
    tabs = QTabWidget()
    tabs.addTab(ProductsTab(self.db), "Товары")
    tabs.addTab(OrdersTab(self.db), "Заказы")
    tabs.addTab(ClientsTab(self.db), "Клиенты")
    tabs.addTab(SuppliersTab(self.db), "Поставщики")
    tabs.addTab(CategoriesTab(self.db), "Категории")
    self.setCentralWidget(tabs)

  def closeEvent(self, event):
    self.db.close()
    event.accept()


if __name__ == "__main__":
  app = QApplication(sys.argv)
  w = MainWindow()
  w.show()
  sys.exit(app.exec())
