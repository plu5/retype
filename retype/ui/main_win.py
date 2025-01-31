import logging
from base64 import b64decode
from qt import (QMainWindow, QStackedWidget, QSplitter, Qt, pyqtSignal, QDir,
                QFile)

from typing import TYPE_CHECKING

from retype.resource_handler import getStylePath, getIcon


class MainWin(QMainWindow):
    opened = pyqtSignal()
    closing = pyqtSignal()

    def __init__(self, console, geometry, parent=None):  # qss_file
        # type: (MainWin, Console, Geometry, QWidget | None) -> None
        super().__init__(parent)
        self.console = console
        self.geom = geometry
        self._initUI()
        self._initQss()

    def _initUI(self):
        # type: (MainWin) -> None
        self.stacker = QStackedWidget()
        self.consistent_layout = QSplitter()
        self.consistent_layout.setHandleWidth(2)
        self.consistent_layout.setOrientation(Qt.Orientation.Vertical)
        self.consistent_layout.setContentsMargins(0, 0, 0, 0)
        self.consistent_layout.addWidget(self.stacker)
        self.consistent_layout.addWidget(self.console)

        self.setCentralWidget(self.consistent_layout)

        self.resize(self.geom['w'], self.geom['h'])
        if self.geom['x'] is not None and self.geom['y'] is not None:
            self.move(self.geom['x'], self.geom['y'])

        self.setWindowTitle('retype')
        self.setWindowIcon(getIcon('retype', 'ico'))

        self.splitters = {'main': self.consistent_layout}
        self.maybeRestoreSplitterState('main')

    def _initQss(self):
        # type: (MainWin) -> None
        QDir.addSearchPath('style', getStylePath())
        qss_file = QFile('style:0_default.qss')
        qss_file.open(QFile.ReadOnly | QFile.Text)
        qss = str(qss_file.readAll(), 'utf-8'
                  )  # type: str  # type: ignore[call-overload]
        self.setStyleSheet(qss)

    def currentView(self):
        # type: (MainWin) -> QWidget
        return self.stacker.currentWidget()

    def showEvent(self, event):
        # type: (MainWin, QShowEvent) -> None
        QMainWindow.showEvent(self, event)
        self.opened.emit()

    def closeEvent(self, event):
        # type: (MainWin, QCloseEvent) -> None
        self.closing.emit()
        event.accept()
        logging.info('retype quit')

    def denoteSplitter(self, name, splitter):
        # type: (MainWin, str, QSplitter) -> None
        self.splitters[name] = splitter

    def maybeRestoreSplitterState(self, name):
        # type: (MainWin, str) -> None
        splitter = self.splitters.get(name)
        if splitter and self.geom['save_splitters_on_quit']:
            key = f'{name}_splitter_state\
'  # type: Literal['main_splitter_state']  # type: ignore[assignment]
            encoded_state = self.geom.get(key)
            if encoded_state is not None:
                splitter.restoreState(b64decode(encoded_state))


if TYPE_CHECKING:
    from retype.extras.metatypes import Geometry  # noqa: F401
    from qt import QWidget, QShowEvent, QCloseEvent  # noqa: F401
    from retype.console import Console  # noqa: F401
    from typing import Literal  # noqa: F401
