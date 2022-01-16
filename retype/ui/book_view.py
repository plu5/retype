import logging
from PyQt5.Qt import (QWidget, QVBoxLayout, QTextBrowser, QTextDocument, QUrl,
                      QTextCursor, QTextCharFormat, QColor, QPainter, QPixmap,
                      QToolBar, QFont, QKeySequence, Qt, QApplication,
                      pyqtSignal, QSplitter, QSize)

from retype.extras.utils import isspaceorempty
from retype.ui.modeline import Modeline
from retype.extras import ManifoldStr
from retype.stats import StatsDock
from retype.resource_handler import getIcon

logger = logging.getLogger(__name__)


class BookDisplay(QTextBrowser):
    keyPressed = pyqtSignal(object)

    def __init__(self, font_size=12, parent=None):
        super().__init__(parent)
        self.cursor = QTextCursor(self.document())
        self.setOpenLinks(False)
        self.font_size = font_size
        self.updateFont()

    def setCursor(self, cursor):
        self.cursor = cursor

    def updateFont(self):
        font = QFont("Times New Roman", self.font_size)
        self.setFont(font)
        self.document().setDefaultFont(font)

    def setFontSize(self, val):
        self.font_size = val
        self.updateFont()

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
        cursor_relative_y = self.cursorRect(self.cursor).y()
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(
            scrollbar.value() + cursor_relative_y -
            viewport_height/2 + cursor_height/2)

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
    def __init__(self, main_win, main_controller, rdict,
                 bookview_settings=None, parent=None):
        super().__init__(parent)
        self._main_win = main_win
        main_win.closing.connect(self.maybeSave)
        self._controller = main_controller
        self._library = self._controller.library
        self._console = self._controller.console
        self.font_size = bookview_settings.get('font_size')
        self._initUI()

        self.rdict = rdict

        self.book = None
        self.cursor = None
        self.chapter_pos = None
        self.line_pos = None
        self.persistent_pos = None
        self.progress = None
        self.chapter_lens = None
        self.total_len = None

        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor('yellow'))
        self.unhighlight_format = QTextCharFormat()
        self.unhighlight_format.setBackground(QColor('white'))
        self.mistake_format = QTextCharFormat()
        self.mistake_format.setBackground(QColor('red'))
        self.mistake_format.setForeground(QColor('white'))

    def _initUI(self):
        self.display = BookDisplay(self.font_size, self)
        self.display.anchorClicked.connect(self.anchorClicked)
        self.display.keyPressed.connect(self._controller.console.transferFocus)

        self._initToolbar()
        self._initModeline()

        self.layout_ = QVBoxLayout()
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(0)

        self.splitter = QSplitter()
        self.splitter.setHandleWidth(2)
        self.splitter.setOrientation(Qt.Vertical)
        self.splitter.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.display)

        self._main_win.denoteSplitter('bookview', self.splitter)

        self.stats_dock = StatsDock()
        self.splitter.addWidget(self.stats_dock)
        self._main_win.maybeRestoreSplitterState('bookview')

        self.layout_.addWidget(self.toolbar)
        self.layout_.addWidget(self.splitter)
        self.layout_.addWidget(self.modeline)
        self.setLayout(self.layout_)

    def _initToolbar(self):
        self.toolbar = QToolBar(self)
        self.toolbar.setIconSize(QSize(16, 16))

        actions = {
            'back':
            {
                'name': 'Back to shelves',
                'func': self.switchToShelves
            },
            'pos':
            {
                'name': 'Cursor position',
                'func': self.gotoCursorPosition,
                'tooltip': 'Go to the cursor position. Hold Ctrl to move cursor\
 to your current position',
                'icon': 'cursor'
            },
            'pchap':
            {
                'name': 'Previous chapter',
                'func': self.previousChapterAction,
                'tooltip': 'Go to the previous chapter. Hold Ctrl to move\
 cursor with you as well',
                'icon': 'arrow-left'
            },
            'nchap':
            {
                'name': 'Next chapter',
                'func': self.nextChapterAction,
                'tooltip': 'Go to the next chapter. Hold Ctrl to move cursor\
 with you as well',
                'icon': 'arrow-right'
            },
            'skip':
            {
                'name': 'Skip line',
                'func': self.advanceLine,
                'tooltip': 'Move cursor to next line',
                'icon': 'skip'
            },
            'zoomin':
            {
                'name': 'Increase font size',
                'func': self.display.zoomIn,
                'shortcut': QKeySequence(QKeySequence.StandardKey.ZoomIn),
                'icon': 't-up'
            },
            'zoomout':
            {
                'name': 'Decrease font size',
                'func': self.display.zoomOut,
                'shortcut': QKeySequence(QKeySequence.StandardKey.ZoomOut),
                'icon': 't-down'
            }
        }

        def addAction(name, func, tooltip=None, shortcut=None, icon=None):
            a = self.toolbar.addAction(name, func)
            if tooltip:
                a.setToolTip(tooltip)
            if shortcut:
                a.setShortcut(shortcut)
            if icon:
                a.setIcon(getIcon(icon))
            return a

        for k, v in actions.items():
            action = addAction(**v)
            actions[k]['action'] = action

        self.pchap_action = actions['pchap']['action']
        self.nchap_action = actions['nchap']['action']

        self.toolbar.insertSeparator(actions['pos']['action'])

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
            chap_total=len(self.book.chapters) - 1,
            progress=int(self.progress),
        )

    def _initChapter(self, reset=True):
        if not self.chapter_pos:
            self.chapter_pos = 0
            # This is the position of the chapter on actual display, which may
            #  not be the same as the chapter the cursor is on
            self.viewed_chapter_pos = 0

        # We split the text of the chapter on new lines, and for each line the
        #  user types correctly, the `cursor_pos' (character position in
        #  chapter) is added to `persistent_pos' and the console is cleared.
        # We use the `line_pos' to set what line needs to be typed
        #  at the moment; this corresponds to the index of the line
        #  in `tobetyped_list'.
        if not self.line_pos or reset:
            self.cursor_pos = 0
            self.line_pos = 0
            self.persistent_pos = 0

        if not self.progress:
            self.progress = 0

        self.setCursor()

        self.tobetyped = self.book.chapters[self.chapter_pos]['plain']
        self.tobetyped_list = self.tobetyped.splitlines()
        self._setLine(self.line_pos)

    def setCursor(self):
        self.cursor = QTextCursor(self.display.document())
        self.updateCursorPosition()
        self.display.setCursor(self.cursor)

        self.highlight_cursor = QTextCursor(self.display.document())
        self.updateHighlightCursor()

        self.mistake_cursor = QTextCursor(self.display.document())
        self.mistake_cursor.setPosition(self.cursor_pos)

    def updateCursorPosition(self):
        self.cursor.setPosition(self.cursor_pos)

    def updateHighlightCursor(self):
        self.highlight_cursor.setPosition(self.cursor_pos,
                                          self.cursor.KeepAnchor)
        self.highlight_cursor.mergeCharFormat(self.unhighlight_format)
        self.highlight_cursor.mergeCharFormat(self.highlight_format)

    def setSource(self, chapter):
        document = QTextDocument()
        document.setHtml(chapter['html'])

        for image in chapter['images']:
            pixmap = QPixmap()
            pixmap.loadFromData(image['raw'])
            document.addResource(QTextDocument.ImageResource,
                                 QUrl(image['link']), pixmap)

        self.display.setDocument(document)

    def anchorClicked(self, link):
        f = link.fileName()
        if f in self.book.chapter_lookup:
            pos = self.book.chapter_lookup[f]
            self.setChapter(pos)
        else:
            logger.error("{} not found".format(f))

    def setBook(self, book, save_data=None):
        self.book = book
        if save_data:
            for p, v in save_data.items():
                self.__dict__[p] = v
            self.cursor_pos = self.persistent_pos
            reset = False
        else:
            self.chapter_pos = 0
            reset = True

        self.chapter_lens = [chapter['len'] for chapter in self.book.chapters]
        self.total_len = sum(self.chapter_lens)

        if not self.stats_dock.connected:
            self.stats_dock.connectConsole(self._controller.console)

        complete = book.progress == 100

        self.setChapter(self.chapter_pos, True, reset)

        if complete:
            self.markComplete()

    def setChapter(self, pos, move_cursor=False, reset=True):
        self.setSource(self.book.chapters[pos])
        self.viewed_chapter_pos = pos
        if move_cursor:
            self.chapter_pos = pos
            self._initChapter(reset)
            if isspaceorempty(self.tobetyped):
                logger.info("Skipping empty chapter")
                self.setChapter(pos + 1, move_cursor)
            self.updateProgress()
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
        if self.tobetyped_list:
            if self.line_pos > len(self.tobetyped_list):
                return logger.warning("line_pos out of range")
            if self.rdict:
                self.current_line = ManifoldStr(self.tobetyped_list[pos],
                                                self.rdict)
            else:
                self.current_line = self.tobetyped_list[pos]

            if isspaceorempty(self.current_line):
                logger.info("Skipping empty line")
                self.advanceLine()
        else:
            logger.error("Bad tobetyped_list; {}".format(self.tobetyped_list))

    def advanceLine(self):
        self._controller.console.command_service.advanceLine()

    def maybeSave(self):
        if self.book:
            key = self.book.path
            data = {'persistent_pos': self.persistent_pos,
                    'line_pos': self.line_pos,
                    'chapter_pos': self.chapter_pos,
                    'progress': self.progress}
            self._library.save(self.book, key, data)

    def switchToShelves(self):
        self.maybeSave()
        self._controller.console.command_service.switch('shelves')

    def gotoCursorPosition(self, move=False):
        if QApplication.instance().keyboardModifiers() == Qt.ControlModifier\
           or move:
            self.setChapter(self.viewed_chapter_pos, True)
            self.updateProgress()
        else:
            self.setChapter(self.chapter_pos)
            self.setCursor()
            self.display.centreAroundCursor()

    def updateToolbarActions(self):
        self.nchap_action.setDisabled(False)
        self.pchap_action.setDisabled(False)
        if self.viewed_chapter_pos == len(self.book.chapters) - 1:
            self.nchap_action.setDisabled(True)
        elif self.viewed_chapter_pos == 0:
            self.pchap_action.setDisabled(True)

    def updateProgress(self):
        if not self.chapter_lens:
            return

        typed = self.persistent_pos
        for chapter_len in self.chapter_lens[0:self.chapter_pos]:
            typed += chapter_len

        self.progress = (typed / self.total_len) * 100
        self.book.updateProgress(self.progress)

    def setFontSize(self, val):
        self.font_size = val
        self.display.setFontSize(val)

    def getFontSize(self):
        return self.display.font_size

    def onLastChapter(self):
        return self.chapter_pos == len(self.book.chapters)-1

    def markComplete(self):
        self.cursor_pos = self.persistent_pos = len(self.tobetyped)
        self.setCursor()
        self.progress = 100
        self.book.updateProgress(self.progress)
        self.updateModeline()
