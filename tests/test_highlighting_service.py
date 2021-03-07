import sys
from PyQt5.Qt import (QObject, pyqtSignal, QTextCursor, QTextCharFormat,
                      QApplication, QTextBrowser)

from retype.console import HighlightingService


SAMPLE_CONTENT = '''<html><body>some test text<br/>
next line
</body></html>'''


class FakeConsole(QObject):
    textChanged = pyqtSignal(str)

    def __init__(self):
        QObject.__init__(self)

    def clear(self):
        pass

    def setText(self, text):
        self.textChanged.emit(text)


class FakeBookDisplay(QTextBrowser):
    def __init__(self):
        QTextBrowser.__init__(self)

    def centreAroundCursor(self):
        pass


class FakeBookView(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.display = FakeBookDisplay()
        self.display.setHtml(SAMPLE_CONTENT)

        self.chapter_pos = 0
        self.cursor_pos = 0
        self.line_pos = 0
        self.persistent_pos = 0
        self.to_be_typed_list = self.display.toPlainText().splitlines()
        self._setLine(self.line_pos)

        self.highlight_format = QTextCharFormat()
        self.unhighlight_format = QTextCharFormat()

        self.cursor = QTextCursor(self.display.document())
        self.cursor.setPosition(self.cursor_pos, self.cursor.KeepAnchor)

    def isVisible(self):
        return True

    def _setLine(self, pos):
        self.current_line = self.to_be_typed_list[pos]

    def setChapter(self, pos):
        pass

    def nextChapter(self, move_cursor=False):
        self.setChapter(self.chapter_pos + 1)

    def updateModeline(self):
        pass


class TestHighlightingService:
    def test_handleHighlighting(self):
        # This is here just to be able to use QTextBrowser, as without a
        #  QApplication Qt doesn’t let you instantiate QWidgets.
        app = QApplication(sys.argv)  # noqa: F841

        console = FakeConsole()
        book_view = FakeBookView()
        highlighting_service = HighlightingService(console,  # noqa: F841
                                                   book_view)
        cursor = book_view.cursor

        # Initial position should be 0
        assert cursor.position() == 0

        # Typing one matching character
        console.setText("s")
        assert cursor.position() == 1

        console.setText("sa")
        assert cursor.position() == 1

        console.setText("so")
        assert cursor.position() == 2

        # Typing one non-matching character
        console.setText("a")
        assert cursor.position() == 0

        # Next line
        console.setText("some test text")
        # Should be 1 higher than text len due to new line
        assert cursor.position() == 15

        console.setText("")
        assert cursor.position() == 15

        console.setText("ne")
        assert cursor.position() == 17

        console.setText("")
        assert cursor.position() == 15
