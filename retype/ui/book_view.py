import logging
from qt import (QWidget, QVBoxLayout, QTextBrowser, QTextDocument, QUrl,
                QTextCursor, QTextCharFormat, QPainter, QPixmap,
                QToolBar, QFont, QKeySequence, Qt, QApplication, pyqtSignal,
                QSplitter, QSize)

from retype.extras import splittext, isspaceorempty, ManifoldStr
from retype.ui.modeline import Modeline
from retype.services import Autosave
from retype.stats import StatsDock
from retype.resource_handler import getIcon
from retype.services.theme import theme, C, Theme

logger = logging.getLogger(__name__)


@theme('BookView.BookDisplay',
       C(fg='black', bg='#F6F1DE', sel_bg='grey', t_border='white',
         b_border='white', l_border='white', r_border='white'))
@theme('BookView.BookDisplay.Cursor', C(fg='red'))
class BookDisplay(QTextBrowser):
    keyPressed = pyqtSignal(object)
    fontChanged = pyqtSignal()

    def __init__(self, font_family, font_size=12, parent=None):
        super().__init__(parent)
        self.cursor = QTextCursor(self.document())
        self.setOpenLinks(False)
        self.setOpenExternalLinks(True)
        self.font = QFont(font_family, font_size)
        self._font_size = font_size
        self._font_family = font_family
        self.updateFont()

        self.c_display, self.c_cursor = self._loadTheme()
        self.c_display.changed.connect(self.themeUpdate)
        self.themeUpdate()

    def _loadTheme(self):
        return (Theme.get('BookView.BookDisplay'),
                Theme.get('BookView.BookDisplay.Cursor'))

    def themeUpdate(self):
        qss = Theme.getQss('BookView.BookDisplay').replace(
            'BookView.BookDisplay', 'QTextBrowser')
        self.setStyleSheet(qss)

    def setCursor(self, cursor):
        self.cursor = cursor

    def updateFont(self):
        self.font.setPixelSize(self.font_size)
        self.setFont(self.font)
        self.document().setDefaultFont(self.font)
        self.fontChanged.emit()

    @property
    def font_size(self):
        return self._font_size

    @font_size.setter
    def font_size(self, val):
        self._font_size = val
        self.updateFont()

    @property
    def font_family(self):
        return self._font_family

    @font_family.setter
    def font_family(self, val):
        self.font.setFamily(val)
        self.updateFont()

    def paintEvent(self, e):
        QTextBrowser.paintEvent(self, e)
        qp = QPainter(self.viewport())
        qp.setPen(self.c_cursor.fg())
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
        if e.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if e.angleDelta().y() > 0:
                self.zoomIn()
            else:
                self.zoomOut()
        QTextBrowser.wheelEvent(self, e)


@theme('BookView.Highlighting.Highlight', C(fg='black', bg='yellow'))
@theme('BookView.Highlighting.Mistake', C(fg='white', bg='red'))
class BookView(QWidget):
    def __init__(self, main_win, main_controller, sdict={}, rdict={},
                 bookview_settings=None, parent=None):
        super().__init__(parent)
        self._main_win = main_win
        main_win.closing.connect(self.maybeSave)
        self._controller = main_controller
        self._library = self._controller.library
        self._console = self._controller.console
        self.autosave = Autosave(self._console)
        self.autosave.save.connect(self.maybeSave)
        self.display = BookDisplay(
            bookview_settings['font'], bookview_settings['font_size'], self)
        self._initUI()

        self.sdict = sdict
        self.rdict = rdict

        self.book = None
        self.cursor = None
        self.chapter_pos = None
        self.line_pos = None
        self.cursor_pos = None
        self.persistent_pos = None
        self.progress = None
        self.chapter_lens = None
        self.total_len = None

        self.c = self._loadTheme()

        self.highlight_sel = self.display.ExtraSelection()
        self.highlight_format = QTextCharFormat()
        self.mistake_format = QTextCharFormat()
        self.formats = (self.highlight_format, self.mistake_format)

        self.c[0].changed.connect(self.themeUpdate)
        self.themeUpdate()

    def _loadTheme(self):
        return (Theme.get('BookView.Highlighting.Highlight'),
                Theme.get('BookView.Highlighting.Mistake'))

    def themeUpdate(self):
        for f, c in zip(self.formats, self.c):
            f.setForeground(c.fg())
            f.setBackground(c.bg())

    def _initUI(self):
        self.display.anchorClicked.connect(self.anchorClicked)
        self.display.keyPressed.connect(self._controller.console.transferFocus)

        self._initToolbar()
        self._initModeline()

        self.layout_ = QVBoxLayout()
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(0)

        self.splitter = QSplitter()
        self.splitter.setHandleWidth(2)
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.splitter.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.display)

        self._main_win.denoteSplitter('bookview', self.splitter)

        self.stats_dock = StatsDock(self)
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
        self.skip_action = actions['skip']['action']

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

        # We split the text of the chapter to lines, and for each line the
        #  user types correctly, the `cursor_pos' (character position in
        #  chapter) is added to `persistent_pos' and the console is cleared.
        # We use the `line_pos' to set what line needs to be typed
        #  at the moment; this corresponds to the index of the line
        #  in `tobetyped_list'.
        if not self.cursor_pos or reset:
            self.cursor_pos = 0
            self.persistent_pos = 0

        if not self.progress:
            self.progress = 0

        self.setCursor()

        self.tobetyped = self.book.chapters[self.chapter_pos]['plain']
        self._prepTobetypedList()

        self.line_pos = self.calcLinePos(self.cursor_pos)

        self._setLine(self.line_pos)

    def _prepTobetypedList(self):
        self.tobetyped_list = splittext(self.tobetyped, self.sdict,
                                        True, True, '\r')

    def setCursor(self):
        self.cursor = QTextCursor(self.display.document())
        self.updateCursorPosition()
        self.display.setCursor(self.cursor)

        self.setHighlightCursor()

        self.setMistakeCursor()

    def setHighlightCursor(self):
        self.highlight_cursor = QTextCursor(self.display.document())
        self.updateHighlightCursor()

    def setMistakeCursor(self):
        self.mistake_cursor = QTextCursor(self.display.document())
        self.mistake_cursor.setPosition(self.cursor_pos)

    def updateCursorPosition(self, to_pos=None):
        pos = to_pos or self.cursor_pos
        self.cursor.setPosition(pos)

    def updateHighlightCursor(self, to_pos=None):
        pos = to_pos or self.cursor_pos
        self.highlight_cursor.setPosition(pos, self.cursor.KeepAnchor)
        self.highlight_sel.cursor = self.highlight_cursor
        self.highlight_sel.format = self.highlight_format
        self.display.setExtraSelections([self.highlight_sel])

        # Also required to avoid ExtraSelections segfault when switching view,
        # even if self.display.extraSelections() is an empty list
        self.highlight_cursor.setPosition(0)

    def fillHighlight(self):
        self.setHighlightCursor()
        self.updateHighlightCursor(self.chapter_lens[self.viewed_chapter_pos])

    def setSource(self, chapter):
        document = QTextDocument()
        document.setHtml(chapter['html'])

        for image in chapter['images']:
            pixmap = QPixmap()
            pixmap.loadFromData(image['raw'])
            document.addResource(QTextDocument.ImageResource,
                                 QUrl(image['link']), pixmap)

        # Extra selections must be cleared before calling setDocument to avoid
        # a crash, see https://stackoverflow.com/a/73776461/18396947
        # Thank you, Patrick Jeeves!
        self.display.setExtraSelections([])
        self.display.setDocument(document)

    def anchorClicked(self, link):
        f = link.fileName()
        if link.scheme() in ["http", "https"]:
            self._controller.openUrl(link)
        elif f in self.book.chapter_lookup:
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
        self._console.clear()
        self.setSource(self.book.chapters[pos])
        self.viewed_chapter_pos = pos
        if move_cursor:
            self.chapter_pos = pos
            self._initChapter(reset)
            if isspaceorempty(self.tobetyped):
                logger.debug("Skipping empty chapter")
                self.setChapter(pos + 1, move_cursor)
            self.updateProgress()
        elif pos == self.chapter_pos:
            self.setCursor()
        elif pos < self.chapter_pos:
            self.fillHighlight()
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
        if QApplication.instance().keyboardModifiers() == \
           Qt.KeyboardModifier.ControlModifier:
            self.nextChapter(True)
        else:
            self.nextChapter(False)

    def previousChapterAction(self):
        if QApplication.instance().keyboardModifiers() == \
           Qt.KeyboardModifier.ControlModifier:
            self.previousChapter(True)
        else:
            self.previousChapter(False)

    def calcLinePos(self, cursor_pos):
        tally = line_pos = 0
        if (not self.tobetyped_list or
                not isinstance(self.tobetyped_list, list)):
            logger.error("Bad tobetyped_list; {}".format(self.tobetyped_list))
        for line in self.tobetyped_list:
            tally += len(line)
            if tally > cursor_pos:
                break
            line_pos += 1
            self.persistent_pos = tally
        return line_pos

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
                logger.debug("Skipping empty line")
                self.advanceLine()
        else:
            logger.error("Bad tobetyped_list; {}".format(self.tobetyped_list))

    def advanceLine(self):
        self._console.clear()
        self._controller.console.command_service.advanceLine()

    def setSdict(self, sdict):
        self.sdict = sdict
        if not self.book:
            return
        self._prepTobetypedList()
        self.line_pos = self.calcLinePos(self.cursor_pos)
        self._setLine(self.line_pos)

    def setRdict(self, rdict):
        self.rdict = rdict
        if not self.book:
            return
        self._setLine(self.line_pos)

    def maybeSave(self):
        if self.book and self.book.dirty:
            logger.debug(f"Saving progress in '{self.book.title}'")
            data = {'persistent_pos': self.persistent_pos,
                    'chapter_pos': self.chapter_pos,
                    'progress': self.progress}
            self._library.save(self.book, data)

    def switchToShelves(self):
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
        if self.viewed_chapter_pos == 0:
            self.pchap_action.setDisabled(True)

    def updateProgress(self):
        if not self.chapter_lens:
            return

        typed = self.persistent_pos
        for chapter_len in self.chapter_lens[0:self.chapter_pos]:
            typed += chapter_len

        self.progress = (typed / self.total_len) * 100
        self.book.updateProgress(self.progress)
        self.book.dirty = True

    @property
    def font_size(self):
        return self.display.font_size

    @font_size.setter
    def font_size(self, val):
        self.display.font_size = val

    @property
    def font_family(self):
        return self.display.font_family

    @font_family.setter
    def font_family(self, val):
        self.display.font_family = val

    def onLastChapter(self):
        return self.chapter_pos == len(self.book.chapters)-1

    def markComplete(self):
        self.cursor_pos = self.persistent_pos = len(self.tobetyped)
        self.setCursor()
        self.progress = 100
        self.book.updateProgress(self.progress)
        self.updateModeline()
