from PyQt5.QtWidgets import (QLineEdit)
from PyQt5.QtCore import (pyqtSignal)
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
        #self._initConsoleService()#
        self._initServices()

    # def _initConsoleService(self):
    #     self._console_service = ConsoleService(self, self._window)

    def _initServices(self):
        self._command_service = CommandService(self, self._window)
        self._highlighting_service = HighlightingService(self, self._window)

    def _returnPressedEvent(self):
        self.onReturnSignal.emit(self.text())

    def clear(self):
        self.setText('')
