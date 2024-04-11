from qt import pyqtSignal, Qt, QSizePolicy

from retype.ui import LineEdit
from retype.services.theme import theme, C, Theme
from retype.console import CommandService, HighlightingService


@theme('Console',
       C(fg='#333', bg='#BEBEBE', sel='#333', sel_bg='white',
         t_border='#4A4A4A', b_border='white', l_border='white',
         r_border='white'))
class Console(LineEdit):
    submitted = pyqtSignal(str)

    def __init__(self, prompt, font_family=None, parent=None):
        super().__init__(parent)
        self.setAccessibleName("console")
        self.returnPressed.connect(self._handleReturnPressed)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMaximumHeight(200)

        self._font = self.font()
        self._font_family = self.font_family = font_family
        self._prompt = prompt

        Theme.get('Console').changed.connect(self.themeUpdate)
        self.themeUpdate()

    def themeUpdate(self):
        qss = Theme.getQss('Console').replace(
            'Console', '*[accessibleName="console"]')
        self.setStyleSheet(qss)

    @property
    def prompt(self):
        return self._prompt

    @prompt.setter
    def prompt(self, value):
        self._prompt = value
        self.command_service.prompt = value

    @property
    def font_family(self):
        return self._font_family

    @font_family.setter
    def font_family(self, value):
        self._font_family = value
        self._font.setFamily(value)
        self.setFont(self._font)

    def initServices(self, book_view, switchView, loadBook, customise, about,
                     auto_newline):
        self.command_service = CommandService(
            self, book_view, switchView, loadBook, self._prompt, customise,
            about)
        self.highlighting_service = HighlightingService(
            self, book_view, auto_newline)

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

    def resizeEvent(self, e):
        height = self.size().height()
        if height > 10:
            px = int(0.8 * height - 5)
            self._font.setPixelSize(px)
            self.setFont(self._font)
        super().resizeEvent(e)
