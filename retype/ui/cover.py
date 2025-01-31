import logging
from qt import QWidget, QPixmap, QPainter, QColor, Qt, QSize, QPoint, QPolygon
from typing import TYPE_CHECKING

from retype.ui.painting import (rectPixmap, textPixmap, ellipsePixmap,
                                arcPixmap, Font)

logger = logging.getLogger(__name__)

colours = [QColor('#264653'), QColor('#2A9D8F'), QColor('#E76F51'),
           QColor('#6B705C'), QColor('#FCA311'), QColor('#3D405B'),
           QColor('#212529'), QColor('#540B0E'), QColor('#3E1F47'),
           QColor('#6C584C')]


class PregeneratedCover:
    def __init__(self, w, h, title, author):
        # type: (PregeneratedCover, int, int, str, str) -> None
        self.w = w
        self.h = h
        self.title = title
        self.author = author

    def pixmap(self):
        # type: (PregeneratedCover) -> QPixmap
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
        font = Font.BOLD
        qp.drawPixmap(inner_xy[0], 0,
                      textPixmap(self.title, *inner_size, font))
        font = Font.GENERAL
        qp.drawPixmap(inner_xy[0], 80,
                      textPixmap(self.author, *inner_size, font))

        return pixmap


class HoverCover:
    def __init__(self, w, h, title, author):
        # type: (HoverCover, int, int, str, str) -> None
        self.w = w
        self.h = h
        self.title = title
        self.author = author
        self.highlight_colour = QColor(80, 80, 80, 128)

    def pixmap(self):
        # type: (HoverCover) -> QPixmap
        (w, h) = (self.w, self.h)
        pixmap = QPixmap(w, h)
        pixmap.fill(self.highlight_colour)
        qp = QPainter(pixmap)

        inner_xy = (10, 10)
        inner_size = (w - 20, h - 20)
        font = Font.BOLD
        qp.drawPixmap(inner_xy[0], 0,
                      textPixmap(self.title, *inner_size, font))

        qp.setPen(QColor('white'))
        qp.setBrush(QColor('red'))
        points = [QPoint(0, 0), QPoint(13, 0), QPoint(0, 0 + 13)]
        qp.drawPolygon(QPolygon(points))

        return pixmap


class CompleteIndicator:
    def __init__(self, w, h):
        # type: (CompleteIndicator, int, int) -> None
        self.w = w
        self.h = h
        self.fg = QColor('green')
        self.circle_diameter = 44
        self.bottom_margin = 10
        self.thickness = 3

    def pixmap(self):
        # type: (CompleteIndicator) -> QPixmap
        (w, h, fg, r, t) = (self.w, self.h, self.fg, self.circle_diameter,
                            self.thickness)
        (circle_x, circle_y) = (int(w/2 - r/2), h - r - self.bottom_margin)
        (smile_r, eye_r) = (int(r/2), 5)
        (smile_x, smile_y) = (circle_x + int(smile_r/2),
                              circle_y + int(smile_r/2) + 1)
        circle_middle_x = circle_x + int(r/2)
        half_eyespacing = int((r/5.5)/2)
        (eye_l_x, eye_r_x, eye_y) = (circle_middle_x - eye_r - half_eyespacing,
                                     circle_middle_x + half_eyespacing,
                                     circle_y + int(r/3))

        pixmap = QPixmap(int(w), int(h))
        pixmap.fill(QColor('transparent'))
        qp = QPainter(pixmap)

        def draw(x, y, pixmap):
            # type: (int, int, QPixmap) -> None
            qp.drawPixmap(x, y, pixmap)

        draw(circle_x, circle_y, ellipsePixmap(r, r, fg, thickness=t))
        draw(smile_x, smile_y, arcPixmap(
            smile_r, smile_r, fg, start_angle=-20*16, span_angle=-140*16,
            thickness=t, cap=Qt.PenCapStyle.RoundCap))
        eye = ellipsePixmap(eye_r, eye_r, fg, bg=fg)
        draw(eye_l_x, eye_y, eye)
        draw(eye_r_x, eye_y, eye)

        return pixmap


class Cover(QWidget):
    def __init__(self, book, parent=None):
        # type: (Cover, BookWrapper, QWidget|None) -> None
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

        self.pixmap = QPixmap(*self.default_size)
        # Try to load cover image
        if self.book.cover:
            self.raw_cover = self.book.cover.content
            self.pixmap.loadFromData(self.raw_cover)
            self.pregenerated = False

            # Scaling
            (w, h) = (self.pixmap.width(), self.pixmap.height())
            mode = Qt.TransformationMode.SmoothTransformation
            if h > w:
                self.pixmap = self.pixmap.scaledToHeight(self.max_height, mode)
            elif w >= h:
                self.pixmap = self.pixmap.scaledToWidth(self.max_width, mode)

        self.h = self.pixmap.size().height()
        self.w = self.pixmap.size().width()
        self.setMaximumSize(self.w, self.h)

        info = (self.w, self.h, self.title, self.author)
        if self.pregenerated:
            self.pixmap = PregeneratedCover(*info).pixmap()
        self.hover_image = HoverCover(*info).pixmap()
        self.complete_indicator = CompleteIndicator(*info[0:2]).pixmap()

    def sizeHint(self):
        # type: (Cover) -> QSize
        return QSize(self.w, self.h)

    def paintEvent(self, e):
        # type: (Cover, QPaintEvent) -> None
        qp = QPainter(self)

        qp.drawPixmap(0, 0, self.pixmap)

        if self.hovered:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            qp.drawPixmap(0, 0, self.hover_image)
            if self.book.progress == 100:
                qp.drawPixmap(0, 0, self.complete_indicator)

    def enterEvent(self, e):
        # type: (Cover, QEvent) -> None
        self.hovered = True
        self.repaint()

    def leaveEvent(self, e):
        # type: (Cover, QEvent) -> None
        self.hovered = False
        self.repaint()


if TYPE_CHECKING:
    from qt import QEvent, QPaintEvent  # noqa: F401
    from retype.controllers.library import BookWrapper  # noqa: F401
