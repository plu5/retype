import sys
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QTextDocument, QTextCursor, QTextCharFormat, QColor
from PyQt5.QtWidgets import QApplication, QTextBrowser

from retype.console import HighlightingService


SAMPLE_CONTENT = "<html><body>some test text</body></html>"


class FakeConsole(QObject):
    textChanged = pyqtSignal(str)

    def __init__(self):
        QObject.__init__(self)

    def clear(self):
        pass

    def setText(self, text):
        self.textChanged.emit(text)


class FakeBookView(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.display = QTextBrowser()
        self.display.setHtml(SAMPLE_CONTENT)

        self.chapter_pos = 0
        self.cursor_pos = 0
        self.line_pos = 0
        self.persistent_pos = 0
        self.to_be_typed_list = self.display.toPlainText().splitlines()
        self.setSentence(self.line_pos)

        self.highlight_format = QTextCharFormat()
        self.unhighlight_format = QTextCharFormat()

        self.cursor = QTextCursor(self.display.document())
        self.cursor.setPosition(self.cursor_pos, self.cursor.KeepAnchor)

    def isVisible(self):
        return True

    def setSentence(self, pos):
        self.current_sentence = self.to_be_typed_list[pos]

    def setChapter(self, pos):
        pass

    def nextChapter(self):
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
        # Fails atm, because it only checks length and not matches. So here it
        #  sees one character in the text so cursor pos gets set to 1, even
        #  though our one character isn’t matching.
