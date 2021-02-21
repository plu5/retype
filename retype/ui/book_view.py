from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QPainter
from retype.ui.modeline import Modeline


class BookDisplay(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cursor = QTextCursor(self.document())

    def setCursor(self, cursor):
        self.cursor = cursor

    def paintEvent(self, e):
        QTextBrowser.paintEvent(self, e)
        qp = QPainter(self.viewport())
        qp.setPen(QColor('red'))
        qp.drawRect(self.cursorRect(self.cursor))
        qp.end()


class BookView(QWidget):
    def __init__(self, main_win, main_controller, parent=None):
        super().__init__(parent)
        self._main_win = main_win
        self._controller = main_controller
        self._library = self._controller._library
        self._initUI()
        self.chapter_pos = 0

    def _initUI(self):
        self.display = BookDisplay(self)

        self._initModeline()

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.display)
        self.layout.addWidget(self.modeline)
        self.setLayout(self.layout)

    def _initModeline(self):
        self.modeline = Modeline(self)
        self.modeline.setTitle('No book loaded')

    def updateModeline(self):
        self.modeline.setTitle(self.book.title)
        self.modeline.setCursorPos(self.cursor_pos)
        self.modeline.setLinePos(self.line_pos)
        self.modeline.setChapPos(self.chapter_pos)
        self.modeline.repaint()

    def _initHighlighting(self):  # bad name. initChapter?
        self.cursor_pos = 0
        self.line_pos = 0
        self.persistent_pos = 0
        self._cleanText()
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor('yellow'))
        self.unhighlight_format = QTextCharFormat()  # temp
        self.unhighlight_format.setBackground(QColor('white'))  #
        self.cursor = QTextCursor(self.display.document())
        self.cursor.setPosition(self.cursor_pos, self.cursor.KeepAnchor)
        self.display.setCursor(self.cursor)

    def setContents(self, content):
        try:
            self.display.setHtml(str(content, 'utf-8'))
            self._initHighlighting()  # is this really best here
            self.updateModeline()  #
            #self.testImage4()  # temp
        except IndexError:
            self.display.setHtml("No book loaded")

    def setBook(self, book):
        self.book = book

    def _cleanText(self):  # bad name
        to_be_typed_raw = self.display.toPlainText()
        # replacements (do this better)
        to_be_typed_raw = to_be_typed_raw.replace('\ufffc', ' ')
        self.to_be_typed_list = to_be_typed_raw.splitlines()
        self.setSentence(self.line_pos)

    def setSentence(self, pos):
        self.current_sentence = self.to_be_typed_list[pos]

    def setChapter(self, pos):
        self.chapter_pos = pos  #
        self.setContents(self.book.chapters[pos].content)
        self._initHighlighting()

    def nextChapter(self):
        self.setChapter(self.chapter_pos + 1)

    def previousChapter(self):
        self.setChapter(self.chapter_pos - 1)
