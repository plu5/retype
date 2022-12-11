from qt import pyqtSignal, Qt, QSize

from retype.ui import LineEdit
from retype.console import CommandService, HighlightingService


class Console(LineEdit):
    submitted = pyqtSignal(str)

    def __init__(self, prompt, parent=None):
        super().__init__(parent)
        self.setAccessibleName("console")
        self.returnPressed.connect(self._handleReturnPressed)
        self.setMaximumHeight(200)

        self._prompt = prompt

    @property
    def prompt(self):
        return self._prompt

    @prompt.setter
    def prompt(self, value):
        self._prompt = value
        self.command_service.prompt = value

    def initServices(self, book_view, switchView, loadBook, customise, about):
        self.command_service = CommandService(
            self, book_view, switchView, loadBook, self._prompt, customise,
            about)
        self.highlighting_service = HighlightingService(self, book_view)

    def _handleReturnPressed(self):
        self.submitted.emit(self.text())

    def clear(self):
        self.setText('')

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Up:
            self.command_service.commandHistoryUp()
        if e.key() == Qt.Key.Key_Down:
            self.command_service.commandHistoryDown()
        super().keyPressEvent(e)

    def transferFocus(self, e):
        """Like setFocus, except you can also pass a keyPress event from
 another widget. Only does so if no modifier keys (excluding Shift) are
 held."""
        if e.modifiers() in [Qt.KeyboardModifier.NoModifier,
                             Qt.KeyboardModifier.ShiftModifier]:
            self.setFocus()
            self.keyPressEvent(e)

    def sizeHint(self):  # TODO
        return QSize(15, 15)

    def resizeEvent(self, e):
        height = self.size().height()
        if height:
            px = int(0.8 * height - 5)
            self.setStyleSheet("font-size: {}px".format(px))
        super().resizeEvent(e)
