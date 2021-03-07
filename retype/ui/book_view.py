from PyQt5.Qt import (QWidget, QVBoxLayout, QTextBrowser, QTextDocument, QUrl,
                      QTextCursor, QTextCharFormat, QColor, QPainter, QPixmap,
                      QToolBar, QFont, QKeySequence, Qt, QApplication,
                      pyqtSignal)

from retype.ui.modeline import Modeline


class BookDisplay(QTextBrowser):
    keyPressed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cursor = QTextCursor(self.document())
        self.setOpenLinks(False)
        self.font_size = 12
        self.updateFont()

    def setCursor(self, cursor):
        self.cursor = cursor

    def updateFont(self):
        font = QFont("Times New Roman", self.font_size)
        self.setFont(font)
        self.document().setDefaultFont(font)

    def paintEvent(self, e):
        QTextBrowser.paintEvent(self, e)
        qp = QPainter(self.viewport())
        qp.setPen(QColor('red'))
        qp.drawRect(self.cursorRect(self.cursor))
        qp.end()

    def keyPressEvent(self, e):
        self.keyPressed.emit(e)
        QTextBrowser.keyPressEvent(self, e)

    def centreAroundCursor(self):
        viewport_height = self.viewport().rect().height()
        cursor_height = self.cursorRect(self.cursor).height()
        block = self.document().findBlock(self.cursor.position())
        cursor_absolute_y = self.document().documentLayout()\
                                           .blockBoundingRect(block).y()

        calculated_value = cursor_absolute_y - (viewport_height / 2) +\
            (cursor_height / 2)
        self.verticalScrollBar().setValue(calculated_value)

    def zoomIn(self, range_=1):
        self.font_size += range_
        QTextBrowser.zoomIn(self, range_)
        self.updateFont()

    def zoomOut(self, range_=-1):
        self.font_size += range_
        QTextBrowser.zoomOut(self, range_)
        self.updateFont()

    def wheelEvent(self, e):
        if e.modifiers() == Qt.ControlModifier:
            if e.angleDelta().y() > 0:
                self.zoomIn()
            else:
                self.zoomOut()
        QTextBrowser.wheelEvent(self, e)


class BookView(QWidget):
    def __init__(self, main_win, main_controller, parent=None):
        super().__init__(parent)
        self._main_win = main_win
        self._controller = main_controller
        self._library = self._controller._library
        self._initUI()

        self.chapter_pos = None

    def _initUI(self):
        self.toolbar = QToolBar(self)
        self.toolbar.addAction("Back to shelves",
                               self.switchToShelves)
        a = self.toolbar.addAction("Cursor position",
                                   self.gotoCursorPosition)
        a.setToolTip("Go to the cursor position. Hold Ctrl to move cursor\
 to your current position")
        a = self.toolbar.addAction("Previous chapter",
                                   self.previousChapterAction)
        a.setToolTip("Go to the previous chapter. Hold Ctrl to move cursor\
 with you as well")
        self.pchap_action = a
        a = self.toolbar.addAction("Next chapter",
                                   self.nextChapterAction)
        a.setToolTip("Go to the next chapter. Hold Ctrl to move cursor\
 with you as well")
        self.nchap_action = a

        a = self.toolbar.addAction("Skip line", self.advanceLine)
        a.setToolTip("Move cursor to next line")

        self.display = BookDisplay(self)
        self.display.anchorClicked.connect(self.anchorClicked)
        self.display.keyPressed.connect(self._controller.console.transferFocus)

        a = self.toolbar.addAction("Increase font size", self.display.zoomIn)
        a.setShortcut(QKeySequence(QKeySequence.StandardKey.ZoomIn))
        a = self.toolbar.addAction("Decrease font size", self.display.zoomOut)
        a.setShortcut(QKeySequence(QKeySequence.StandardKey.ZoomOut))

        self._initModeline()

        self.layout_ = QVBoxLayout()
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(0)
        self.layout_.addWidget(self.toolbar)
        self.layout_.addWidget(self.display)
        self.layout_.addWidget(self.modeline)
        self.setLayout(self.layout_)

    def _initModeline(self):
        self.modeline = Modeline(self)
        self.modeline.update_(title="No book loaded")

    def updateModeline(self):
        self.modeline.update_(
            title=self.book.title,
            path=self.book.path,
            cursor_pos=self.cursor_pos,
            line_pos=self.line_pos,
            chap_pos=self.chapter_pos,
            viewed_chap_pos=self.viewed_chapter_pos,
            chap_total=len(self.book.chapters) - 1
        )

    def _initChapter(self):
        if not self.chapter_pos:
            self.chapter_pos = 0
            # This is the position of the chapter on actual display, which may
            #  not be the same as the chapter the cursor is on
            self.viewed_chapter_pos = 0
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
        self._setLine(self.line_pos)

        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor('yellow'))
        self.unhighlight_format = QTextCharFormat()
        self.unhighlight_format.setBackground(QColor('white'))
        self.setCursor()

    def setCursor(self):
        self.cursor = QTextCursor(self.display.document())
        self.cursor.setPosition(self.cursor_pos, self.cursor.KeepAnchor)
        self.display.setCursor(self.cursor)
        self.cursor.mergeCharFormat(self.highlight_format)

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
        self.setChapter(pos)

    def setBook(self, book):
        self.book = book

    def setChapter(self, pos, move_cursor=False):
        self.setSource(self.book.chapters[pos])
        self.viewed_chapter_pos = pos
        if move_cursor:
            self.chapter_pos = pos
            self._initChapter()
        elif pos == self.chapter_pos:
            self.setCursor()
        self.updateModeline()
        self.display.updateFont()
        self.updateToolbarActions()

    def nextChapter(self, move_cursor=False):
        pos = self.chapter_pos + 1 if move_cursor \
            else self.viewed_chapter_pos + 1
        if pos >= len(self.book.chapters):
            return
        self.setChapter(pos, move_cursor)

    def previousChapter(self, move_cursor=False):
        pos = self.chapter_pos - 1 if move_cursor \
            else self.viewed_chapter_pos - 1
        if pos < 0:
            return
        self.setChapter(pos, move_cursor)

    def nextChapterAction(self):
        if (QApplication.instance().keyboardModifiers() == Qt.ControlModifier):
            self.nextChapter(True)
        else:
            self.nextChapter(False)

    def previousChapterAction(self):
        if (QApplication.instance().keyboardModifiers() == Qt.ControlModifier):
            self.previousChapter(True)
        else:
            self.previousChapter(False)

    def _setLine(self, pos):
        if self.to_be_typed_list:
            self.current_line = self.to_be_typed_list[pos]

    def advanceLine(self):
        self._controller.console.command_service.advanceLine()

    def switchToShelves(self):
        self._controller.console.command_service.switch('shelves')

    def gotoCursorPosition(self, move=False):
        if QApplication.instance().keyboardModifiers() == Qt.ControlModifier\
           or move:
            self.setChapter(self.viewed_chapter_pos, True)
        else:
            self.setChapter(self.chapter_pos)
            self.setCursor()

    def updateToolbarActions(self):
        self.nchap_action.setDisabled(False)
        self.pchap_action.setDisabled(False)
        if self.viewed_chapter_pos == len(self.book.chapters) - 1:
            self.nchap_action.setDisabled(True)
        elif self.viewed_chapter_pos == 0:
            self.pchap_action.setDisabled(True)
