from enum import Enum
from qt import pyqtSignal, Qt, QSizePolicy

from typing import TYPE_CHECKING

from retype.ui import LineEdit
from retype.services.theme import theme, C, Theme
from retype.console import CommandService, HighlightingService


@theme('Console',
       C(fg='#333', bg='#BEBEBE', sel='#333', sel_bg='white',
         t_border='#4A4A4A', b_border='white', l_border='white',
         r_border='white'))
class Console(LineEdit):
    submitted = pyqtSignal(str)

    class Ev(Enum):
        keypress = 0
        keyrelease = 1

    def __init__(self, prompt, font_family=None, parent=None):
        # type: (Console, str, str | None, QWidget | None) -> None
        super().__init__(parent)
        self.setAccessibleName("console")
        self.returnPressed.connect(self._handleReturnPressed)
        self.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Preferred)  # type: ignore[misc]
        self.setMaximumHeight(200)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._ev_subscribers = {
            self.Ev.keypress: [], self.Ev.keyrelease: []
        }  # type: dict[Console.Ev, list[Callable[[QKeyEvent], None]]]

        self._font = self.font()
        self._font_family = font_family  # type: str | None
        self._prompt = prompt

        self.command_service = None  # type: CommandService | None
        self.highlighting_service = None  # type: HighlightingService | None

        Theme.connect_changed('Console', self.themeUpdate)
        self.themeUpdate()

    def themeUpdate(self):
        # type: (Console) -> None
        qss = Theme.getQss('Console').replace(
            'Console', '*[accessibleName="console"]')
        self.setStyleSheet(qss)

    @property
    def prompt(self):
        # type: (Console) -> str
        return self._prompt

    @prompt.setter
    def prompt(self, value):
        # type: (Console, str) -> None
        self._prompt = value
        if self.command_service is not None:
            self.command_service.prompt = value

    @property
    def font_family(self):
        # type: (Console) -> str | None
        return self._font_family

    @font_family.setter
    def font_family(self, value):
        # type: (Console, str) -> None
        self._font_family = value
        self._font.setFamily(value)
        self.setFont(self._font)

    def initServices(self,  # type: Console
                     book_view,  # type: BookView
                     switchView,  # type: pyqtBoundSignal
                     loadBook,  # type: pyqtBoundSignal
                     customise,  # type: pyqtBoundSignal
                     about,  # type: pyqtBoundSignal
                     auto_newline  # type: bool
                     ):
        # type: (...) -> None
        self.command_service = CommandService(
            self, book_view, switchView, loadBook, self._prompt, customise,
            about)
        self.highlighting_service = HighlightingService(
            self, book_view, auto_newline)

    def _handleReturnPressed(self):
        # type: (Console) -> None
        self.submitted.emit(self.text())

    def clear(self):
        # type: (Console) -> None
        self.setText('')

    def keyPressEvent(self, e):
        # type: (Console, QKeyEvent) -> None
        if self.command_service is not None:
            if e.key() == Qt.Key.Key_Up:
                self.command_service.commandHistoryUp()
            if e.key() == Qt.Key.Key_Down:
                self.command_service.commandHistoryDown()

        super().keyPressEvent(e)

        for subscriber in self._ev_subscribers.get(self.Ev.keypress, []):
            subscriber(e)

    def keyReleaseEvent(self, e):
        # type: (Console, QKeyEvent) -> None
        super().keyReleaseEvent(e)

        for subscriber in self._ev_subscribers.get(self.Ev.keyrelease, []):
            subscriber(e)

    def subscribe(self, event_type, f):
        # type: (Console, Console.Ev, Callable[[QKeyEvent], None]) -> None
        if event_type == self.Ev.keypress:
            self._ev_subscribers[self.Ev.keypress].append(f)
        elif event_type == self.Ev.keyrelease:
            self._ev_subscribers[self.Ev.keyrelease].append(f)

    def transferFocus(self, e):
        # type: (Console, QKeyEvent) -> None
        """Like setFocus, except you can also pass a keyPress event from
 another widget. Only does so if no modifier keys (excluding Shift) are
 held."""
        if e.modifiers() in [
                Qt.KeyboardModifiers(Qt.KeyboardModifier.NoModifier),
                Qt.KeyboardModifiers(Qt.KeyboardModifier.ShiftModifier)
        ]:
            self.setFocus()
            self.keyPressEvent(e)

    def resizeEvent(self, e):
        # type: (Console, QResizeEvent) -> None
        height = self.size().height()
        if height > 10:
            px = int(0.8 * height - 5)
            self._font.setPixelSize(px)
            self.setFont(self._font)
        super().resizeEvent(e)


if TYPE_CHECKING:
    from typing import Callable  # noqa: F401
    from qt import (QWidget, QEvent, QKeyEvent, QFocusEvent,  # noqa: F401
                    QResizeEvent, pyqtBoundSignal)
    from retype.ui import BookView  # noqa: F401
