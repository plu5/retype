import random
from enum import Enum
from datetime import timedelta
from qt import (QWidget, QSize, QTimer, QPainter, QPixmap, QRect, QTextCursor,
                pyqtSignal)

from typing import TYPE_CHECKING

from retype.ui import BookView
from retype.ui.painting import ellipsePixmap, transparent, Font, textPixmap
from retype.services.theme import theme, C, Theme


stages = {
    '1': {'name': 'Left hand, bottom row',
          'desc': '<i>Learn the steno keyboard:</i> Left hand, bottom row',
          'letters': ['S', 'K', 'W', 'R']},
    '2': {'name': 'Right hand, bottom row',
          'desc': '<i>Learn the steno keyboard:</i> Right hand, bottom row',
          'letters': ['-R', '-B', '-G', '-S', '-Z']},
    '3': {'name': 'Left hand, top row',
          'desc': '<i>Learn the steno keyboard:</i> Left hand, top row',
          'letters': ['S', 'T', 'P', 'H']},
    '4': {'name': 'Right hand, top row',
          'desc': '<i>Learn the steno keyboard:</i> Right hand, top row',
          'letters': ['-F', '-P', '-L', '-T', '-D']},
    '5': {'name': 'Vowels',
          'desc': '<i>Learn the steno keyboard:</i> Vowels',
          'letters': ['A', 'O', 'E', 'U']},
    '6': {'name': 'All left hand',
          'desc': '<i>Learn the steno keyboard:</i> All left hand',
          'letters': ['S', 'K', 'W', 'R', 'S', 'T', 'P', 'H', 'A', 'O']},
    '7': {'name': 'All right hand',
          'desc': '<i>Learn the steno keyboard:</i> All right hand',
          'letters': ['-R', '-B', '-G', '-S', '-Z', '-F', '-P', '-L', '-T',
                      '-D', 'E', 'U']},
    '8': {'name': 'All single-input keys',
          'desc': '<i>Learn the steno keyboard:</i> All single-input keys',
          'letters': ['S', 'K', 'W', 'R', 'S', 'T', 'P', 'H', 'A', 'O', '-R',
                      '-B', '-G', '-S', '-Z', '-F', '-P', '-L', '-T', '-D',
                      'E', 'U']}
}  # type: dict[str, Stage]

num_letters_per_stage = 100

selectors = {"key": "Games.Steno.Keyboard.Key",
             "main": "Games.Steno.Keyboard"}


@theme(selectors['key'], C(fg='black', bg='white', sel='gray'))
@theme(selectors['main'], C(bg='#CDCDC1'))
class VisualStenoKeyboard(QWidget):
    keySelected = pyqtSignal(str)

    def __init__(self,  # type: VisualStenoKeyboard
                 kdict=None,  # type: KDict | None
                 console=None,  # type: Console | None
                 parent=None  # type: QWidget | None
                 ):
        # type: (...) -> None
        super().__init__(parent)
        if console:
            console.subscribe(console.Ev.keypress, self._handleKeyPress)
            console.subscribe(console.Ev.keyrelease, self._handleKeyRelease)
        self._console = console
        self.kdict = kdict or {}
        self.keys = [
            {'l': 'S', 'x': 0, 'y': 0, 'r': True, 'dbl': True, 'on': False},
            {'l': 'T', 'x': 1, 'y': 0, 'r': False, 'dbl': False, 'on': False},
            {'l': 'K', 'x': 1, 'y': 1, 'r': True, 'dbl': False, 'on': False},
            {'l': 'P', 'x': 2, 'y': 0, 'r': False, 'dbl': False, 'on': False},
            {'l': 'W', 'x': 2, 'y': 1, 'r': True, 'dbl': False, 'on': False},
            {'l': 'H', 'x': 3, 'y': 0, 'r': False, 'dbl': False, 'on': False},
            {'l': 'R', 'x': 3, 'y': 1, 'r': True, 'dbl': False, 'on': False},
            {'l': '*', 'x': 4, 'y': 0, 'r': True, 'dbl': True, 'on': False},
            {'l': 'F', 'x': 5, 'y': 0, 'r': False, 'dbl': False, 'on': False},
            {'l': 'R', 'x': 5, 'y': 1, 'r': True, 'dbl': False, 'on': False},
            {'l': 'P', 'x': 6, 'y': 0, 'r': False, 'dbl': False, 'on': False},
            {'l': 'B', 'x': 6, 'y': 1, 'r': True, 'dbl': False, 'on': False},
            {'l': 'L', 'x': 7, 'y': 0, 'r': False, 'dbl': False, 'on': False},
            {'l': 'G', 'x': 7, 'y': 1, 'r': True, 'dbl': False, 'on': False},
            {'l': 'T', 'x': 8, 'y': 0, 'r': False, 'dbl': False, 'on': False},
            {'l': 'S', 'x': 8, 'y': 1, 'r': True, 'dbl': False, 'on': False},
            {'l': 'D', 'x': 9, 'y': 0, 'r': False, 'dbl': False, 'on': False},
            {'l': 'Z', 'x': 9, 'y': 1, 'r': True, 'dbl': False, 'on': False},
            {'l': 'A', 'x': 2, 'y': 2, 'r': True, 'dbl': False, 'on': False},
            {'l': 'O', 'x': 3, 'y': 2, 'r': True, 'dbl': False, 'on': False},
            {'l': 'E', 'x': 5, 'y': 2, 'r': True, 'dbl': False, 'on': False},
            {'l': 'U', 'x': 6, 'y': 2, 'r': True, 'dbl': False, 'on': False},
        ]  # type: list[Key]
        for k in self.keys:
            representation = k['l']
            if k['x'] > 4 and representation not in ['E', 'U']:
                representation = '-' + representation
            k['representation'] = representation
        self.should_enter_key_on_click = False
        self.should_select_key_on_click = False
        self.selected_key = None  # type: Key | None
        self.labels = {}  # type: dict[str, QPixmap]
        self._font = Font.GENERAL.toQFont()
        (self.c_key, self.c) = self._loadTheme()

    def _loadTheme(self):
        # type: (VisualStenoKeyboard) -> tuple[C, ...]
        return tuple(Theme.get(c) for c in selectors.values())

    def releaseKeys(self):
        # type: (VisualStenoKeyboard) -> None
        for k in self.keys:
            k['on'] = False
        self.update()

    def _getEquivalents(self, key):
        # type: (VisualStenoKeyboard, Key) -> list[str] | None
        return self.kdict.get(key['representation'])

    def _handleKeyPress(self, e):
        # type: (VisualStenoKeyboard, QKeyEvent) -> None
        if self.isHidden():
            return
        entered = e.text()
        for k in self.keys:
            equivalents = self._getEquivalents(k)
            if equivalents and entered.upper() in equivalents:
                k['on'] = True
                self.update()
                return

    def _handleKeyRelease(self, e):
        # type: (VisualStenoKeyboard, QKeyEvent) -> None
        if self.isHidden():
            return
        self.releaseKeys()

    def sizeHint(self):
        # type: (VisualStenoKeyboard) -> QSize
        return QSize(100, 100)

    def _keyPixmap(self, width, height, c, rad=0):
        # type: (VisualStenoKeyboard, int, int, QColor, int) -> QPixmap
        pixmap = QPixmap(int(width), int(height))
        pixmap.fill(transparent)
        qp = QPainter(pixmap)
        h = height-rad if rad else height
        qp.fillRect(0, 0, int(width), int(h), c)
        if rad:
            qp.drawPixmap(0, int(h - rad), ellipsePixmap(rad*2, rad*2, c, c))
        return pixmap

    def _textPixmap(self, width, height, text, font):
        # type: (VisualStenoKeyboard, int, int, str, Font) -> QPixmap
        return textPixmap(text, width, height, font)

    def selectKey(self, representation, emit=False):
        # type: (VisualStenoKeyboard, str, bool) -> None
        for k in self.keys:
            if k['representation'] == representation:
                if self.selected_key != k:
                    self.deselectKey()
                k['on'] = True
                self.selected_key = k
                if emit:
                    self.keySelected.emit(representation)
                self.update()
                return

    def deselectKey(self):
        # type: (VisualStenoKeyboard) -> None
        if self.selected_key:
            self.selected_key['on'] = False

    def mousePressEvent(self, e):
        # type: (VisualStenoKeyboard, QMouseEvent) -> None
        super().mousePressEvent(e)
        # NOTE(plu5): localPos is a QPointF and QRect.contains only
        # takes ints.
        pos = e.localPos().toPoint()
        for k in self.keys:
            loc = k.get('current_location')
            if not loc:
                return
            rec = QRect(*loc)
            if rec.contains(pos.x(), pos.y()):
                k['on'] = True
                self.update()
                if self._console and self.should_enter_key_on_click:
                    eqs = self._getEquivalents(k)
                    eq = eqs[0] if eqs else ''
                    self._console.setText(self._console.text() + eq)
                    self._console.moveCursor(QTextCursor.MoveOperation.End,
                                             QTextCursor.MoveMode.MoveAnchor)
                if self.should_select_key_on_click:
                    if self.selected_key != k:
                        self.deselectKey()
                    self.selected_key = k
                    self.keySelected.emit(k['representation'])
                return

    def mouseReleaseEvent(self, e):
        # type: (VisualStenoKeyboard, QMouseEvent) -> None
        super().mouseReleaseEvent(e)
        if not self.should_select_key_on_click:
            self.releaseKeys()

    def paintEvent(self, e):
        # type: (VisualStenoKeyboard, QPaintEvent) -> None
        w = self.size().width()
        h = self.size().height()

        qp = QPainter()
        qp.begin(self)
        draw = qp.drawPixmap

        # Background
        qp.fillRect(0, 0, w, h, self.c.bg())

        left_pad = 10
        self.kpad = 2
        self.kwidth = int((h - self.kpad*4) / 3)
        self.kheight = self.kwidth
        width_required = self.kwidth*10 + self.kpad*10
        if width_required > w:
            self.kwidth = int((w - self.kpad*11) / 10)
            self.kheight = int((h - self.kpad*4) / 3)
            left_pad = 0
        else:
            left_pad = min(left_pad, w - width_required)
        if self.kwidth < 1:
            return
        c = self.c_key.bg()
        onc = self.c_key.sel()
        krad = int(self.kwidth/2)
        self.r1top = self.kpad
        self.r2top = self.r1top + self.kpad + self.kwidth

        self.key = self._keyPixmap(self.kwidth, self.kheight, c)
        self.rkey = self._keyPixmap(self.kwidth, self.kheight, c, krad)
        self.drkey = self._keyPixmap(
            self.kwidth, self.kheight*2 + self.kpad, c, krad)
        self.onkey = self._keyPixmap(self.kwidth, self.kheight, onc)
        self.onrkey = self._keyPixmap(self.kwidth, self.kheight, onc, krad)
        self.ondrkey = self._keyPixmap(
            self.kwidth, self.kheight*2 + self.kpad, onc, krad)

        for t in ['S', 'T', 'K', 'P', 'W', 'H', 'R', '*', 'F', 'B', 'L', 'G',
                  'D', 'Z', 'A', 'O', 'E', 'U']:
            self.labels[t] = textPixmap(t, self.kwidth, self.kheight,
                                        self._font, self.c_key.fg())

        for k in self.keys:
            x = k['x']
            x = left_pad + x*self.kwidth + x*self.kpad + self.kpad
            y = k['y']
            y = y*self.kheight + y*self.kpad + self.kpad
            shape = self.key
            if k['on']:
                shape = self.ondrkey if k['dbl'] else (
                    self.onrkey if k['r'] else self.onkey)
            else:
                shape = self.drkey if k['dbl'] else (
                    self.rkey if k['r'] else self.key)
            draw(x, y, shape)
            label = self.labels[k['l']]
            draw(x, y + int(shape.height()/2) - int(label.height()/2), label)
            k['current_location'] = [x, y, shape.width(), shape.height()]


class StenoBook:
    def __init__(self, html='', letters=None, titleext=''):
        # type: (StenoBook, str, list[str] | None, str) -> None
        self.path = ''
        self.title = 'Learn Stenography' + titleext
        self.progress = 0.0
        s = h = ''
        letters = letters or []
        if len(letters):
            selection = []
            for i in range(num_letters_per_stage):
                selection.append(f'{random.choice(letters)} ')
            s = ''.join(selection)
        h = s + html
        if not len(s):
            s = html
        self.chapters = [{'len': len(s), 'html': h, 'plain': s, 'images': []}
                         ]  # type: list[Chapter]
        self.chapter_lookup = {}  # type: dict[str, int]
        self.dirty = False

    def updateProgress(self, *args):
        # type: (StenoBook, object) -> None
        pass


class State(Enum):
    stage_selection = 1
    in_progress = 2


class StenoView(BookView):
    def __init__(self,  # type: StenoView
                 main_win,  # type: MainWin
                 main_controller,  # type: MainController
                 bookview_settings,  # type: BookViewSettings
                 kdict=None  # type: KDict | None
                 ):
        # type: (...) -> None
        super().__init__(main_win, main_controller,
                         bookview_settings=bookview_settings, parent=main_win)
        self._console = main_controller.console
        kdict = kdict or {}
        self.setKdict(kdict)
        self.wrong_start = None  # type: int | None
        self.skip_action.setDisabled(True)
        self._stageSelectionScreen()
        self.return_entry = '0'
        self.visual_kbd = VisualStenoKeyboard(self.kdict, self._console, self)
        self.stats_dock.deleteLater()
        self.autosave.deleteLater()
        self.splitter.addWidget(self.visual_kbd)
        self.stage = None  # type: Stage | None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tallySeconds)
        self.seconds = 0
        self.started = self.paused = False

    def setKdict(self, kdict):
        # type: (StenoView, KDict) -> None
        self.kdict = kdict
        translation = {}
        for a, b in self.kdict.items():
            for c in b:
                s = f'{a} '
                translation[c] = s
                translation[c.lower()] = s
        self.trans = str.maketrans(translation)

    def maybeSave(self):
        # type: (StenoView) -> None
        pass

    def showEvent(self, e):
        # type: (StenoView, QShowEvent) -> None
        super().showEvent(e)
        self._console.returnPressed.connect(self._handleEntry)
        self._console.textChanged.connect(self._handleHighlighting)
        if self.paused:
            self.resume()

    def hideEvent(self, e):
        # type: (StenoView, QHideEvent) -> None
        super().hideEvent(e)
        self._console.returnPressed.disconnect(self._handleEntry)
        self._console.textChanged.disconnect(self._handleHighlighting)
        if self.started:
            self.pause()

    def _tallySeconds(self):
        # type: (StenoView) -> None
        self.seconds += 1

    def _startTimer(self):
        # type: (StenoView) -> None
        self.seconds = 0
        self.resume()

    def _stopTimer(self):
        # type: (StenoView) -> None
        self.timer.stop()
        self.started = False

    def _start(self):
        # type: (StenoView) -> None
        self._startTimer()
        self.visual_kbd.should_enter_key_on_click = True

    def _stop(self):
        # type: (StenoView) -> None
        self._stopTimer()
        self.visual_kbd.should_enter_key_on_click = False

    def resume(self):
        # type: (StenoView) -> None
        self.timer.start(1000)
        self.started = True
        self.paused = False

    def pause(self):
        # type: (StenoView) -> None
        self._stop()
        self.paused = True

    def _stageSelectionScreen(self, ended=False):
        # type: (StenoView, bool) -> None
        self.state = State.stage_selection

        lines = []
        lines.append("<h1>Learn Stenography</h1>")
        if ended and self.stage is not None:
            lines.append("<hr/>")
            lines.append(f"<b>Completed stage:</b> {self.stage['name']}<br/>")
            lines.append(f"<b>Time:</b> {timedelta(seconds=self.seconds)} -\
 {int(60 / self.seconds * num_letters_per_stage)} strokes per minute")
            lines.append("<hr/>")
        lines.append("<p>Choose a training stage (enter number):</p>")
        for i, stage in stages.items():
            lines.append(f'<p><b>{i}</b>: {stage["desc"]}</p>')

        self.setBook(StenoBook(''.join(lines)))

    def _setStage(self, stage):
        # type: (StenoView, Stage) -> None
        self.stage = stage
        html = f"<hr/><p><i>Enter {self.return_entry} to back out to\
 stage selection.</i></p>"
        self.setBook(StenoBook(
            html, stage.get('letters'), f': {stage["name"]}'))
        self.state = State.in_progress
        self._start()

    def _handleEntry(self):
        # type: (StenoView) -> None
        text = self._console.text()
        if self.state == State.stage_selection:
            matching = stages.get(text)
            if matching:
                self._console.clear()
                self._setStage(matching)
        elif self.state == State.in_progress:
            if text == self.return_entry:
                self._console.clear()
                self._stop()
                self._stageSelectionScreen()

    def _handleHighlighting(self, text):
        # type: (StenoView, str) -> None
        if self.state != State.in_progress or self.cursor_pos is None:
            return
        end_correctness_index = 0
        if self.cursor_pos < len(self.current_line):
            a = self.current_line[self.cursor_pos]
            increment = 2
            if a == '-' and self.cursor_pos + 1 < len(self.current_line):
                a += self.current_line[self.cursor_pos + 1]
                increment = 3
            if len(text) == 1 and a in self.kdict:
                # Match
                for c in self.kdict[str(a)]:
                    if text.upper() == c:
                        self.cursor_pos += increment
                        self._console.clear()
                        self.updateHighlighting()
                        end_correctness_index = 1
                        # Note: This will end early if there is more than one
                        #  line to be typed. At the moment for steno training I
                        #  don't see the point in breaking it up into multiple
                        #  lines, so I use only one.
                        if self.cursor_pos == len(self.current_line) - 1:
                            self._stop()
                            self._stageSelectionScreen(True)
            self._handleMistakes(self, text, end_correctness_index)

    def updateHighlighting(self):
        # type: (StenoView) -> None
        self.updateCursorPosition()
        self.updateHighlightCursor()
        self.updateModeline()

    def _handleMistakes(self, v, text, end_correctness_index):
        # type: (StenoView, BookView, str, int) -> None
        if v.cursor_pos is None:
            return

        # The way this works is if there’s any previous wrong_text it gets
        #  entirely removed, then readded as necessary.
        if self.wrong_start is not None and self.wrong_end is not None:
            self._removeWrongText(v, self.wrong_start, self.wrong_end)
        else:
            self.wrong_start = v.cursor_pos + end_correctness_index

        self.wrong_text = text[end_correctness_index:]

        # Show steno chars in wrong text
        self.wrong_text = self.wrong_text.translate(self.trans)

        # If not (or no longer) wrong, reset wrong-tracking variables and
        #  silently follow the cursor pos.
        if not self.wrong_text:
            self.wrong = False
            self.wrong_start = None
            self.wrong_end = None  # type: int | None
            v.mistake_cursor.setPosition(v.cursor_pos)
            return

        self.wrong = True
        v.mistake_cursor.setPosition(self.wrong_start)
        self._insertWrongText(v, v.mistake_cursor.position(), self.wrong_text)
        self.wrong_end = self.wrong_start + len(self.wrong_text)

    def _insertWrongText(self, v, pre_pos, text):
        # type: (StenoView, BookView, int, str) -> None
        v.mistake_cursor.setPosition(pre_pos, v.mistake_cursor.MoveAnchor)
        v.mistake_cursor.insertText(text, v.mistake_format)
        self.updateHighlighting()
        if pre_pos == 0:
            self.display.setExtraSelections([])

    def _removeWrongText(self, v, start, end):
        # type: (StenoView, BookView, int, int) -> None
        v.mistake_cursor.setPosition(start, v.mistake_cursor.MoveAnchor)
        v.mistake_cursor.setPosition(end, v.mistake_cursor.KeepAnchor)
        v.mistake_cursor.removeSelectedText()


if TYPE_CHECKING:
    from retype.extras.metatypes import (  # noqa: F401
        KDict, BookViewSettings, Chapter)
    from retype.ui import MainWin  # noqa: F401
    from retype.controllers import MainController  # noqa: F401
    from retype.console import Console  # noqa: F401
    from qt import (  # noqa: F401
        QKeyEvent, QMouseEvent, QShowEvent, QHideEvent, QPaintEvent, QColor)
    from typing import TypedDict
    Stage = TypedDict(
        'Stage',
        {'name': str, 'desc': str, 'letters': list[str]})
    Key = TypedDict(
        'Key',
        {'l': str, 'x': int, 'y': int, 'r': bool, 'dbl': bool, 'on': bool,
         'representation': str, 'current_location': list[int]}, total=False)
