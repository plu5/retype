from PyQt5.QtWidgets import (QMainWindow, QStackedWidget, QVBoxLayout, QWidget,
                             QPushButton)
from PyQt5.QtCore import (pyqtSignal)
from resource_handler import getStylePath
from os import path
from controllers.library import LibraryController, BookWrapper  #


class MainWin(QMainWindow):
    switchViewSignal = pyqtSignal(int)

    def __init__(self, console, parent=None): # qss_file
        super().__init__(parent)
        self.console = console
        self._initUI()
        self._initQss()
        #self.bookcontroller = BookController(self)  #
        #print(self.bookcontroller._book_list)  #

    def _initUI(self):
        self.stacker = QStackedWidget()
        self.consistent_layout = QVBoxLayout()
        self.consistent_layout.setContentsMargins(0, 0, 0, 0)
        self.consistent_layout.setSpacing(0)
        self.consistent_layout.addWidget(self.stacker)
        self.consistent_layout.addWidget(self.console)
        self.layout_container = QWidget()
        self.layout_container.setLayout(self.consistent_layout)

        self.setCentralWidget(self.layout_container)
        self.setGeometry(-900, 300, 800, 600)
        self.setWindowTitle('retype')

    def _initQss(self):
        qss_file = open(path.join(getStylePath(), 'default.qss')).read()
        self.setStyleSheet(qss_file)

    def currentView(self):
        return self.stacker.currentWidget()
