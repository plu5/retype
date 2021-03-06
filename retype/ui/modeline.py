from PyQt5.Qt import (QWidget, QPainter, QColor, Qt, QPixmap, QPoint, QPolygon,
                      QLabel, pyqtSignal, QFrame)

from retype.layouts import RowLayout


class Separator(QWidget):
    def __init__(self, colour, padding=0, facing_right=True):
        super().__init__()
        self.colour = colour
        self.start = padding
        width = 8 + padding * 2
        self._pixmap = QPixmap(width, 16)
        self._pixmap.fill(Qt.transparent)
        self.setMinimumSize(width, 16)
        self.facing_right = facing_right

    def pixmap(self):
        qp = QPainter(self._pixmap)
        qp.setPen(self.colour)
        qp.setBrush(self.colour)

        s = self.start
        if self.facing_right:
            points = [QPoint(s, 0), QPoint(s, 2),
                      QPoint(s + 7, 9), QPoint(s, 16)]
        else:
            points = [QPoint(s, 0), QPoint(s + 7, 0), QPoint(s + 7, 2),
                      QPoint(s, 9), QPoint(s + 7, 16), QPoint(s, 16)]
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
    def __init__(self, width=30, parent=None):
        super().__init__(parent)
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


class WidgetsGroup(QFrame):
    def __init__(self, *widgets, css_=None, tooltip=None, cursor=None,
                 height=16):
        super().__init__()
        self.layout_ = RowLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(0)

        self.setMinimumHeight(height)
        if css_:
            self.setProperty("css_", css_)
        if tooltip:
            self.setToolTip(tooltip)
        if cursor:
            self.setCursor(cursor)

        for widget in widgets:
            self.addWidget(widget)

    def addWidget(self, widget):
        self.layout_.addWidget(widget)


class Modeline(QWidget):
    repainted = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(16)
        self.setStyleSheet("*[css_~='hover']:hover{background: white}")

        # Dynamic
        self.cursor_pos = QLabel(str(0))
        self.line_pos = QLabel(str(0))
        self.title = QLabel("")
        self.path = ""  # TODO
        self.chap_pos = QLabel(str(0))
        self.viewed_chap_pos = QLabel(str(0))
        # For chapTotal I need two: one for the group with cursor chapter
        #  information and one for viewed chapter information
        self.chap_total = QLabel(str(0))
        self.chap_total_dupe = QLabel(str(0))
        self.percentage = QLabel(str(0))

        # Static
        self.padding = 5
        self.pos_sep = QLabel(":")
        self.chap_pre = QLabel("c:")
        self.chap_sep = QLabel("/")
        self.colour1 = QColor(255, 215, 0)
        self.colour2 = QColor(205, 173, 0)
        self.colour3 = QColor(139, 117, 0)
        self.colour4 = QColor(198, 171, 120)

        def makeGroup(*widgets, tooltip):
            return WidgetsGroup(*widgets, css_="hover", tooltip=tooltip,
                                cursor=Qt.WhatsThisCursor)

        l_group = makeGroup(self.cursor_pos, self.pos_sep, self.line_pos,
                            tooltip="Line and character position of cursor")

        t_group = makeGroup(self.title, tooltip="path (TODO)")
        self.title.setStyleSheet("font-weight:bold")

        c_group = makeGroup(self.chap_pre, self.chap_pos,
                            self.chap_sep, self.chap_total,
                            tooltip="Chapter position of cursor")

        v_group = makeGroup(QLabel("v:"), self.viewed_chap_pos,
                            QLabel(self.chap_sep.text()),
                            self.chap_total_dupe,
                            tooltip="Chapter position of view")

        self.layout_ = RowLayout(self)
        self.layout_.setContentsMargins(0, self.padding, 0, 0)
        self.layout_.setSpacing(0)

        self.separators = [Separator(self.colour1, self.padding),
                           Separator(self.colour2, self.padding),
                           Separator(self.colour3, self.padding, False),
                           Separator(self.colour2, self.padding, False)]
        self.elements = [l_group, self.separators[0], t_group,
                         self.separators[1], c_group, Spacer(self.padding),
                         v_group, Spacer(45, self), self.separators[2],
                         self.separators[3]]
        for element in self.elements:
            self.layout_.addWidget(element)

    def setCursorPos(self, value):
        self.cursor_pos.setText(str(value))

    def setTitle(self, title):
        self.title.setText(title)

    def setLinePos(self, value):
        self.line_pos.setText(str(value))

    def setChapPos(self, value):
        self.chap_pos.setText(str(value))

    def setViewedChapPos(self, value):
        self.viewed_chap_pos.setText(str(value))

    def setChapTotal(self, value):
        self.chap_total.setText(str(value))
        self.chap_total_dupe.setText(str(value))

    def paintEvent(self, e):
        width = self.size().width()
        height = self.size().height()

        qp = QPainter()
        qp.begin(self)

        # Main rect
        qp.setPen(self.colour1)
        qp.setBrush(self.colour1)
        qp.drawRect(0, 0, width, height)

        for separator in reversed(self.separators):
            qp.setPen(separator.colour)
            qp.setBrush(separator.colour)
            qp.drawRect(0, 0, separator.pos().x() + self.padding, 16)

        qp.end()
        self.repainted.emit()
