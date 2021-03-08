import logging
from PyQt5.Qt import (QWidget, QPixmap, QPainter, QFont, QColor, Qt,
                      QRectF, QSize, QPoint, QPolygon)

logger = logging.getLogger(__name__)

colours = [QColor('#264653'), QColor('#2A9D8F'), QColor('#E76F51'),
           QColor('#6B705C'), QColor('#FCA311'), QColor('#3D405B'),
           QColor('#212529'), QColor('#540B0E'), QColor('#3E1F47'),
           QColor('#6C584C')]


def rectanglePixmap(w, h, fg=Qt.white, bg=Qt.transparent):
    pixmap = QPixmap(w + 1, h + 1)
    pixmap.fill(Qt.transparent)
    qp = QPainter(pixmap)
    qp.setPen(fg)
    qp.setBrush(bg)
    qp.drawRect(0, 0, w, h)
    return pixmap


def textPixmap(text, w, h, font, fg=Qt.white,
               alignment=Qt.AlignCenter | Qt.TextWordWrap):
    pixmap = QPixmap(w, h)
    pixmap.fill(Qt.transparent)
    qp = QPainter(pixmap)
    qp.setFont(font)
    qp.setPen(fg)
    qp.drawText(QRectF(0, 0, w, h), alignment, text)
    return pixmap


class PregeneratedCover:
    def __init__(self, w, h, title, author):
        self.w = w
        self.h = h
        self.title = title
        self.author = author

    def pixmap(self):
        (w, h) = (self.w, self.h)
        pixmap = QPixmap(w, h)

        char = self.title[-1]
        ind = ord(char) - 96
        i = ind % len(colours)
        pixmap.fill(colours[i])

        qp = QPainter(pixmap)

        inner_xy = (10, 10)
        inner_size = (w - 20, h - 20)
        qp.drawPixmap(*inner_xy, rectanglePixmap(*inner_size))
        font = QFont('Times', 9, 99)
        qp.drawPixmap(inner_xy[0], 0,
                      textPixmap(self.title, *inner_size, font))
        font = QFont('Times', 8)
        qp.drawPixmap(inner_xy[0], 80,
                      textPixmap(self.author, *inner_size, font))

        return pixmap


class HoverCover:
    def __init__(self, w, h, title, author):
        self.w = w
        self.h = h
        self.title = title
        self.author = author
        self.highlight_colour = QColor(80, 80, 80, 128)

    def pixmap(self):
        (w, h) = (self.w, self.h)
        pixmap = QPixmap(w, h)
        pixmap.fill(self.highlight_colour)
        qp = QPainter(pixmap)

        inner_xy = (10, 10)
        inner_size = (w - 20, h - 20)
        font = QFont('Times', 9, 99)
        qp.drawPixmap(inner_xy[0], 0,
                      textPixmap(self.title, *inner_size, font))

        qp.setPen(Qt.white)
        qp.setBrush(Qt.red)
        points = [QPoint(0, 0), QPoint(13, 0), QPoint(0, 0 + 13)]
        qp.drawPolygon(QPolygon(points))

        return pixmap


class Cover(QWidget):
    def __init__(self, book, parent=None):
        super().__init__(parent)
        self.idn = book.idn
        self.book = book
        self.title = book.title
        self.author = book.author
        self.hovered = False
        self.pregenerated = True
        self.default_size = (125, 200)
        self.max_height = 200
        self.max_width = 150

        self.image = QPixmap(*self.default_size)
        # Try to load cover image
        if self.book.cover:
            self.raw_cover = self.book.cover.content
            self.image.loadFromData(self.raw_cover)
            self.pregenerated = False

            # Scaling
            (w, h) = (self.image.width(), self.image.height())
            if h > w:
                self.image = self.image.scaledToHeight(self.max_height, 1)
            elif w >= h:
                self.image = self.image.scaledToWidth(self.max_width, 1)

        self.height = self.image.size().height()
        self.width = self.image.size().width()
        self.setMaximumSize(self.width, self.height + 10)

        info = (self.width, self.height, self.title, self.author)
        if self.pregenerated:
            self.image = PregeneratedCover(*info).pixmap()
        self.hover_image = HoverCover(*info).pixmap()

    def sizeHint(self):
        size = QSize(self.width, self.height + 10)
        return size

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)

        s = 10
        qp.drawPixmap(0, s, self.image)

        if self.hovered:
            self.setCursor(Qt.PointingHandCursor)
            qp.drawPixmap(0, s, self.hover_image)

        # Draw id
        (w, h) = (self.width, self.height)
        qp.setPen(Qt.gray)
        font = QFont('Times', 9, 99)
        qp.drawPixmap(0, -3,
                      textPixmap(str(self.idn), w, h, font, Qt.gray,
                                 Qt.AlignHCenter))

        qp.end()

    def enterEvent(self, e):
        self.hovered = True
        self.repaint()

    def leaveEvent(self, e):
        self.hovered = False
        self.repaint()
