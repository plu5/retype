from PyQt5.QtWidgets import (QLineEdit)
from PyQt5.QtCore import (pyqtSignal)
from console.console_service import ConsoleService


class Console(QLineEdit):
    onReturnSignal = pyqtSignal(str)
    loadBookSignal = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self._window = parent
        self.setAccessibleName("console")
        self.returnPressed.connect(self._returnPressedEvent)
        self._initConsoleService()#

    def _initConsoleService(self):
        self._console_service = ConsoleService(self, self._window)

    def _returnPressedEvent(self):
        self.onReturnSignal.emit(self.text())

    def clear(self):
        self.setText('')
