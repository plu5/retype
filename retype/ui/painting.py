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


def linePixmap(x2, y2, colour=Qt.white, thickness=2, style=Qt.SolidLine):
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
    pixmap.fill(Qt.transparent)
    qp = QPainter(pixmap)
    qp.setPen(QPen(colour, thickness, style=style))
    qp.drawLine(x1, y1, x2, y2)
    return pixmap


def ellipsePixmap(w, h, fg=Qt.white, bg=Qt.transparent, thickness=2,
                  style=Qt.SolidLine):
    bounding_rect = QRectF(thickness/2, thickness/2, w-thickness, h-thickness)
    pixmap = QPixmap(w, h)
    pixmap.fill(Qt.transparent)
    qp = QPainter(pixmap)
    qp.setRenderHint(QPainter.Antialiasing)
    qp.setPen(QPen(fg, thickness, style))
    qp.setBrush(bg)
    qp.drawEllipse(bounding_rect)
    return pixmap


def arcPixmap(w, h, fg=Qt.white, thickness=2, style=Qt.SolidLine,
              start_angle=0, span_angle=16*180, antialiasing=True,
              cap=Qt.SquareCap):
    bounding_rect = QRectF(thickness/2, thickness/2, w-thickness, h-thickness)
    pixmap = QPixmap(w, h)
    pixmap.fill(Qt.transparent)
    qp = QPainter(pixmap)
    if antialiasing:
        qp.setRenderHint(QPainter.Antialiasing)
    qp.setPen(QPen(fg, thickness, style, cap))
    qp.drawArc(bounding_rect, start_angle, span_angle)
    return pixmap
