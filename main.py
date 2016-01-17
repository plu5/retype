import sys
from PyQt5.QtWidgets import (QPushButton, QMainWindow, QApplication, QWidget,
                             QDialog, QStackedWidget, QLineEdit, QHBoxLayout,
                             QVBoxLayout)


class Main(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked = QStackedWidget()
        self.setCentralWidget(self.stacked)
        self.switchMainView()

        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('retype')
        self.show()

    def switchMainView(self):
        mainView = MainView(self)
        self.stacked.addWidget(mainView)
        self.stacked.setCurrentWidget(mainView)

    def switchBookView(self):
        bookView = BookView(self)
        self.stacked.addWidget(bookView)
        self.stacked.setCurrentWidget(bookView)


class MainView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout()
        book1 = QPushButton('book1', self)
        book1.clicked.connect(self.parent().switchBookView)
        console = QLineEdit(self)
        self.layout.addWidget(book1)
        self.layout.addStretch(0)
        self.layout.addWidget(console)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)


class BookView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        backBtn = QPushButton('back to main', self)
        backBtn.clicked.connect(self.parent().switchMainView)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    retype = Main()
    sys.exit(app.exec_())
