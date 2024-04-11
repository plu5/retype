import logging
from qt import (QWidget, QVBoxLayout, QPainter, Qt, QColor, QEvent, QPixmap,
                QSize)

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
        super().__init__(parent)
        self.parent = parent
        self._controller = main_controller
        self._library = self._controller.library
        self.c_background, self.c_shelf, self.c_top = self._loadTheme()
        self.c_background.changed.connect(self.themeUpdate)
        self._initUI()

    def _loadTheme(self):
        return (Theme.get('ShelfView.Background'),
                Theme.get('ShelfView.Shelf'),
                Theme.get('ShelfView.Top'))

    def themeUpdate(self):
        self.update()

    def _initUI(self):
        self.cell_dimensions = (150, 200, 232)  # min width, max width, height
        self.shelf_height = self.cell_dimensions[2]

        self.shelves = ShelvesWidget(self, *self.cell_dimensions)
        self.shelves.setContentsMargins(10, 15, 15, 10)
        self.shelves.container.installEventFilter(self)

        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.addWidget(self.shelves)

    def _populate(self):
        for book in self._library.books.values():
            loadBook = self._controller.loadBookRequested
            item = ShelfItem(book, loadBook)
            self.shelves.addWidget(item)

    def repopulate(self):
        self.shelves.clearWidgets()
        self._populate()

    def keyPressEvent(self, e):
        self._controller.console.transferFocus(e)
        QWidget.keyPressEvent(self, e)

    def eventFilter(self, watched, event):
        if watched == self.shelves.container and\
           event.type() == QEvent.Type.Paint:
            o = (0, 0)
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
        super().__init__(parent)
        self.book = book
        self.idn = book.idn
        self.cover = Cover(book, self)
        self.loadBook = loadBook
        self.progress = self.book.progress
        self._initUI()

    def _initUI(self):
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(0)
        self.setLayout(self.layout_)
        self.layout_.addWidget(IDNDisplay(self.idn, self.cover.width))
        self.layout_.addWidget(self.cover)
        self.progress_bar = ProgressBar(self.cover.width, self.progress)
        self.book.progress_subscribers.append(self.progress_bar.update_)
        self.layout_.addWidget(self.progress_bar)

    def mouseReleaseEvent(self, e):
        self.loadBook.emit(self.book.idn)


@theme('ShelfView.IDNDisplay', C(fg='gray'))
class IDNDisplay(QWidget):
    def __init__(self, idn, w):
        super().__init__()
        self.idn = idn
        self.w = w
        self.c = self._loadTheme()

    def _loadTheme(self):
        return Theme.get('ShelfView.IDNDisplay')

    def pixmap(self, idn):
        (w, h) = (self.w, 10)
        pixmap = QPixmap(w, h)
        pixmap.fill(QColor('transparent'))
        qp = QPainter(pixmap)
        font = Font.GENERAL
        qp.drawPixmap(0, -3,
                      textPixmap(str(idn), w, 20, font, self.c.fg(),
                                 Qt.AlignmentFlag.AlignHCenter))
        return pixmap

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.drawPixmap(0, 0, self.pixmap(self.idn))

    def sizeHint(self):
        return QSize(self.w, 10)


@theme('ShelfView.ProgressBar', C(fg='yellow', bg='black'))
@theme('ShelfView.ProgressBar:complete', C(fg='green'))
class ProgressBar(QWidget):
    def __init__(self, w, progress):
        super().__init__()
        self.w = w
        self.h = 2
        self.progress = progress
        self.c, self.c_complete = self._loadTheme()

    def _loadTheme(self):
        return (Theme.get('ShelfView.ProgressBar'),
                Theme.get('ShelfView.ProgressBar:complete'))

    def pixmap(self):
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
                      rectPixmap(w * progress, h, pc, pc))
        return pixmap

    def paintEvent(self, e):
        qp = QPainter(self)
        # If no progress, don’t draw anything
        if not self.progress:
            return
        qp.drawPixmap(0, 0, self.pixmap())

    def sizeHint(self):
        return QSize(self.w, self.h)

    def update_(self, progress):
        self.progress = progress
