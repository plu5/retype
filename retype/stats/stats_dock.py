from math import floor
from time import time
from qt import QWidget, QPainter, QFont, Qt, QSize, QColor, QFontMetricsF

from retype.ui.painting import rectPixmap, textPixmap, linePixmap


class StatsDock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.connected = False

        self.prev_cursor_pos = 0
        self.prev_seconds = 0
        self.prev_ts = 0
        self.c = 0
        self.cpm = 0
        self.wpm = 0
        self.wpm_pb = 0
        self.wpms = []

        self.background_colour = QColor('#CDCDC1')
        self.foreground_colour = QColor('white')
        self.text_colour = QColor('black')
        self.grid_colour = QColor('gray')

    def connectConsole(self, console):
        self._hs = console.highlighting_service
        console.textEdited.connect(self.onUpdate)
        self.connected = True

    def onUpdate(self, text):
        v = self._hs.book_view
        if not v.isVisible:
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
            self.c = self.cpm / 12

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
        w = self.size().width()
        h = self.size().height()
        factor = 1 if not self.wpm_pb else h/self.wpm_pb

        qp = QPainter()
        qp.begin(self)
        draw = qp.drawPixmap

        # Background
        qp.fillRect(0, 0, w, h, self.background_colour)

        # WPM rects
        i = 0
        for wpm in self.wpms:
            rect_h = floor(wpm * factor)
            draw(i, h - rect_h,
                 rectPixmap(self.rect_w, wpm * factor,
                            self.background_colour, self.foreground_colour))
            i += self.rect_w

        # Gridlines
        i = 50
        while i < self.wpm_pb:
            y = h - (i * factor)
            qp.drawPixmap(0, y,
                          linePixmap(w, 0, self.grid_colour, 1,
                                     style=Qt.PenStyle.DashLine))
            i += 50

        # Text
        font = QFont('Times', 9, 0)
        fm = QFontMetricsF(font)
        font_h = fm.height()
        pb_txt = "PB: {}".format(self.wpm_pb)
        cur_txt = "Current: {} WPM".format(self.wpm)
        draw(2, 2,
             textPixmap(pb_txt, fm.horizontalAdvance(pb_txt), font_h,
                        font, self.text_colour))
        cur_w = fm.horizontalAdvance(cur_txt)
        draw(w - cur_w - 2, 2,
             textPixmap(cur_txt, cur_w, font_h, font, self.text_colour))

        qp.end()

    def sizeHint(self):
        return QSize(50, 25)
