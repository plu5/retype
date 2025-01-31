from enum import Enum
from qt import Qt, QPainter, QPixmap, QRectF, QPen, QColor, QFontDatabase
from typing import TYPE_CHECKING


white = QColor('white')
transparent = QColor('transparent')
center = Qt.AlignmentFlag.AlignCenter
wordwrap = Qt.TextFlag.TextWordWrap
solid = Qt.PenStyle.SolidLine
squarecap = Qt.PenCapStyle.SquareCap


class Font(Enum):
    GENERAL = 1
    FIXED = 2
    BOLD = 3

    @staticmethod
    def systemfonts():
        # type: () -> dict[int, QFont]
        get = QFontDatabase.systemFont
        return {
            1: get(QFontDatabase.GeneralFont),
            2: get(QFontDatabase.FixedFont),
        }

    @classmethod
    def general(cls):
        # type: (type[Font]) -> QFont
        return cls.systemfonts()[1]

    @classmethod
    def fixed(cls):
        # type: (type[Font]) -> QFont
        return cls.systemfonts()[2]

    @classmethod
    def bold(cls):
        # type: (type[Font]) -> QFont
        font = cls.general()
        font.setBold(True)
        return font

    def toQFont(self):
        # type: (Font) -> QFont
        return getattr(
            self, self.name.lower())()  # type: ignore[misc]


def rectPixmap(w, h, fg=white, bg=transparent):
    # type: (int, int, QColor, QColor) -> QPixmap
    pixmap = QPixmap(w + 1, h + 1)
    pixmap.fill(transparent)
    qp = QPainter(pixmap)
    qp.setPen(fg)
    qp.setBrush(bg)
    qp.drawRect(0, 0, w, h)
    return pixmap


def textPixmap(text,  # type: str
               w,  # type: int
               h,  # type: int
               font,  # type: Font | QFont
               fg=white,  # type: QColor
               alignment=center | wordwrap,  # type: int | Qt.Alignment
               bounding_rect=None  # type: QRectF | None
               ):
    # type: (...) -> QPixmap
    pixmap = QPixmap(w, h)
    pixmap.fill(transparent)
    # On some versions of Qt there is a last optional argument to drawText to
    #  give the bounding rect, but my version doesn't, so draw it in an inner
    #  pixmap.
    qp = inner_pixmap = None
    if bounding_rect:
        inner_pixmap = QPixmap(w, h)
        inner_pixmap.fill(transparent)
        qp = QPainter(inner_pixmap)
    else:
        qp = QPainter(pixmap)
        bounding_rect = QRectF(0, 0, w, h)
    font = font.toQFont() if isinstance(font, Font) else font
    qp.setFont(font)
    qp.setPen(fg)
    qp.drawText(bounding_rect, int(alignment), text)
    if inner_pixmap:
        qp = QPainter(pixmap)
        qp.drawPixmap(0, 0, inner_pixmap)
    return pixmap


def linePixmap(x2, y2, colour=white, thickness=2, style=solid):
    # type: (int, int, QColor, int, Qt.PenStyle) -> QPixmap
    """Line from origin (0, 0) to (x2, y2)"""
    rect = QRectF()
    x1 = y1 = 0
    rect.adjust(x1, y1, x2, y2)
    (w, h) = (int(rect.width()), int(rect.height()))
    if not h:
        h = thickness
    elif not w:
        w = thickness
    pixmap = QPixmap(w, h)
    pixmap.fill(transparent)
    qp = QPainter(pixmap)
    qp.setPen(QPen(colour, thickness, style=style))
    qp.drawLine(x1, y1, x2, y2)
    return pixmap


def ellipsePixmap(w, h, fg=white, bg=transparent, thickness=2,
                  style=solid):
    # type: (int, int, QColor, QColor, int, Qt.PenStyle) -> QPixmap
    bounding_rect = QRectF(thickness/2, thickness/2, w-thickness, h-thickness)
    pixmap = QPixmap(w, h)
    pixmap.fill(transparent)
    qp = QPainter(pixmap)
    qp.setRenderHint(QPainter.RenderHint.Antialiasing)
    qp.setPen(QPen(fg, thickness, style))
    qp.setBrush(bg)
    qp.drawEllipse(bounding_rect)
    return pixmap


def arcPixmap(w,  # type: int
              h,  # type: int
              fg=white,  # type: QColor
              thickness=2,  # type: int
              style=solid,  # type: Qt.PenStyle
              start_angle=0,  # type: int
              span_angle=16*180,  # type: int
              antialiasing=True,  # type: bool
              cap=squarecap  # type: Qt.PenCapStyle
              ):
    # type: (...) -> QPixmap
    bounding_rect = QRectF(thickness/2, thickness/2, w-thickness, h-thickness)
    pixmap = QPixmap(w, h)
    pixmap.fill(transparent)
    qp = QPainter(pixmap)
    if antialiasing:
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
    qp.setPen(QPen(fg, thickness, style, cap))
    qp.drawArc(bounding_rect, start_angle, span_angle)
    return pixmap


if TYPE_CHECKING:
    from qt import QFont  # noqa: F401
