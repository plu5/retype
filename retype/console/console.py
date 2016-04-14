from PyQt5.QtWidgets import (QLineEdit)
from PyQt5.QtCore import (pyqtSignal)
from console.console_service import ConsoleService


class Console(QLineEdit):
    #onEntrySignal = pyqtSignal(str)
    #onReturnSignal = pyqtSignal(str)
    onReturnSignal = pyqtSignal(str)#

    def __init__(self, parent):
        super().__init__(parent)
        self._window = parent
        self.setAccessibleName("console")
        #self.textChanged.connect(self._textChangedEvent)
        self.returnPressed.connect(self._returnPressedEvent)#
        self._initConsoleService()#

    def _initConsoleService(self):
        self._console_service = ConsoleService(self, self._window)
        #self.textChanged.connect(self._console_service.handleHighlighting)

    def _textChangedEvent(self):
        self.onEntrySignal.emit(self.text())

    def _returnPressedEvent(self):
        self.onReturnSignal.emit(self.text())

    def clear(self):
        self.setText('')
