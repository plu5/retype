from os import path
from base64 import b64decode
from qt import QMainWindow, QStackedWidget, QSplitter, Qt, pyqtSignal

from retype.resource_handler import getStylePath, getIcon


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
        self.consistent_layout.setOrientation(Qt.Orientation.Vertical)
        self.consistent_layout.setContentsMargins(0, 0, 0, 0)
        self.consistent_layout.addWidget(self.stacker)
        self.consistent_layout.addWidget(self.console)

        self.setCentralWidget(self.consistent_layout)

        self.resize(self.geometry['w'], self.geometry['h'])
        if self.geometry['x'] is not None and self.geometry['y'] is not None:
            self.move(self.geometry['x'], self.geometry['y'])

        self.setWindowTitle('retype')
        self.setWindowIcon(getIcon('retype', 'ico'))

        self.splitters = {'main': self.consistent_layout}
        self.maybeRestoreSplitterState('main')

    def _initQss(self):
        qss_file = open(path.join(getStylePath(), 'default.qss')).read()
        self.setStyleSheet(qss_file)

    def currentView(self):
        return self.stacker.currentWidget()

    def closeEvent(self, event):
        self.closing.emit()
        event.accept()

    def denoteSplitter(self, name, splitter):
        self.splitters[name] = splitter

    def maybeRestoreSplitterState(self, name):
        splitter = self.splitters.get(name)
        if splitter and self.geometry.get('save_splitters_on_quit', True):
            encoded_state = self.geometry.get(f'{name}_splitter_state', None)
            if encoded_state is not None:
                splitter.restoreState(b64decode(encoded_state))
