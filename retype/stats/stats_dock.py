from math import floor, ceil
from time import time
from qt import QWidget, QPainter, Qt, QSize, QFontMetricsF

from typing import TYPE_CHECKING

from retype.ui.painting import rectPixmap, textPixmap, linePixmap, Font
from retype.services.theme import theme, C, Theme


@theme('BookView.StatsDock.Main', C(fg='white', bg='#CDCDC1'))
@theme('BookView.StatsDock.Text', C(fg='black'))
@theme('BookView.StatsDock.Grid', C(fg='gray'))
class StatsDock(QWidget):
    def __init__(self, book_view, parent=None):
        # type: (StatsDock, BookView, QWidget | None) -> None
        super().__init__(parent)
        self.book_view = book_view

        self.connected = False

        self.prev_cursor_pos = 0
        self.prev_seconds = 0
        self.prev_ts = 0
        self.c = 0
        self.cpm = 0
        self.wpm = 0
        self.wpm_pb = 0
        self.wpms = []  # type: list[int]

        self.main_c, self.text_c, self.grid_c = self._loadTheme()
        self.main_c.changed.connect(self.themeUpdate)

    def _loadTheme(self):
        # type: (StatsDock) -> tuple[C, ...]
        return (Theme.get('BookView.StatsDock.Main'),
                Theme.get('BookView.StatsDock.Text'),
                Theme.get('BookView.StatsDock.Grid'))

    def themeUpdate(self):
        # type: (StatsDock) -> None
        self.update()

    def connectConsole(self, console):
        # type: (StatsDock, Console) -> None
        self._hs = console.highlighting_service
        console.textEdited.connect(self.onUpdate)
        self.connected = True

    def onUpdate(self, text):
        # type: (StatsDock, str) -> None
        v = self.book_view
        if not v.isVisible() or v.cursor_pos is None:
            return

        ts = round(time())
        # Start “timer”
        if not self.prev_ts:
            self.prev_ts = ts

        seconds = (ts - self.prev_ts) or 1

        # Reset if been inactive
        if seconds - self.prev_seconds > 2:
            self.prev_ts = ts
            self.c = 0

        graphShouldUpdate = False
        # FIXME: This is probably not very robust; it’s an attempt to make
        #  things work for both character-by-character typing and stenography
        #  where whole words can be inputted at once, while preventing the
        #  cursor-maniplation commands from affecting the count undesirably.
        if len(text) >= v.cursor_pos - self.prev_cursor_pos > 0:
            self.c += v.cursor_pos - self.prev_cursor_pos
            graphShouldUpdate = True

        # CPM and WPM calculation
        self.cpm = floor((self.c / seconds) * 60)
        self.wpm = floor(self.cpm / 5)

        # Personal best
        if self.wpm > self.wpm_pb:
            self.wpm_pb = self.wpm

        # Periodic refreshment
        if seconds > 20:
            self.prev_ts = ts - 5
            self.c = int(self.cpm / 12)

        # Graph update
        if graphShouldUpdate:
            self.rect_w = 15
            w = self.size().width()
            amount = floor(w / self.rect_w)
            if len(self.wpms) > amount:
                length = len(self.wpms)
                self.wpms = self.wpms[length-amount:length]
            self.wpms.append(self.wpm)
            self.update()

        self.prev_seconds = seconds
        self.prev_cursor_pos = v.cursor_pos

    def paintEvent(self, e):
        # type: (StatsDock, QPaintEvent) -> None
        w = self.size().width()
        h = self.size().height()
        factor = 1 if not self.wpm_pb else h/self.wpm_pb

        qp = QPainter()
        qp.begin(self)
        draw = qp.drawPixmap

        # Background
        qp.fillRect(0, 0, w, h, self.main_c.bg())

        # WPM rects
        i = 0
        for wpm in self.wpms:
            rect_h = floor(wpm * factor)
            draw(i, h - rect_h,
                 rectPixmap(self.rect_w, int(wpm * factor),
                            self.main_c.bg(), self.main_c.fg()))
            i += self.rect_w

        # Gridlines
        i = 50
        while i < self.wpm_pb:
            y = h - int(i * factor)
            qp.drawPixmap(0, y,
                          linePixmap(w, 0, self.grid_c.fg(), 1,
                                     style=Qt.PenStyle.DashLine))
            i += 50

        # Text
        font = Font.GENERAL.toQFont()
        fm = QFontMetricsF(font)
        font_h = ceil(fm.height())
        pb_txt = "PB: {}".format(self.wpm_pb)
        cur_txt = "Current: {} WPM".format(self.wpm)
        draw(2, 2,
             textPixmap(pb_txt, ceil(fm.horizontalAdvance(pb_txt)), font_h,
                        font, self.text_c.fg()))
        cur_w = ceil(fm.horizontalAdvance(cur_txt))
        draw(w - cur_w - 2, 2,
             textPixmap(cur_txt, cur_w, font_h, font, self.text_c.fg()))

        qp.end()

    def sizeHint(self):
        # type: (StatsDock) -> QSize
        return QSize(50, 25)


if TYPE_CHECKING:
    from retype.ui import BookView  # noqa: F401
    from retype.console import Console  # noqa: F401
    from qt import QPaintEvent  # noqa: F401
