import logging
from qt import (QWidget, QVBoxLayout, QPainter, Qt, QColor, QEvent, QPixmap,
                QSize, QFontMetrics, QRectF)

from typing import TYPE_CHECKING

from retype.layouts import ShelvesWidget
from retype.ui import Cover
from retype.ui.painting import rectPixmap, linePixmap, textPixmap, Font
from retype.services.theme import theme, C, Theme

logger = logging.getLogger(__name__)


@theme('ShelfView.Background',
       C(bg='#F0F0F0', outline='#555', l_border='#A9A9A9', r_border='#A9A9A9'))
@theme('ShelfView.Shelf',
       C(fg='#B5B5B5', bg='#A9A9A9', t_border='#CACACA', l_border='#555',
         r_border='#555', b_border='#555'))
@theme('ShelfView.Top',
       C(t_border='#A1A0A0', b_border='#555'))
class ShelfView(QWidget):
    def __init__(self, main_win, main_controller, parent=None):
        # type: (ShelfView, MainWin, MainController, QWidget | None) -> None
        super().__init__(parent)
        self._parent = parent
        self._controller = main_controller
        self._library = self._controller.library
        self.c_background, self.c_shelf, self.c_top = self._loadTheme()
        self.c_background.changed.connect(self.themeUpdate)
        self._initUI()

    def _loadTheme(self):
        # type: (ShelfView) -> tuple[C, ...]
        return (Theme.get('ShelfView.Background'),
                Theme.get('ShelfView.Shelf'),
                Theme.get('ShelfView.Top'))

    def themeUpdate(self):
        # type: (ShelfView) -> None
        self.update()

    def _initUI(self):
        # type: (ShelfView) -> None
        self.cell_dimensions = (150, 200, 232)  # min width, max width, height
        self.shelf_height = self.cell_dimensions[2]

        self.shelves = ShelvesWidget(self, *self.cell_dimensions)
        self.shelves.setContentsMargins(10, 15, 15, 10)
        self.shelves.container.installEventFilter(self)

        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.addWidget(self.shelves)

    def _populate(self):
        # type: (ShelfView) -> None
        if self._library.books is None:
            logger.error('_populate: _library.books is None')
            return
        for book in self._library.books.values():
            loadBook = self._controller.loadBookRequested
            item = ShelfItem(book, loadBook)
            if item.book.valid:
                self.shelves.addWidget(item)
            else:
                logger.warning("_populate: skipping invalid book "
                               f"{item.book.idn}:{item.book.path}")

    def repopulate(self):
        # type: (ShelfView) -> None
        self.shelves.clearWidgets()
        self._populate()

    def keyPressEvent(self, e):
        # type: (ShelfView, QKeyEvent) -> None
        self._controller.console.transferFocus(e)
        QWidget.keyPressEvent(self, e)

    def eventFilter(self, watched, event):
        # type: (ShelfView, QObject, QEvent) -> bool
        if watched == self.shelves.container and\
           event.type() == QEvent.Type.Paint:
            o = (0, 0)
            assert isinstance(watched, QWidget)
            (w, h) = (watched.size().width(), watched.size().height())
            top_shelf_y = self.shelf_height + 5
            deepness = 10
            inset = 4
            front_h = 10

            outline_colour = self.c_background.outline()
            background_colour = self.c_background.bg()
            border_left_colour = self.c_background.l_border()
            border_right_colour = self.c_background.r_border()
            shelf_colour = self.c_shelf.fg()
            shelf_background_colour = self.c_shelf.bg()
            shelf_border_top_colour = self.c_shelf.t_border()
            shelf_border_left_colour = self.c_shelf.l_border()
            shelf_border_right_colour = self.c_shelf.r_border()
            shelf_border_bottom_colour = self.c_shelf.b_border()
            top_border_top_colour = self.c_top.t_border()
            top_border_bottom_colour = self.c_top.b_border()

            qp = QPainter(watched)
            draw = qp.drawPixmap

            draw(*o, rectPixmap(w, h, background_colour, background_colour))
            draw(*o, rectPixmap(10, h, border_left_colour, border_left_colour))
            draw(w - 11, 0, rectPixmap(
                10, h, border_right_colour, border_right_colour))
            outline = rectPixmap(2, h, outline_colour, background_colour)
            draw(10, 0, outline)
            draw(w - 13, 0, outline)

            def shelf():
                # type: () -> QPixmap
                pixmap = QPixmap(w, h)
                pixmap.fill(QColor('transparent'))
                qp = QPainter(pixmap)
                draw = qp.drawPixmap
                # Top
                draw(0, 3, rectPixmap(w, deepness, shelf_background_colour,
                                      shelf_background_colour))
                # Front
                draw(inset, deepness + 3, rectPixmap(w - 10, 10, shelf_colour,
                                                     shelf_colour))
                # Front outline
                draw(12, 0, rectPixmap(w - 25, 2,
                                       outline_colour, background_colour))
                draw(inset, deepness + 3,
                     linePixmap(w - 7, 0, shelf_border_top_colour, 4))
                draw(inset, deepness + 3 + front_h,
                     linePixmap(w - 7, 0, shelf_border_bottom_colour, 4))
                draw(3, deepness + 3,
                     linePixmap(0, 11, shelf_border_left_colour, 4))
                draw(w - 5, deepness + 3,
                     linePixmap(0, 11, shelf_border_right_colour, 4))
                return pixmap

            shelf_pixmap = shelf()

            shelf_y = top_shelf_y - 3
            while shelf_y < h:
                draw(0, shelf_y, shelf_pixmap)
                shelf_y += self.shelf_height

            # The rectangles at the very top
            draw(*o, rectPixmap(
                w, 20, top_border_top_colour, top_border_top_colour))
            draw(0, 20, rectPixmap(
                w, 3, top_border_bottom_colour, top_border_bottom_colour))

            return True
        return super().eventFilter(watched, event)


class ShelfItem(QWidget):
    def __init__(self, book, loadBook, parent=None):
        # type: (ShelfItem, BookWrapper, pyqtBoundSignal, QWidget|None) -> None
        super().__init__(parent)
        self.book = book
        self.idn = book.idn
        self.cover = Cover(book, self)
        self.loadBook = loadBook
        self.progress = self.book.progress or 0.0
        self._initUI()

    def _initUI(self):
        # type: (ShelfItem) -> None
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(0)
        self.layout_.addWidget(IDNDisplay(self.idn, self.cover.w))
        self.layout_.addWidget(self.cover)
        self.progress_bar = ProgressBar(self.cover.w, self.progress)
        self.book.progress_subscribers.append(self.progress_bar.update_)
        self.layout_.addWidget(self.progress_bar)

    def mouseReleaseEvent(self, e):
        # type: (ShelfItem, QMouseEvent) -> None
        self.loadBook.emit(self.book.idn)


@theme('ShelfView.IDNDisplay', C(fg='gray'))
class IDNDisplay(QWidget):
    def __init__(self, idn, w):
        # type: (IDNDisplay, int, int) -> None
        super().__init__()
        self._idn = idn
        self._font = Font.GENERAL.toQFont()
        self._w = w
        self._h = 20
        self._bottom_margin = 2
        self.c = self._loadTheme()
        self._pixmap = self.pixmap()

    def _loadTheme(self):
        # type: (IDNDisplay) -> C
        return Theme.get('ShelfView.IDNDisplay')

    def pixmap(self):
        # type: (IDNDisplay) -> QPixmap
        font = self._font
        fm = QFontMetrics(font)
        descent = fm.descent()
        bounding_rect = QRectF(
            0, 0, self._w, self._h + descent - self._bottom_margin)
        return textPixmap(
            str(self._idn), self._w, self._h, font, self.c.fg(),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
            bounding_rect)

    def paintEvent(self, e):
        # type: (IDNDisplay, QPaintEvent) -> None
        qp = QPainter(self)
        qp.drawPixmap(0, 0, self._pixmap)

    def sizeHint(self):
        # type: (IDNDisplay) -> QSize
        return QSize(self._w, self._h)


@theme('ShelfView.ProgressBar', C(fg='yellow', bg='black'))
@theme('ShelfView.ProgressBar:complete', C(fg='green'))
class ProgressBar(QWidget):
    def __init__(self, w, progress):
        # type: (ProgressBar, int, float) -> None
        super().__init__()
        self.w = w
        self.h = 2
        self.progress = progress
        self.c, self.c_complete = self._loadTheme()

    def _loadTheme(self):
        # type: (ProgressBar) -> tuple[C, ...]
        return (Theme.get('ShelfView.ProgressBar'),
                Theme.get('ShelfView.ProgressBar:complete'))

    def pixmap(self):
        # type: (ProgressBar) -> QPixmap
        (w, h) = (self.w, self.h)
        (pc, bc) = (self.c.fg(), self.c.bg())
        if self.progress == 100:
            pc = self.c_complete.fg()

        progress = self.progress / 100
        pixmap = QPixmap(self.w, h)
        pixmap.fill(QColor('transparent'))
        qp = QPainter(pixmap)
        qp.drawPixmap(0, 0,
                      rectPixmap(w, h, bc, bc))
        qp.drawPixmap(0, 0,
                      rectPixmap(int(w * progress), h, pc, pc))
        return pixmap

    def paintEvent(self, e):
        # type: (ProgressBar, QPaintEvent) -> None
        qp = QPainter(self)
        # If no progress, don’t draw anything
        if not self.progress:
            return
        qp.drawPixmap(0, 0, self.pixmap())

    def sizeHint(self):
        # type: (ProgressBar) -> QSize
        return QSize(self.w, self.h)

    def update_(self, progress):
        # type: (ProgressBar, float) -> None
        self.progress = progress


if TYPE_CHECKING:
    from retype.ui import MainWin  # noqa: F401
    from retype.controllers import MainController  # noqa: F401
    from retype.controllers.library import BookWrapper  # noqa: F401
    from qt import (  # noqa: F401
        QKeyEvent, QPaintEvent, QMouseEvent, pyqtBoundSignal, QObject)
