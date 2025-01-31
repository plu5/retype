from math import floor
from qt import (QWidget, QPainter, QColor, Qt, QPixmap, QPoint, QPolygon,
                QLabel, pyqtSignal, QFrame, QSize, QSizePolicy)

from typing import TYPE_CHECKING

from retype.layouts import RowLayout
from retype.services.theme import theme, C, Theme


class Separator(QWidget):
    def __init__(self, c, facing_right=True):
        # type: (Separator, C, bool) -> None
        super().__init__()
        self.c = c
        self.facing_right = facing_right
        self.setSizePolicy(QSizePolicy.Policy.Preferred,
                           QSizePolicy.Policy.Expanding)
        self._calc(self.width(), self.height())

    def hasHeightForWidth(self):
        # type: (Separator) -> bool
        return True

    def heightForWidth(self, height):
        # type: (Separator, int) -> int
        """Despite the name, this returns width for height"""
        return int(height / 2)

    def sizeHint(self):
        # type: (Separator) -> QSize
        """Minimum"""
        h = 4
        return QSize(self.heightForWidth(h), h)

    def _calc(self, width, height):
        # type: (Separator, int, int) -> tuple[int, int, int]
        half = floor((height - 1) / 2)
        chupchik = (height - 2 * half) - 1
        return (height, half, chupchik)

    def pixmap(self, width, height):
        # type: (Separator, int, int) -> QPixmap
        p = QPixmap(width, height)
        p.fill(QColor('transparent'))
        qp = QPainter(p)
        qp.setPen(self.c.bg())
        qp.setBrush(self.c.bg())

        h, half, chupchik = self._calc(width, height)
        if self.facing_right:
            points = [QPoint(0, 0), QPoint(0, chupchik),
                      QPoint(half, chupchik + half), QPoint(0, h)]
        else:
            points = [QPoint(0, 0), QPoint(half, 0),
                      QPoint(half, chupchik), QPoint(0, half + chupchik),
                      QPoint(half, h - 1), QPoint(0, h - 1)]
        qp.drawPolygon(QPolygon(points))

        return p

    def paintEvent(self, e):
        # type: (Separator, QPaintEvent) -> None
        qp = QPainter()
        qp.begin(self)
        qp.drawPixmap(0, 0, self.pixmap(self.width(), self.height()))
        qp.end()


class WidgetsGroup(QFrame):
    def __init__(self,  # type: WidgetsGroup
                 *widgets,  # type: QWidget
                 css_=None,  # type: str | None
                 tooltip=None,  # type: str | None
                 cursor=None  # type: Qt.CursorShape | None
                 ):
        # type: (...) -> None
        super().__init__()
        self.layout_ = RowLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(0)
        self.setSizePolicy(QSizePolicy.Policy.Preferred,
                           QSizePolicy.Policy.Expanding)

        self.hover_css = ''

        if css_:
            self.setProperty("css_", css_)
        if tooltip:
            self.setToolTip(tooltip)
        if cursor:
            self.setCursor(cursor)

        for widget in widgets:
            self.addWidget(widget)

    def addWidget(self, widget):
        # type: (WidgetsGroup, QWidget) -> None
        self.layout_.addWidget(widget)

    def setHoverStyle(self, css):
        # type: (WidgetsGroup, str) -> None
        self.hover_css = css

    def enterEvent(self, e):
        # type: (WidgetsGroup, QEvent) -> None
        self.old_stylesheet = self.styleSheet()
        self.setStyleSheet(self.old_stylesheet + self.hover_css)

    def leaveEvent(self, e):
        # type: (WidgetsGroup, QEvent) -> None
        self.setStyleSheet(self.old_stylesheet)


@theme('BookView.Modeline.OuterSegment',
       C(fg='black', bg='#FFD700', sel_bg='white'))
@theme('BookView.Modeline.MidSegment',
       C(fg='black', bg='#CDAD00', sel_bg='white'))
@theme('BookView.Modeline.InnerSegment',
       C(fg='yellow', bg='#8B7500', sel='brown', sel_bg='white'))
class Modeline(QWidget):
    repainted = pyqtSignal()

    def __init__(self, parent=None):
        # type: (Modeline, QWidget | None) -> None
        super().__init__(parent)
        self.setMinimumHeight(16)

        self.c_outer, self.c_mid, self.c_inner = self._loadTheme()

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
        self.percent = QLabel("%")
        self.pos_sep = QLabel(":")
        self.chap_pre = QLabel("c:")
        self.chap_sep = QLabel("/")
        self.vchap_pre = QLabel("v:")
        self.vchap_sep = QLabel("/")

        def makeGroup(*widgets, tooltip):
            # type: (QWidget, str) -> WidgetsGroup
            return WidgetsGroup(*widgets, css_="hover", tooltip=tooltip,
                                cursor=Qt.CursorShape.WhatsThisCursor)

        self.l_group = makeGroup(
            self.line_pos, self.pos_sep, self.cursor_pos,
            tooltip="Line and character position of cursor")

        self.t_group = makeGroup(self.title, tooltip="?")
        self.title.setStyleSheet("font-weight:bold")

        self.p_group = makeGroup(self.progress, self.percent,
                                 tooltip="Progress percentage")

        self.c_group = makeGroup(self.chap_pre, self.chap_pos,
                                 self.chap_sep, self.chap_total,
                                 tooltip="Chapter position of cursor")

        self.v_group = makeGroup(self.vchap_pre, self.viewed_chap_pos,
                                 self.vchap_sep,
                                 self.chap_total_dupe,
                                 tooltip="Chapter position of view")

        self.layout_ = RowLayout(self)
        self.layout_.setContentsMargins(0, self.padding, 0, 0)
        self.layout_.setSpacing(self.padding)

        # A spacer which serves to push the left-facing end separators to the
        #  right
        self.push_to_right = QWidget()
        self.push_to_right.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.separators = [
            Separator(self.c_outer),
            Separator(self.c_mid),
            Separator(self.c_inner, False),
            Separator(self.c_mid, False)
        ]
        self.elements = [
            # line:char
            self.l_group, self.separators[0],
            # title
            self.t_group, self.separators[1],
            # progress %
            self.p_group,
            self.push_to_right,
            # chapter/total, viewed_chapter/total
            self.separators[2], self.v_group,
            self.separators[3], self.c_group,
        ]
        for element in self.elements:
            self.layout_.addWidget(element)

        self.widgets_by_segment = ([self.l_group, self.c_group],
                                   [self.t_group, self.v_group],
                                   [self.p_group])
        self.c = (self.c_outer, self.c_mid, self.c_inner)

        self.c_inner.changed.connect(self.themeUpdate)
        self.themeUpdate()

    def _loadTheme(self):
        # type: (Modeline) -> tuple[C, ...]
        return (Theme.get('BookView.Modeline.OuterSegment'),
                Theme.get('BookView.Modeline.MidSegment'),
                Theme.get('BookView.Modeline.InnerSegment'))

    def themeUpdate(self):
        # type: (Modeline) -> None
        for widgets, c in zip(self.widgets_by_segment, self.c):
            for w in widgets:
                w.setStyleSheet(f"QLabel{{color: {c.fg().name()}}}\
 *[css_~='hover']:hover{{background: {c.sel_bg().name()}}}")
                w.setHoverStyle(f'QLabel{{color: {c.sel().name()}}}')
        self.update()

    def update_(self,  # type: Modeline
                title=None,  # type: str | None
                cursor_pos=None,  # type: int | str | None
                line_pos=None,  # type: int | str | None
                chap_pos=None,  # type: int | str | None
                viewed_chap_pos=None,  # type: int | str | None
                chap_total=None,  # type: int | str | None
                path=None,  # type: str | None
                progress=None  # type: float | str | None
                ):
        # type: (...) -> None
        for p, v in vars().items():  # type: ignore[misc]
            if v is not None and p != "self":  # type: ignore[misc]
                self.__dict__[p].setText(str(v))  # type: ignore[misc]

        if chap_total is not None:
            self.chap_total_dupe.setText(str(chap_total))

        if path is not None:
            self.t_group.setToolTip(path)

        # Update width of push_to_right spacer based on new width of right
        #  widgets if their values changed
        if any([chap_pos, viewed_chap_pos, chap_total]):
            self.c_group.adjustSize()
            self.v_group.adjustSize()
            # TODO: The line below was here but doesn't do anything
            # self.push_to_right.width = self.c_group.rect().width() + \
            #     self.v_group.rect().width() + 50

        self.update()

    def paintEvent(self, e):
        # type: (Modeline, QPaintEvent) -> None
        width = self.size().width()
        height = self.size().height()

        qp = QPainter()
        qp.begin(self)

        # Main rect
        qp.setPen(self.c_outer.bg())
        qp.setBrush(self.c_outer.bg())
        qp.drawRect(0, 0, width, height)

        for separator in reversed(self.separators):
            qp.setPen(separator.c.bg())
            qp.setBrush(separator.c.bg())
            qp.drawRect(0, 0, separator.pos().x(), height)

        qp.end()
        self.repainted.emit()


if TYPE_CHECKING:
    from qt import QPaintEvent, QCursor, QEvent  # noqa: F401
