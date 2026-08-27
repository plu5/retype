import logging
from qt import QObject, QTextCursor, QTextCharFormat, QTextBrowser

from retype.extras import splittext, isspaceorempty, ManifoldStr
from retype.console import Console, HighlightingService
from retype.constants import default_config

logger = logging.getLogger(__name__)


SAMPLE_CONTENT = '''<html><body>some test text<br/>
<span>next line </span><br/>
again
</body></html>'''


class FakeBookDisplay(QTextBrowser):
    def __init__(self):
        QTextBrowser.__init__(self)

    def centreAroundCursor(self):
        pass


class FakeBookView(QObject):
    def __init__(self, rdict=default_config.get('rdict')):
        QObject.__init__(self)
        self.display = FakeBookDisplay()
        self.rdict = rdict or {}
        self.highlight_format = QTextCharFormat()
        self.mistake_format = QTextCharFormat()
        self.cursor = QTextCursor(self.display.document())
        self.mistake_cursor = QTextCursor(self.display.document())
        self.highlight_cursor = QTextCursor(self.display.document())
        self.progress = 0

    def _initChapter(self, html):
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

        self.updateCursorPosition()
        self.mistake_cursor.setPosition(self.cursor_pos)

    def isVisible(self):
        return True

    def advanceLine(self):
        self.h.advanceLine()

    def _setLine(self, pos):
        if self.tobetyped_list:
            if self.line_pos is not None and \
               self.line_pos > len(self.tobetyped_list):
                return logger.warning("line_pos out of range")
            if self.rdict:
                self.current_line = ManifoldStr(
                    self.tobetyped_list[pos],
                    self.rdict)  # type: str | ManifoldStr
            else:
                self.current_line = self.tobetyped_list[pos]

            if isspaceorempty(self.current_line):
                logger.debug("Skipping empty line")
                self.advanceLine()
        else:
            logger.error("Bad tobetyped_list; {}".format(self.tobetyped_list))

    def setChapter(self, pos):
        self.chapter_pos = pos

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
    console = Console('>')
    book_view = FakeBookView()
    service = HighlightingService(console, book_view)
    book_view.h = service  # to be able to call advanceLine
    book_view._initChapter(book_view_content)
    cursor = book_view.cursor
    return (console, book_view, service, cursor)


class TestHighlightingPlusConsolePlusManifold:
    def test_ends_with_empty_line(self):
        SAMPLE = '''<html><body>hi<br/>  </body></html>'''
        (console, v, service, cursor) = _setup(SAMPLE)

        assert v.chapter_pos == 0
        console.setText("hi")
        assert v.chapter_pos == 1, "chapter pos should advance"
