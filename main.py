import sys
from PyQt5.QtWidgets import (QPushButton, QMainWindow, QApplication, QWidget,
                             QDialog, QStackedWidget, QLineEdit, QHBoxLayout,
                             QVBoxLayout, QLabel, qApp, QAction)
from PyQt5.QtCore import Qt


class Main(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        global console

        console = QLineEdit(self)
        console.setStyleSheet("background-color: #BEBEBE; color: #333")
        console.textChanged.connect(handleEntry)
        console.returnPressed.connect(handleEntryReturn)

        self.stacked = QStackedWidget()
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.stacked)
        self.mainLayout.addWidget(console)
        mainWidget = QWidget()
        mainWidget.setLayout(self.mainLayout)
        self.switchBookView() #

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        exitAction = QAction('&Exit', self)
        exitAction.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAction)
        switchMenu = menubar.addMenu('&Switch')
        switchMainAction = QAction('&Main Menu', self)
        switchMainAction.triggered.connect(self.switchMainView)
        switchMenu.addAction(switchMainAction)
        switchBookAction = QAction('&Book1', self)
        switchBookAction.triggered.connect(self.switchBookView)
        switchMenu.addAction(switchBookAction)
        # these menus are temporary

        self.setCentralWidget(mainWidget)
        self.setGeometry(100, 300, 800, 600)
        self.setWindowTitle('retype')

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
        self.label = QLabel('Main View', self)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)


class BookView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout()
        self.label = QLabel('Book View', self)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)


def handleEntry():
    print(console.text())


def handleEntryReturn():
    entry = console.text()

    if entry == 'book1':
        retype.switchBookView()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    retype = Main()
    retype.show()
    sys.exit(app.exec_())
