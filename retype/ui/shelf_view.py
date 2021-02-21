import logging
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton,
                             QGridLayout)
from PyQt5.QtCore import (pyqtSignal, Qt, QRectF, QSize)
from PyQt5.QtGui import (QPixmap, QPainter, QFont, QColor, QPen)
#from controllers import library

from retype.layouts import ShelvesWidget

logger = logging.getLogger(__name__)


class ShelfView(QWidget):
    def __init__(self, main_win, main_controller, parent=None):
        super().__init__(parent)
        self._controller = main_controller
        self._library = self._controller._library
        self._initUI()
        self.items = []
        self._generateItems()
        self._populate()

    def _initUI(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.shelves = ShelvesWidget(self, 130, 225)
        self.shelves.setContentsMargins(0, 5, 5, 0);
        self.layout.addWidget(self.shelves)

    #def _instantiateItems(self):
        # for book in _controller._book_list...

    def _populate(self):
        for item in self.items:
            self.shelves.addWidget(item)
        # debug thing below
        for i in range(10):
            book_wrapper = self._library._instantiateBook(0)
            item = ShelfItem(book_wrapper)
            self.shelves.addWidget(item)

    def _generateItems(self):
        for book in self._library._book_list:
            book_wrapper = self._library._instantiateBook(book)
            item = ShelfItem(book_wrapper)
            self.items.append(item)


class ShelfItem(QWidget):
    """"""
    def __init__(self, book_wrapper, parent=None):
        super().__init__(parent)
        self._book_wrapper = book_wrapper
        self.title = self._book_wrapper.title
        self._initCover()
        self.active = False
        self.highlight_colour = QColor(80, 80, 80, 128)

    def _initCover(self):
        # todo: a more clever way to get an image that is likely to be the cover
        # only use it as cover if it is large enough to avoid using ornaments
        # otherwise use our pregenerated cover
        self.cover = QPixmap(120, 200)
        # try to load cover image
        try:
            self.raw_cover = self._book_wrapper.testimage[0].content
            self.cover.loadFromData(self.raw_cover)
        except IndexError:
            logger.debug("No cover image found")
            self.cover.fill(Qt.black)

        # scaling
        if self.cover.height() > self.cover.width():
            self.cover = self.cover.scaledToHeight(200, 1)
        elif self.cover.width() >= self.cover.height():
            self.cover = self.cover.scaledToWidth(150, 1)

        self.height = self.cover.size().height()
        self.width = self.cover.size().width()
        self.setMaximumSize(self.width, self.height)

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        qp.drawPixmap(0, 0, self.cover)
        if self.active:
            self.setCursor(Qt.PointingHandCursor)
            qp.fillRect(0, 0, self.width, self.height, self.highlight_colour)
            qp.setPen(QPen(Qt.white, 1, Qt.SolidLine))
            font = QFont('Times', 9, 99)
            qp.setFont(font)
            title_rect = QRectF(0, 0, self.width, self.height)
            qp.drawText(title_rect, Qt.AlignCenter | Qt.TextWordWrap,
                        self.title)
        qp.end()

    def enterEvent(self, e):
        self.active = True
        self.repaint()

    def leaveEvent(self, e):
        self.active = False
        self.repaint()

    def sizeHint(self):
        return QSize(self.width, self.height)
