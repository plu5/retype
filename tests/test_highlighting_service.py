from qt import QObject, pyqtSignal, QTextCursor, QTextCharFormat, QTextBrowser

from retype.extras import splittext
from retype.console import HighlightingService


SAMPLE_CONTENT = '''<html><body>some test text<br/>
<span>next line </span><br/>
again
</body></html>'''

SAMPLE_CONTENT2 = '''<html><body><br/>
begins with an empty line
<span>  </span><br/>
followed by a line of just spaces</body></html>'''


class FakeConsole(QObject):
    textChanged = pyqtSignal(str)
    submitted = pyqtSignal(str)

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
    def __init__(self, html):
        QObject.__init__(self)
        self.display = FakeBookDisplay()
        self.display.setHtml(html)

        self.chapter_pos = 0
        self.cursor_pos = 0
        self.line_pos = 0
        self.persistent_pos = 0
        self.tobetyped_list = splittext(
            self.display.toPlainText(),
            {'\n': {'keep': False}}, True, True, '\r')
        self._setLine(self.line_pos)
        self.progress = 0

        self.highlight_format = QTextCharFormat()
        self.unhighlight_format = QTextCharFormat()
        self.mistake_format = QTextCharFormat()

        self.cursor = QTextCursor(self.display.document())
        self.updateCursorPosition()
        self.mistake_cursor = QTextCursor(self.display.document())
        self.mistake_cursor.setPosition(self.cursor_pos)
        self.highlight_cursor = QTextCursor(self.display.document())

    def isVisible(self):
        return True

    def _setLine(self, pos):
        self.current_line = self.tobetyped_list[pos]

    def setChapter(self, pos):
        pass

    def nextChapter(self, move_cursor=False):
        self.setChapter(self.chapter_pos + 1)

    def updateModeline(self):
        pass

    def updateProgress(self):
        pass

    def onLastChapter(self):
        return False

    def updateCursorPosition(self):
        self.cursor.setPosition(self.cursor_pos)

    def updateHighlightCursor(self):
        pass


def _setup(book_view_content=SAMPLE_CONTENT):
    console = FakeConsole()
    book_view = FakeBookView(book_view_content)
    service = HighlightingService(console, book_view)
    cursor = book_view.cursor
    return (console, book_view, service, cursor)


class TestHighlightingService:
    def test_handleHighlighting(self):
        (console, _, service, cursor) = _setup()

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

        # Trailing spaces should be skipped
        console.setText("next line")
        assert cursor.position() == 26

    def test_skipEmptyLines(self):
        (console, _, service, cursor) = _setup(SAMPLE_CONTENT2)

        console.setText("")
        assert cursor.position() == 1

        t = "begins with an empty line"
        console.setText(t)
        assert cursor.position() == 1 + (len(t) - 1) + 3

    def test_handleMistakes(self):
        (console, v, service, cursor) = _setup(SAMPLE_CONTENT)
        mistake_cursor = v.mistake_cursor

        assert mistake_cursor.position() == 0
        assert service.wrong is False

        console.setText("a")
        assert mistake_cursor.position() == 1
        assert service.wrong is True
        assert service.wrong_text == "a"
        assert service.wrong_start == 0

        console.setText("b")
        assert service.wrong_text == "b"
        assert mistake_cursor.position() == 1
        assert service.wrong is True

        console.setText("")
        assert service.wrong is False
        assert service.wrong_text == ""
        assert mistake_cursor.position() == 0

        console.setText("abcd")
        assert mistake_cursor.position() == 4
        assert service.wrong is True
        assert service.wrong_text == "abcd"

        console.setText("abc")
        assert service.wrong_text == "abc"
        assert mistake_cursor.position() == 3
        assert service.wrong is True

        console.setText("a")
        assert service.wrong_text == "a"
        assert mistake_cursor.position() == 1
        assert service.wrong is True
        assert service.wrong_start == 0
        assert service.wrong_end == 1

        console.setText("abcdefghijklmnopqrstuvwxyz")
        assert mistake_cursor.position() == 26
        assert service.wrong_start == 0
        assert service.wrong_end == 26

        console.setText("")
        assert service.wrong is False
        assert mistake_cursor.position() == 0
        assert service.wrong_start is None
        assert service.wrong_end is None

        console.setText("abcdefghijklmnopqrstuvwxyz")
        console.setText("bcdefghijklmnopqrstuvwxyz")
        assert service.wrong_text == "bcdefghijklmnopqrstuvwxyz"
        console.setText("bcdefghiqrstuvwxyz")
        assert service.wrong_start == 0
        assert service.wrong_end == 18
        assert service.wrong_text == "bcdefghiqrstuvwxyz"

        # starting with actual correct text
        console.setText("some test")
        assert service.wrong is False
        assert service.wrong_text == ""
        assert service.wrong_start is None
        assert cursor.position() == 9
        # now we make a little typo
        console.setText("some testd")
        assert service.wrong is True
        assert service.wrong_text == "d"
        assert service.wrong_start == 9
        assert cursor.position() == 9
        # now we correct
        console.setText("some test")
        assert service.wrong is False
        assert service.wrong_text == ""
        assert service.wrong_start is None
        assert cursor.position() == 9

    def test_handleMistakes_deleting_from_front(self):
        (console, v, service, cursor) = _setup(SAMPLE_CONTENT)

        def getFirstLine():
            text = v.display.document().toPlainText()
            return text.split('\n')[0]

        console.setText("some test")
        console.setText("ome test")
        assert service.wrong is True
        assert service.wrong_text == "ome test"
        assert service.wrong_start == 0
        assert cursor.position() == 0
        assert getFirstLine() == "ome testsome test text"
