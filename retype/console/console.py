from PyQt5.Qt import QLineEdit, pyqtSignal, Qt

from retype.console import CommandService, HighlightingService


class Console(QLineEdit):
    submitted = pyqtSignal(str)
    loadBook = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAccessibleName("console")
        self.returnPressed.connect(self._handleReturnPressed)

    def initServices(self, book_view, switchViewSignal):
        self.command_service = CommandService(self, book_view, switchViewSignal)
        self.highlighting_service = HighlightingService(self, book_view)

    def _handleReturnPressed(self):
        self.submitted.emit(self.text())

    def clear(self):
        self.setText('')

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Up:
            self.command_service.commandHistoryUp()
        if e.key() == Qt.Key_Down:
            self.command_service.commandHistoryDown()
        QLineEdit.keyPressEvent(self, e)

    def transferFocus(self, e):
        """Like setFocus, except you can also pass a keyPress event from
 another widget."""
        self.setFocus()
        self.keyPressEvent(e)
