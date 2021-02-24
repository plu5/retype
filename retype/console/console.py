from PyQt5.Qt import QLineEdit, pyqtSignal, Qt

from retype.console import CommandService, HighlightingService


class Console(QLineEdit):
    submitted = pyqtSignal(str)
    loadBook = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAccessibleName("console")
        self.returnPressed.connect(self._handleReturnPressed)

    def initServices(self, book_view, switchView):
        self._command_service = CommandService(self, book_view, switchView)
        self._highlighting_service = HighlightingService(self, book_view)

    def _handleReturnPressed(self):
        self.submitted.emit(self.text())

    def clear(self):
        self.setText('')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self._command_service.commandHistoryUp()
        if event.key() == Qt.Key_Down:
            self._command_service.commandHistoryDown()
        QLineEdit.keyPressEvent(self, event)
