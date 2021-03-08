from PyQt5.Qt import Qt, QPainter, QPixmap, QRectF, QPen


def rectPixmap(w, h, fg=Qt.white, bg=Qt.transparent):
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


def linePixmap(x1, y1, x2, y2, colour=Qt.white, thickness=2):
    rect = QRectF()
    rect.adjust(x1, y1, x2, y2)
    (w, h) = (rect.width(), rect.height())
    if not h:
        h = thickness
    elif not w:
        w = thickness
    pixmap = QPixmap(w, h)
    pixmap.fill(Qt.transparent)
    qp = QPainter(pixmap)
    qp.setPen(QPen(colour, thickness))
    qp.drawLine(x1, y1, x2, y2)
    return pixmap
