import logging
from PyQt5.Qt import (QWidget, QPixmap, QPainter, QFont, QColor, Qt,
                      QSize, QPoint, QPolygon)

from retype.ui.painting import rectPixmap, textPixmap, ellipsePixmap, arcPixmap

logger = logging.getLogger(__name__)

colours = [QColor('#264653'), QColor('#2A9D8F'), QColor('#E76F51'),
           QColor('#6B705C'), QColor('#FCA311'), QColor('#3D405B'),
           QColor('#212529'), QColor('#540B0E'), QColor('#3E1F47'),
           QColor('#6C584C')]


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
        qp.drawPixmap(*inner_xy, rectPixmap(*inner_size))
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


class CompleteIndicator:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.fg = Qt.green
        self.circle_diameter = 44
        self.bottom_margin = 10
        self.thickness = 3

    def pixmap(self):
        (w, h, fg, r, t) = (self.w, self.h, self.fg, self.circle_diameter,
                            self.thickness)
        (circle_x, circle_y) = (w/2 - r/2, h - r - self.bottom_margin)
        (smile_r, eye_r) = (r/2, 5)
        (smile_x, smile_y) = (circle_x + smile_r/2,
                              circle_y + smile_r/2 + 1)
        circle_middle_x = circle_x + r/2
        eye_spacing = r/5.5
        (eye_l_x, eye_r_x, eye_y) = (circle_middle_x - eye_r - eye_spacing/2,
                                     circle_middle_x + eye_spacing/2,
                                     circle_y + r/3)

        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.transparent)
        qp = QPainter(pixmap)
        draw = qp.drawPixmap

        draw(circle_x, circle_y, ellipsePixmap(r, r, fg, thickness=t))
        draw(smile_x, smile_y, arcPixmap(
            smile_r, smile_r, fg, start_angle=-20*16, span_angle=-140*16,
            thickness=t, cap=Qt.RoundCap))
        eye = ellipsePixmap(eye_r, eye_r, fg, bg=fg)
        draw(eye_l_x, eye_y, eye)
        draw(eye_r_x, eye_y, eye)

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
        self.setMaximumSize(self.width, self.height)

        info = (self.width, self.height, self.title, self.author)
        if self.pregenerated:
            self.image = PregeneratedCover(*info).pixmap()
        self.hover_image = HoverCover(*info).pixmap()
        self.complete_indicator = CompleteIndicator(*info[0:2]).pixmap()

    def sizeHint(self):
        size = QSize(self.width, self.height)
        return size

    def paintEvent(self, e):
        qp = QPainter(self)

        qp.drawPixmap(0, 0, self.image)

        if self.hovered:
            self.setCursor(Qt.PointingHandCursor)
            qp.drawPixmap(0, 0, self.hover_image)
            if self.book.progress == 100:
                qp.drawPixmap(0, 0, self.complete_indicator)

    def enterEvent(self, e):
        self.hovered = True
        self.repaint()

    def leaveEvent(self, e):
        self.hovered = False
        self.repaint()
