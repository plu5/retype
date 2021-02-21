from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import pyqtSignal, Qt

from retype.console.command_service import CommandService
from retype.console.highlighting_service import HighlightingService


class Console(QLineEdit):
    submitted = pyqtSignal(str)
    loadBook = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAccessibleName("console")
        self.returnPressed.connect(self._returnPressedEvent)

    def initServices(self, bookView, switchView):
        self._command_service = CommandService(self, bookView, switchView)
        self._highlighting_service = HighlightingService(self, bookView)

    def _returnPressedEvent(self):
        self.submitted.emit(self.text())

    def clear(self):
        self.setText('')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self._command_service.commandHistoryUp()
        if event.key() == Qt.Key_Down:
            self._command_service.commandHistoryDown()
        QLineEdit.keyPressEvent(self, event)
