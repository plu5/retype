from os import path
from PyQt5.Qt import QMainWindow, QStackedWidget, QSplitter, Qt, pyqtSignal

from retype.resource_handler import getStylePath


class MainWin(QMainWindow):
    closing = pyqtSignal()

    def __init__(self, console, geometry, parent=None):  # qss_file
        super().__init__(parent)
        self.console = console
        self.geometry = geometry
        self._initUI()
        self._initQss()

    def _initUI(self):
        self.stacker = QStackedWidget()
        self.consistent_layout = QSplitter()
        self.consistent_layout.setHandleWidth(2)
        self.consistent_layout.setOrientation(Qt.Vertical)
        self.consistent_layout.setContentsMargins(0, 0, 0, 0)
        self.consistent_layout.addWidget(self.stacker)
        self.consistent_layout.addWidget(self.console)

        self.setCentralWidget(self.consistent_layout)

        self.resize(self.geometry['w'], self.geometry['h'])
        if self.geometry['x'] is not None and self.geometry['y'] is not None:
            self.move(self.geometry['x'], self.geometry['y'])

        self.setWindowTitle('retype')

    def _initQss(self):
        qss_file = open(path.join(getStylePath(), 'default.qss')).read()
        self.setStyleSheet(qss_file)

    def currentView(self):
        return self.stacker.currentWidget()

    def closeEvent(self, event):
        self.closing.emit()
        event.accept()
