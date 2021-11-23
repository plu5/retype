import logging
from PyQt5.Qt import (QWidget, QVBoxLayout, QPainter, Qt, QColor, QEvent,
                      QPixmap, QFont, QSize)

from retype.layouts import ShelvesWidget
from retype.ui import Cover
from retype.ui.painting import rectPixmap, linePixmap, textPixmap

logger = logging.getLogger(__name__)


class ShelfView(QWidget):
    def __init__(self, main_win, main_controller, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._controller = main_controller
        self._library = self._controller.library
        self._initUI()

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
        if watched == self.shelves.container and event.type() == QEvent.Paint:
            o = (0, 0)
            (w, h) = (watched.size().width(), watched.size().height())
            top_shelf_y = self.shelf_height + 5
            deepness = 10
            inset = 4
            front_h = 10
            shadow_colour = Qt.darkGray
            line_colour = QColor('#555')
            light_colour = QColor('#B5B5B5')
            highlight_colour = QColor('#CACACA')

            qp = QPainter(watched)
            draw = qp.drawPixmap

            draw(*o, rectPixmap(10, h, shadow_colour, shadow_colour))
            draw(w - 11, 0, rectPixmap(10, h, shadow_colour, shadow_colour))
            draw(10, 0, rectPixmap(2, h, line_colour))
            draw(w - 13, 0, rectPixmap(2, h, line_colour))

            def shelf():
                pixmap = QPixmap(w, h)
                pixmap.fill(Qt.transparent)
                qp = QPainter(pixmap)
                draw = qp.drawPixmap
                # Top
                draw(0, 3, rectPixmap(w, deepness, shadow_colour,
                                      shadow_colour))
                # Front
                draw(inset, deepness + 3, rectPixmap(w - 10, 10, light_colour,
                                                     light_colour))
                # Front outline
                draw(12, 0, rectPixmap(w - 25, 2, line_colour, Qt.white))
                draw(inset, deepness + 3,
                     linePixmap(w - 7, 0, highlight_colour, 4))
                draw(inset, deepness + 3 + front_h,
                     linePixmap(w - 7, 0, line_colour, 4))
                sideline = linePixmap(0, 11, line_colour, 4)
                draw(3, deepness + 3, sideline)
                draw(w - 5, deepness + 3, sideline)
                return pixmap

            shelf_pixmap = shelf()

            shelf_y = top_shelf_y - 3
            while shelf_y < h:
                draw(0, shelf_y, shelf_pixmap)
                shelf_y += self.shelf_height

            # The rectangles at the very top
            c = QColor('#A1A0A0')
            draw(*o, rectPixmap(w, 20, c, c))
            draw(0, 20, rectPixmap(w, 3, line_colour, line_colour))

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


class IDNDisplay(QWidget):
    def __init__(self, idn, w):
        super().__init__()
        self.idn = idn
        self.w = w

    def pixmap(self, idn):
        (w, h) = (self.w, 10)
        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.transparent)
        qp = QPainter(pixmap)
        font = QFont('Times', 8)
        qp.drawPixmap(0, -3,
                      textPixmap(str(idn), w, 20, font, Qt.gray,
                                 Qt.AlignHCenter))
        return pixmap

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.drawPixmap(0, 0, self.pixmap(self.idn))

    def sizeHint(self):
        return QSize(self.w, 10)


class ProgressBar(QWidget):
    def __init__(self, w, progress):
        super().__init__()
        self.w = w
        self.h = 2
        self.progress = progress
        self.progress_colour = Qt.yellow
        self.complete_colour = Qt.green
        self.background_colour = Qt.black

    def pixmap(self):
        (w, h) = (self.w, self.h)
        (pc, bc) = (self.progress_colour, self.background_colour)
        if self.progress == 100:
            pc = self.complete_colour

        progress = self.progress / 100
        pixmap = QPixmap(self.w, h)
        pixmap.fill(Qt.transparent)
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
