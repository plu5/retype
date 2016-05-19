from PyQt5.QtWidgets import (QLineEdit)
from PyQt5.QtCore import (pyqtSignal, Qt)
from console.command_service import CommandService
from console.highlighting_service import HighlightingService


class Console(QLineEdit):
    onReturnSignal = pyqtSignal(str)
    loadBookSignal = pyqtSignal(int)  #

    def __init__(self, parent):
        super().__init__(parent)
        self._window = parent
        self.setAccessibleName("console")
        self.returnPressed.connect(self._returnPressedEvent)
        self._initServices()

    def _initServices(self):
        self._command_service = CommandService(self, self._window)
        self._highlighting_service = HighlightingService(self, self._window)

    def _returnPressedEvent(self):
        self.onReturnSignal.emit(self.text())

    def clear(self):
        self.setText('')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self._command_service.commandHistoryUp()
        if event.key() == Qt.Key_Down:
            self._command_service.commandHistoryDown()
        QLineEdit.keyPressEvent(self, event)
