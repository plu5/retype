from enum import Enum
from qt import Qt, QPainter, QPixmap, QRectF, QPen, QColor, QFontDatabase


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
        get = QFontDatabase.systemFont
        return {
            1: get(QFontDatabase.GeneralFont),
            2: get(QFontDatabase.FixedFont),
        }

    @classmethod
    def general(cls):
        return cls.systemfonts()[1]

    @classmethod
    def fixed(cls):
        return cls.systemfonts()[2]

    @classmethod
    def bold(cls):
        font = cls.general()
        font.setBold(True)
        return font

    def toQFont(self):
        return getattr(self, self.name.lower())()


def rectPixmap(w, h, fg=white, bg=transparent):
    pixmap = QPixmap(w + 1, h + 1)
    pixmap.fill(transparent)
    qp = QPainter(pixmap)
    qp.setPen(fg)
    qp.setBrush(bg)
    qp.drawRect(0, 0, w, h)
    return pixmap


def textPixmap(text, w, h, font, fg=white,
               alignment=center | wordwrap):
    pixmap = QPixmap(w, h)
    pixmap.fill(transparent)
    qp = QPainter(pixmap)
    font = font.toQFont() if type(font) == Font else font
    qp.setFont(font)
    qp.setPen(fg)
    qp.drawText(QRectF(0, 0, w, h), alignment, text)
    return pixmap


def linePixmap(x2, y2, colour=white, thickness=2, style=solid):
    """Line from origin (0, 0) to (x2, y2)"""
    rect = QRectF()
    x1 = y1 = 0
    rect.adjust(x1, y1, x2, y2)
    (w, h) = (rect.width(), rect.height())
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
    bounding_rect = QRectF(thickness/2, thickness/2, w-thickness, h-thickness)
    pixmap = QPixmap(w, h)
    pixmap.fill(transparent)
    qp = QPainter(pixmap)
    qp.setRenderHint(QPainter.RenderHint.Antialiasing)
    qp.setPen(QPen(fg, thickness, style))
    qp.setBrush(bg)
    qp.drawEllipse(bounding_rect)
    return pixmap


def arcPixmap(w, h, fg=white, thickness=2, style=solid,
              start_angle=0, span_angle=16*180, antialiasing=True,
              cap=squarecap):
    bounding_rect = QRectF(thickness/2, thickness/2, w-thickness, h-thickness)
    pixmap = QPixmap(w, h)
    pixmap.fill(transparent)
    qp = QPainter(pixmap)
    if antialiasing:
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
    qp.setPen(QPen(fg, thickness, style, cap))
    qp.drawArc(bounding_rect, start_angle, span_angle)
    return pixmap
