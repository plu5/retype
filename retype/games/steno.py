import random
from enum import Enum
from datetime import timedelta
from qt import QWidget, QSize, QTimer, QPainter, QPixmap, QRect, QTextCursor

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
}
keyboard = {'S': ['A', 'Q'], 'K': ['S'], 'W': ['D'], 'R': ['F'],
            '-R': ['J'], '-B': ['K'], '-G': ['L'], '-S': [';'], '-Z': ["'"],
            'T': ['W'], 'P': ['E'], 'H': ['R'],
            '-F': ['U'], '-P': ['I'], '-L': ['O'], '-T': ['P'], '-D': ['['],
            'A': ['C'], 'O': ['V'], 'E': ['N'], 'U': ['M'],
            '*': ['G', 'H', 'T', 'Y']}
translation = {}
num_letters_per_stage = 100

for a, b in keyboard.items():
    for c in b:
        s = f'{a} '
        translation[c] = s
        translation[c.lower()] = s

trans = str.maketrans(translation)

selectors = {"key": "Games.Steno.Keyboard.Key",
             "main": "Games.Steno.Keyboard"}


@theme(selectors['key'], C(fg='black', bg='white', sel='gray'))
@theme(selectors['main'], C(bg='#CDCDC1'))
class VisualStenoKeyboard(QWidget):
    def __init__(self, console, parent=None):
        super().__init__(parent)
        console.subscribe(console.Ev.keypress, self._handleKeyPress)
        console.subscribe(console.Ev.keyrelease, self._handleKeyRelease)
        self._console = console
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
        ]
        self.should_enter_key_on_click = False
        self.labels = {}
        self.font = Font.GENERAL.toQFont()
        (self.c_key, self.c) = self._loadTheme()

    def _loadTheme(self):
        return tuple(Theme.get(c) for c in selectors.values())

    def releaseKeys(self):
        for k in self.keys:
            k['on'] = False
        self.update()

    def _handleHighlighting(self, text):
        if not len(text):
            return
        c = text[-1]
        if translation.get(c):
            pass

    def _getEquivalents(self, key):
        label = key['l']
        if key['x'] > 4 and label not in ['E', 'U']:
            label = '-' + label
        return keyboard.get(label)

    def _handleKeyPress(self, e):
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
        if self.isHidden():
            return
        self.releaseKeys()

    def sizeHint(self):
        return QSize(100, 100)

    def _keyPixmap(self, width, height, c, rad=0):
        pixmap = QPixmap(width, height)
        pixmap.fill(transparent)
        qp = QPainter(pixmap)
        h = height-rad if rad else height
        qp.fillRect(0, 0, width, h, c)
        if rad:
            qp.drawPixmap(0, h - rad, ellipsePixmap(rad*2, rad*2, c, c))
        return pixmap

    def _textPixmap(self, width, height, text, font):
        return textPixmap(text, width, height, font)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        pos = e.localPos()
        for k in self.keys:
            loc = k.get('current_location')
            if not loc:
                return
            loc = QRect(*loc)
            if loc.contains(pos.x(), pos.y()):
                k['on'] = True
                self.update()
                if self.should_enter_key_on_click:
                    eq = self._getEquivalents(k)
                    eq = eq[0] if eq else ''
                    self._console.setText(self._console.text() + eq)
                    self._console.moveCursor(QTextCursor.MoveOperation.End,
                                             QTextCursor.MoveMode.MoveAnchor)
                return

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.releaseKeys()

    def paintEvent(self, e):
        w = self.size().width()
        h = self.size().height()
        qp = QPainter()
        qp.begin(self)
        draw = qp.drawPixmap

        # Background
        qp.fillRect(0, 0, w, h, self.c.bg())

        left_pad = 10
        self.kpad = 2
        self.kwidth = (h - self.kpad*4) / 3
        self.kheight = self.kwidth
        width_required = self.kwidth*10 + self.kpad*10
        if width_required > w:
            self.kwidth = (w - self.kpad*11) / 10
            self.kheight = (h - self.kpad*4) / 3
            left_pad = 0
        else:
            left_pad = min(left_pad, w - width_required)
        if self.kwidth < 1:
            return
        c = self.c_key.bg()
        onc = self.c_key.sel()
        krad = self.kwidth/2
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
                                        self.font, self.c_key.fg())

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
            draw(x, y + shape.height()/2 - label.height()/2, label)
            k['current_location'] = [x, y, shape.width(), shape.height()]


class StenoBook:
    def __init__(self, html='', letters=[], titleext=''):
        self.path = ''
        self.title = 'Learn Stenography' + titleext
        self.progress = 0
        s = h = ''
        if len(letters):
            selection = []
            for i in range(num_letters_per_stage):
                selection.append(f'{random.choice(letters)} ')
            s = ''.join(selection)
        h = s + html
        if not len(s):
            s = html
        self.chapters = [{'len': len(s), 'html': h, 'plain': s, 'images': []}]
        self.dirty = False

    def updateProgress(self, *args):
        pass


class State(Enum):
    stage_selection = 1
    in_progress = 2


class StenoView(BookView):
    def __init__(self, main_win, main_controller, bookview_settings):
        super().__init__(main_win, main_controller,
                         bookview_settings=bookview_settings, parent=main_win)
        self._console = main_controller.console
        self.wrong_start = None
        self.skip_action.setDisabled(True)
        self._stageSelectionScreen()
        self.return_entry = '0'
        self.visual_kbd = VisualStenoKeyboard(self._console, self)
        self.stats_dock.deleteLater()
        self.splitter.addWidget(self.visual_kbd)
        self.stage = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tallySeconds)
        self.seconds = 0

    def maybeSave(self):
        pass

    def showEvent(self, e):
        super().showEvent(e)
        self._console.returnPressed.connect(self._handleEntry)
        self._console.textChanged.connect(self._handleHighlighting)

    def hideEvent(self, e):
        super().hideEvent(e)
        self._console.returnPressed.disconnect(self._handleEntry)
        self._console.textChanged.disconnect(self._handleHighlighting)

    def _tallySeconds(self):
        self.seconds += 1

    def _startTimer(self):
        self.seconds = 0
        self.timer.start(1000)

    def _stopTimer(self):
        self.timer.stop()

    def _start(self):
        self._startTimer()
        self.visual_kbd.should_enter_key_on_click = True

    def _stop(self):
        self._stopTimer()
        self.visual_kbd.should_enter_key_on_click = False

    def _stageSelectionScreen(self, ended=False):
        self.state = State.stage_selection

        lines = []
        lines.append("<h1>Learn Stenography</h1>")
        if ended:
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
        self.stage = stage
        html = f"<hr/><p><i>Enter {self.return_entry} to back out to\
 stage selection.</i></p>"
        self.setBook(StenoBook(
            html, stage.get('letters'), f': {stage["name"]}'))
        self.state = State.in_progress
        self._start()

    def _handleEntry(self):
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
        if self.state != State.in_progress:
            return
        end_correctness_index = 0
        if self.cursor_pos < len(self.current_line):
            a = self.current_line[self.cursor_pos]
            increment = 2
            if a == '-' and self.cursor_pos + 1 < len(self.current_line):
                a += self.current_line[self.cursor_pos + 1]
                increment = 3
            if len(text) == 1 and a in keyboard:
                # Match
                for c in keyboard[a]:
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
        self.updateCursorPosition()
        self.updateHighlightCursor()
        self.updateModeline()

    def _handleMistakes(self, v, text, end_correctness_index):
        # The way this works is if there’s any previous wrong_text it gets
        #  entirely removed, then readded as necessary.
        if self.wrong_start is not None:
            self._removeWrongText(v, self.wrong_start, self.wrong_end)
        else:
            self.wrong_start = v.cursor_pos + end_correctness_index

        self.wrong_text = text[end_correctness_index:]

        # Show steno chars in wrong text
        self.wrong_text = self.wrong_text.translate(trans)

        # If not (or no longer) wrong, reset wrong-tracking variables and
        #  silently follow the cursor pos.
        if not self.wrong_text:
            self.wrong = False
            self.wrong_start = None
            self.wrong_end = None
            v.mistake_cursor.setPosition(v.cursor_pos)
            return

        self.wrong = True
        v.mistake_cursor.setPosition(self.wrong_start)
        self._insertWrongText(v, v.mistake_cursor.position(), self.wrong_text)
        self.wrong_end = self.wrong_start + len(self.wrong_text)

    def _insertWrongText(self, v, pre_pos, text):
        v.mistake_cursor.setPosition(pre_pos, v.mistake_cursor.MoveAnchor)
        v.mistake_cursor.insertText(text, v.mistake_format)

    def _removeWrongText(self, v, start, end):
        v.mistake_cursor.setPosition(start, v.mistake_cursor.MoveAnchor)
        v.mistake_cursor.setPosition(end, v.mistake_cursor.KeepAnchor)
        v.mistake_cursor.removeSelectedText()
