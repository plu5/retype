from PyQt5.Qt import (QWidget, QVBoxLayout, QTextBrowser, QTextDocument, QUrl,
                      QTextCursor, QTextCharFormat, QColor, QPainter, QPixmap)

from retype.ui.modeline import Modeline


class BookDisplay(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cursor = QTextCursor(self.document())
        self.setOpenLinks(False)

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

        self.chapter_pos = None

    def _initUI(self):
        self.display = BookDisplay(self)
        self.display.anchorClicked.connect(self.anchorClicked)

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

    def _initChapter(self):
        if not self.chapter_pos:
            self.chapter_pos = 0
        # Character position in chapter
        self.cursor_pos = 0
        # We split the text of the chapter on new lines, and for each line the
        #  user types correctly, the `cursor_pos' is added to `persistent_pos'
        #  and the console is cleared. We use the `line_pos' to set what line
        #  needs to be typed at the moment; this corresponds to the index of
        #  the line in `to_be_typed_list'
        self.line_pos = 0
        self.persistent_pos = 0

        to_be_typed_raw = self.display.toPlainText()
        # replacements (do this better)
        to_be_typed_raw = to_be_typed_raw.replace('\ufffc', ' ')
        self.to_be_typed_list = to_be_typed_raw.splitlines()
        self.setLine(self.line_pos)

        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor('yellow'))
        self.unhighlight_format = QTextCharFormat()
        self.unhighlight_format.setBackground(QColor('white'))
        self.setCursor()

    def setCursor(self):
        self.cursor = QTextCursor(self.display.document())
        self.cursor.setPosition(self.cursor_pos, self.cursor.KeepAnchor)
        self.display.setCursor(self.cursor)

    def setSource(self, chapter):
        document = QTextDocument()
        document.setHtml(str(chapter['raw'], 'utf-8'))

        for image in chapter['images']:
            pixmap = QPixmap()
            pixmap.loadFromData(image['raw'])
            document.addResource(QTextDocument.ImageResource,
                                 QUrl(image['link']), pixmap)

        self.display.setDocument(document)

    def anchorClicked(self, link):
        pos = self.book.chapter_lookup[link.fileName()]
        self.setSource(self.book.chapters[pos])
        if pos == self.chapter_pos:
            self.setCursor()
            self.cursor.mergeCharFormat(self.highlight_format)

    def setBook(self, book):
        self.book = book

    def setChapter(self, pos):
        self.chapter_pos = pos
        self.setSource(self.book.chapters[pos])
        self._initChapter()
        self.updateModeline()

    def nextChapter(self):
        self.setChapter(self.chapter_pos + 1)

    def previousChapter(self):
        self.setChapter(self.chapter_pos - 1)

    def setLine(self, pos):
        self.current_line = self.to_be_typed_list[pos]
