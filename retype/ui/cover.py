import logging
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap, QPainter, QPen, QFont, QColor
from PyQt5.QtCore import Qt, QRectF, QSize

logger = logging.getLogger(__name__)


class Cover(QWidget):
    def __init__(self, book, parent=None):
        super().__init__(parent)
        self.idn = book.idn  # id
        self.book = book
        self.title = book.title
        self.hovered = False
        self.highlight_colour = QColor(80, 80, 80, 128)

        # todo: a more clever way to get an image that is likely to be the cover
        # only use it as cover if it is large enough to avoid using ornaments
        # otherwise use our pregenerated cover
        self.image = QPixmap(120, 200)
        # try to load cover image
        try:
            self.raw_cover = self.book.testimage[0].content
            self.image.loadFromData(self.raw_cover)
        except IndexError:
            logger.debug("No cover image found")
            self.image.fill(Qt.black)

        # scaling
        if self.image.height() > self.image.width():
            self.image = self.image.scaledToHeight(200, 1)
        elif self.image.width() >= self.image.height():
            self.image = self.image.scaledToWidth(150, 1)

        self.height = self.image.size().height()
        self.width = self.image.size().width()
        self.setMaximumSize(self.width, self.height)

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        qp.drawPixmap(0, 0, self.image)
        if self.hovered:
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
        self.hovered = True
        self.repaint()

    def leaveEvent(self, e):
        self.hovered = False
        self.repaint()

    def sizeHint(self):
        return QSize(self.width, self.height)
