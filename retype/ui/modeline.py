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
            self.p.repainted.connect(self.update_)
        else:
            self.setFixedWidth(self.width)

    def update_(self):
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

        self.hover_css = ''

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

    def setHoverStyle(self, css):
        self.hover_css = css

    def enterEvent(self, e):
        self.old_stylesheet = self.styleSheet()
        self.setStyleSheet(self.old_stylesheet + self.hover_css)

    def leaveEvent(self, e):
        self.setStyleSheet(self.old_stylesheet)


class Modeline(QWidget):
    repainted = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(16)
        self.setStyleSheet("*[css_~='hover']:hover{background: white}")

        # Dynamic
        self.title = QLabel("")
        self.path = QLabel("")
        self.line_pos = QLabel(str(0))
        self.cursor_pos = QLabel(str(0))
        self.chap_pos = QLabel(str(0))
        self.viewed_chap_pos = QLabel(str(0))
        # Two chap totals because it needs to be displayed twice; in the cursor
        #  chapter information and viewed chapter information. Qt does not
        #  allow the same widget to be in two different places at once.
        self.chap_total = QLabel(str(0))
        self.chap_total_dupe = QLabel(str(0))
        self.progress = QLabel(str(0))

        # Static
        self.padding = 5
        self.pos_sep = QLabel(":")
        self.chap_pre = QLabel("c:")
        self.chap_sep = QLabel("/")
        self.colour1 = QColor(255, 215, 0)
        self.colour2 = QColor(205, 173, 0)
        self.colour3 = QColor(139, 117, 0)

        def makeGroup(*widgets, tooltip):
            return WidgetsGroup(*widgets, css_="hover", tooltip=tooltip,
                                cursor=Qt.WhatsThisCursor)

        l_group = makeGroup(self.line_pos, self.pos_sep, self.cursor_pos,
                            tooltip="Line and character position of cursor")

        self.t_group = makeGroup(self.title, tooltip="?")
        self.title.setStyleSheet("font-weight:bold")

        p_group = makeGroup(self.progress, QLabel("%"),
                            tooltip="Progress percentage")
        p_group.setStyleSheet("QLabel{color: yellow}")
        p_group.setHoverStyle("QLabel{color: brown}")

        self.c_group = makeGroup(self.chap_pre, self.chap_pos,
                                 self.chap_sep, self.chap_total,
                                 tooltip="Chapter position of cursor")

        self.v_group = makeGroup(QLabel("v:"), self.viewed_chap_pos,
                                 QLabel(self.chap_sep.text()),
                                 self.chap_total_dupe,
                                 tooltip="Chapter position of view")

        self.layout_ = RowLayout(self)
        self.layout_.setContentsMargins(0, self.padding, 0, 0)
        self.layout_.setSpacing(0)

        # A spacer which serves to push the left-facing end separators to the
        #  right
        self.push_to_right = Spacer(112, self)

        self.separators = [
            Separator(self.colour1, self.padding),
            Separator(self.colour2, self.padding),
            Separator(self.colour3, self.padding, False),
            Separator(self.colour2, self.padding, False)
        ]
        self.elements = [
            # line:char
            l_group, self.separators[0],
            # title
            self.t_group, self.separators[1],
            # progress %
            Spacer(self.padding / 2), p_group,
            self.push_to_right,
            # chapter/total, viewed_chapter/total
            self.separators[2], self.v_group,
            self.separators[3], self.c_group,
        ]
        for element in self.elements:
            self.layout_.addWidget(element)

    def update_(self, title=None, cursor_pos=None, line_pos=None,
                chap_pos=None, viewed_chap_pos=None, chap_total=None,
                path=None, progress=None):
        for p, v in vars().items():
            if v is not None and p != "self":
                self.__dict__[p].setText(str(v))

        if chap_total is not None:
            self.chap_total_dupe.setText(str(chap_total))

        if path is not None:
            self.t_group.setToolTip(path)

        # Update width of push_to_right spacer based on new width of right
        #  widgets if their values changed
        if any([chap_pos, viewed_chap_pos, chap_total]):
            self.c_group.adjustSize()
            self.v_group.adjustSize()
            self.push_to_right.width = self.c_group.rect().width() + \
                self.v_group.rect().width() + 50

        self.repaint()

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
