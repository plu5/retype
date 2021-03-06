from PyQt5.Qt import (QWidget, QPainter, QColor, Qt, QPixmap, QPoint, QPolygon,
                      QLabel, pyqtSignal)

from retype.layouts import RowLayout


class Separator(QWidget):
    def __init__(self, colour, padding=0):
        super().__init__()
        self.colour = colour
        self.start = padding
        width = 8 + padding * 2
        self._pixmap = QPixmap(width, 17)
        self._pixmap.fill(Qt.transparent)
        self.setMinimumSize(width, 17)

    def pixmap(self):
        qp = QPainter(self._pixmap)
        qp.setPen(self.colour)
        qp.setBrush(self.colour)

        s = self.start
        points = [QPoint(s, 1), QPoint(s, 2),
                  QPoint(s + 7, 9), QPoint(s, 17)]
        qp.drawPolygon(QPolygon(points))

        return self._pixmap

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        qp.drawPixmap(0, 0, self.pixmap())
        qp.end()


class Spacer(QWidget):
    """Either a fixed-width spacer with width `width', or a spacer that will
 fill the width of the parent minus `width'. For the latter pass parent with a
 repainted signal for when it should be updated (for example, emit it on
 paintEvent)."""
    def __init__(self, parent=None, width=30):
        super().__init__()
        self.p = parent
        self.width = width
        if self.p and hasattr(self.p, 'repainted'):
            self.p.repainted.connect(self.update)
        else:
            self.setFixedWidth(self.width)

    def update(self):
        if not self.p:
            return
        pwidth = self.p.size().width()
        pheight = self.p.size().height()
        x = self.pos().x()

        width = pwidth - x - self.width
        height = pheight

        if width > 0:
            self.setFixedWidth(width)
        if height > 0:
            self.setFixedHeight(height)


class Modeline(QWidget):
    repainted = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(1, 17)

        self.cursorPos = QLabel(str(0))
        self.title = QLabel("")
        self.title.setStyleSheet("font-weight: bold")
        self.linePos = QLabel(str(0))
        self.chapPos = QLabel(str(0))
        self.chapTotal = QLabel(str(0))
        self.percentage = QLabel(str(0))
        self.padding = 5
        self.posSeparator = QLabel(":")
        self.chapPretext = QLabel("chapter ")
        self.chapSeparator = QLabel("/")
        self.colour1 = QColor(255, 215, 0)
        self.colour2 = QColor(205, 173, 0)
        self.colour3 = QColor(139, 117, 0)
        self.colour4 = QColor(198, 171, 120)

        self.layout_ = RowLayout(self)
        self.layout_.setContentsMargins(0, self.padding, 0, 0)
        self.layout_.setSpacing(0)

        self.separators = [Separator(self.colour1, self.padding),
                           Separator(self.colour2, self.padding),
                           Separator(self.colour3, self.padding),
                           Separator(self.colour2, self.padding)]
        self.elements = [
            self.linePos, self.posSeparator, self.cursorPos,
            self.separators[0],
            self.title,
            self.separators[1],
            self.chapPretext, self.chapPos, self.chapSeparator, self.chapTotal,
            Spacer(self, 45), self.separators[2], self.separators[3]
        ]
        for element in self.elements:
            self.layout_.addWidget(element)

    def setCursorPos(self, value):
        self.cursorPos.setText(str(value))

    def setTitle(self, title):
        self.title.setText(title)

    def setLinePos(self, value):
        self.linePos.setText(str(value))

    def setChapPos(self, value):
        self.chapPos.setText(str(value))

    def setChapTotal(self, value):
        self.chapTotal.setText(str(value))

    def paintEvent(self, e):
        width = self.size().width()
        height = self.size().height()

        qp = QPainter()
        qp.begin(self)

        # Main rect
        qp.setPen(self.colour1)
        qp.setBrush(self.colour1)
        qp.drawRect(0, 0, width, height)
        # Top line
        qp.setBrush(self.colour2)
        qp.setPen(self.colour2)
        qp.drawLine(0, 0, width, 0)

        for separator in reversed(self.separators):
            qp.setPen(separator.colour)
            qp.setBrush(separator.colour)
            qp.drawRect(0, 1, separator.pos().x() + self.padding, 17)

        qp.end()
        self.repainted.emit()
