import os
import random
import logging
from enum import Enum
from qt import QWidget, QSize, QPainter, QTimer, QFontMetrics, Qt, pyqtSignal

from typing import TYPE_CHECKING

from retype.ui import BookView
from retype.ui.painting import textPixmap
from retype.services.theme import theme, C, Theme
from retype.resource_handler import getTypespeedWordsPath


logger = logging.getLogger(__name__)

ranks = ["None", "Beginner", "Learner", "NoGood", "Average",
         "Good", "VeryGood", "Pro", "3l33t", "*(GOD)*", "Computer"]
typoranks = ["None", "Alien", "Secretary", "Human", "IT Person", "Handicap",
             "Monkey", "Pencil", "T-Bone", "E-Typo", "TypOmatiC", "TypoKing"]

selectors = {"u0": "Games.Typespeed.WordUrgency.low",
             "u1": "Games.Typespeed.WordUrgency.mid",
             "u2": "Games.Typespeed.WordUrgency.high",
             "r0": "Games.Typespeed.Rank.low",
             "r1": "Games.Typespeed.Rank.midlow",
             "r2": "Games.Typespeed.Rank.midhigh",
             "r3": "Games.Typespeed.Rank.high",
             "main": "Games.Typespeed"}


class Rules():
    misses = 10    # number of misses before game over
    minlen = 1
    maxlen = 19
    minwords = 1
    maxwords = 22
    minspeed = 3
    maxspeed = 0
    step = 175     # speed step


class State(Enum):
    stage_selection = 1
    in_progress = 2


class TypespeedBook:
    def __init__(self, html='', titleext=''):
        # type: (TypespeedBook, str, str) -> None
        self.path = ''
        self.title = 'Typespeed' + titleext
        self.progress = 0.0
        s = html
        self.chapters = [{'len': len(s), 'html': s, 'plain': s, 'images': []}
                         ]  # type: list[Chapter]
        self.chapter_lookup = {}  # type: dict[str, int]
        self.dirty = False

    def updateProgress(self, *args):
        # type: (TypespeedBook, object) -> None
        pass


class WordUrgency(Enum):
    low = 0
    mid = 1
    high = 2


@theme(selectors['u0'], C(fg='green'))
@theme(selectors['u1'], C(fg='#b37100'))
@theme(selectors['u2'], C(fg='red'))
@theme(selectors['r0'], C(fg='blue'))
@theme(selectors['r1'], C(fg='green'))
@theme(selectors['r2'], C(fg='#b37100'))
@theme(selectors['r3'], C(fg='red'))
@theme(selectors['main'], C(fg='#02759f', bg='#F6F1DE'))
class TypespeedGame(QWidget):
    scoreChanged = pyqtSignal()

    def __init__(self, display, console, parent):
        # type: (TypespeedGame, BookDisplay, Console, QWidget | None) -> None
        super().__init__(parent)
        (self.c_u0, self.c_u1, self.c_u2, self.c_r0, self.c_r1, self.c_r2,
         self.c_r3, self.c) = self._loadTheme()
        self.display = display
        self._font = display._font
        self._console = console
        console.subscribe(console.Ev.keypress, self._handleKeyPress)
        display.fontChanged.connect(self._setSizeDependentStuff)

        # x ratio enables us to have the display drawn at whatever size is
        #  convenient while still keeping the same rate of movement of words
        #  as the original typespeed, which was hardcoded to be drawn to
        #  80 character widths.
        self.x_ratio = 1/80
        self.num_slots = Rules.maxwords
        self.cx_start = -2
        self.cx_increment = 1

        # The original typespeed has extra delay due to waiting for getch. Not
        #  having it makes the game loop a bit faster and thus more difficult.
        #  You would be surprised at the difference 5 hundredths of a second
        #  can make.
        self.extra_delay = 5

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._gameLoop)

        self._resetVariables()

    def _loadTheme(self):
        # type: (TypespeedGame) -> tuple[C, ...]
        return tuple(Theme.get(c) for c in selectors.values())

    def _resetVariables(self):
        # type: (TypespeedGame) -> None
        self.initial = True
        self.started = self.paused = False
        self.over = False
        self.hundredth_seconds = self.prev_hundredth_seconds = 0
        self.rate = 1.0
        self.wordswritten = 0
        self.misses = 0
        self.presses = 0
        self.score = 0
        self.rank = ranks[0]
        self.typorank = typoranks[0]
        self.cps = 0.00
        self.wpm = 0
        self._clearSlots()

    def _clearSlots(self):
        # type: (TypespeedGame) -> None
        self.word_slots = []  # type: list[Slot]
        for i in range(self.num_slots):
            self.word_slots.append(
                {'free': True, 'text': '', 'cx': self.cx_start,
                 'x': 0, 'y': 0,
                 'urgency': WordUrgency.low})

    def _clearSlot(self, slot):
        # type: (TypespeedGame, Slot) -> None
        slot['text'] = ''
        slot['cx'] = self.cx_start
        slot['x'] = int(self.cx_start * self.x_increment)
        slot['free'] = True
        slot['urgency'] = WordUrgency.low
        self.update()

    def _setSizeDependentStuff(self, font=False):
        # type: (TypespeedGame, bool) -> None
        """Set positions and font size based on widget size.
This game is designed to adapt to the width and height it has available, while
 still behaving the same as the original typespeed, which had a constant width
 and height.
Font adjustment: In order to stay consistent with typespeed, we need to have 22
 vertical slots for words which may or may not fit on the amount of space we
 have, so I thought the easiest thing is to calculate the font size based on
 the height.
"""
        self.w = self.width()
        self.h = self.height()
        self.x_increment = self.cx_increment * (self.w * self.x_ratio)
        self.hper = int(self.h / self.num_slots)
        if font:
            self._font.setPixelSize(self.hper)
        self.fm = QFontMetrics(self._font)
        self.edge = 79 * self.x_increment - (
            4 * self.x_increment - 4 * self.fm.averageCharWidth())
        y = 0
        for s in self.word_slots:
            s['x'] = int(s['cx'] * self.x_increment)
            s['y'] = y
            y += self.hper

    def _isFontBad(self):
        # type: (TypespeedGame) -> bool
        h = self.height()
        fm = QFontMetrics(self.display._font)
        return fm.height() * self.num_slots > h

    def resizeEvent(self, e):
        # type: (TypespeedGame, QResizeEvent) -> None
        super().resizeEvent(e)
        if self.initial:
            self.initial = False
            return
        self._setSizeDependentStuff(True)

    def wheelEvent(self, e):
        # type: (TypespeedGame, QWheelEvent) -> None
        super().wheelEvent(e)
        self.display.wheelEvent(e)

    def showEvent(self, e):
        # type: (TypespeedGame, QShowEvent) -> None
        super().showEvent(e)
        self._setSizeDependentStuff(self._isFontBad())
        self._console.textChanged.connect(self._handleTextChanged)
        if self.paused:
            self.resume()

    def hideEvent(self, e):
        # type: (TypespeedGame, QHideEvent) -> None
        super().hideEvent(e)
        self._console.textChanged.disconnect(self._handleTextChanged)
        if self.started:
            self.pause()

    def start(self, words):
        # type: (TypespeedGame, list[str]) -> None
        self._resetVariables()
        self.words = words
        self.resume()

    def stop(self):
        # type: (TypespeedGame) -> None
        self.timer.stop()
        self.started = False

    def resume(self):
        # type: (TypespeedGame) -> None
        self.timer.start(10)  # every 100th of a second
        self.started = True
        self.paused = False

    def pause(self):
        # type: (TypespeedGame) -> None
        self.stop()
        self.paused = True

    def _gameLoop(self):
        # type: (TypespeedGame) -> None
        self.hundredth_seconds += 1
        if self.hundredth_seconds >= (self.prev_hundredth_seconds +
                                      (100.0 / self.rate) + self.extra_delay):
            self.prev_hundredth_seconds = self.hundredth_seconds
            self._moveWords()
            self._adjustRateAndMaybeAddWord()
            self.cps = ((self.score + self.wordswritten) * 100.0 /
                        self.hundredth_seconds)
            self.wpm = int(self.cps * 12)
            self.update()
        if self.misses >= Rules.misses:
            self._gameOver()

    def _countPartial(self):
        # type: (TypespeedGame) -> None
        text = self._console.text()
        length = len(text)
        for s in self.word_slots:
            word = s['text']
            if length < len(word):
                if text[0:length] == word[0:length]:
                    self.score += length
                    self._scoreChange()

    def _addNewWord(self):
        # type: (TypespeedGame) -> bool
        """Insert a random new word on the screen that does not already exist.
Returns True on success or False on failure.
Can result in a very long loop when there are many words on field and only a
few words in word list (no duplicates allowed)."""
        # random free slot
        free_slots = []
        existing_words = []
        for i in range(len(self.word_slots)):
            if self.word_slots[i]['free'] is True:
                free_slots.append(i)
            else:
                existing_words.append(self.word_slots[i]['text'])
        if not len(free_slots):
            return False
        slot = random.choice(free_slots)
        # random word that is not a duplicate
        word = random.choice(self.words)
        while word in existing_words:
            word = random.choice(self.words)
        self.word_slots[slot]['text'] = word
        self.word_slots[slot]['free'] = False
        self.word_slots[slot]['x'] = int(self.cx_start * self.x_increment)
        return True

    def _moveWords(self):
        # type: (TypespeedGame) -> None
        """Move words across the screen, removing them if they reach the right
 side."""
        for s in self.word_slots:
            if s['free'] is False:
                s['cx'] += self.cx_increment
                s['x'] = int(s['cx'] * self.x_increment)

                x = s['x']
                length = len(s['text'])
                if x > (79 - length) * self.x_increment:
                    self.misses += 1
                    self._clearSlot(s)
                    continue
                elif x > (65 - length) * self.x_increment:
                    s['urgency'] = WordUrgency.high
                elif x > (50 - length) * self.x_increment:
                    s['urgency'] = WordUrgency.mid
                else:
                    s['urgency'] = WordUrgency.low

        # If user was typing a word then exceeded number of misses before
        #  game over, typespeed counts the characters typed if correct so
        #  far in order to avoid that contributing to typo ratio.
        if self.misses >= Rules.misses:
            self._countPartial()

        self._scoreChange()

    def _adjustRateAndMaybeAddWord(self):
        # type: (TypespeedGame) -> None
        """Set rate according to current length of all visible words.
If words with too few chars are on screen, throw in another word."""
        wc = length = 0
        for s in self.word_slots:
            if s['free'] is False:
                wc += 1
                length += len(s['text']) + 1

        if (length < self.score / 4 + 1 or wc < Rules.minwords):
            self._addNewWord()

        self.rate = self.score / Rules.step + Rules.minspeed
        if Rules.maxspeed and self.rate > Rules.maxspeed:
            self.rate = Rules.maxspeed

    def _updateRank(self):
        # type: (TypespeedGame) -> None
        rank = 0
        if self.score > 0:
            rank = min(int(self.score / 100 + 1), 10)
        self.rank = ranks[rank]

    def _scoreChange(self):
        # type: (TypespeedGame) -> None
        self._updateRank()
        self.scoreChanged.emit()

    def _enterAttempt(self, text):
        # type: (TypespeedGame, str) -> None
        found_word = False
        length = len(text)
        if not length:
            return
        for s in self.word_slots:
            if text != s['text']:
                continue
            found_word = True
            self.wordswritten += 1
            self.score += length
            self._clearSlot(s)
            self._scoreChange()
        if not found_word:
            # I don't know why this gets incremented here
            self.presses += 1

    def _getTyporank(self, ratio):
        # type: (TypespeedGame, float) -> str
        typorank = 0
        r = {2: 2, 3: 4, 4: 6, 5: 8, 6: 11, 7: 15, 8: 20, 9: 30, 10: 50}

        if ratio < 0:
            typorank = 0
        elif ratio == 0:
            typorank = 1
        else:
            for rank, value in r.items():
                if ratio < value:
                    typorank = rank
                    break
            if typorank == 0:  # if none of the conditions so far passed
                typorank = 11

        return typoranks[typorank]

    def _gameOver(self):
        # type: (TypespeedGame) -> None
        self.timer.stop()
        self.typo_ratio = 0.0
        if self.presses:
            self.typo_ratio = (1 - (self.score + self.wordswritten) /
                               (self.presses + self.wordswritten)) * 100
            self.typorank = self._getTyporank(self.typo_ratio)
        else:
            self.typorank = typoranks[0]

        self.game_over_lines = {
            "GAME OVER!": "",
            "You achieved:": "",
            "Rank:": f"{self.rank}",
            "Score:": f"{self.score}",
            "WPM:": f"{self.wpm:.0f}",
            "CPS:": f"{self.cps:.3f}",
            "Typo ratio:": f"{self.typo_ratio:.1f}%",
            "Typorank:": f"{self.typorank}"
        }
        self.over = True
        self._console.clear()

    def _handleKeyPress(self, e):
        # type: (TypespeedGame, QKeyEvent) -> None
        if not self.started or self.isHidden():
            return
        if e.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space]:
            self._enterAttempt(self._console.text().rstrip())
            self._console.clear()
        elif len(e.text()) and e.text().isprintable():
            self.presses += 1

    def _handleTextChanged(self, text):
        # type: (TypespeedGame, str) -> None
        if not self.started:
            return
        if text == " ":
            self._console.setText("")

    def sizeHint(self):
        # type: (TypespeedGame) -> QSize
        return QSize(100, 100)

    def minimumSizeHint(self):
        # type: (TypespeedGame) -> QSize
        return self.sizeHint()

    def _cRank(self):
        # type: (TypespeedGame) -> C
        c = self.c
        if self.score < 400:
            c = self.c_r0
        elif self.score < 600:
            c = self.c_r1
        elif self.score < 700:
            c = self.c_r2
        else:
            c = self.c_r3
        return c

    def _cTyporank(self):
        # type: (TypespeedGame) -> C
        c = self.c
        if self.typo_ratio < 6:
            c = self.c_r0
        elif self.typo_ratio < 11:
            c = self.c_r1
        elif self.typo_ratio < 20:
            c = self.c_r2
        else:
            c = self.c_r3
        return c

    def paintEvent(self, e):
        # type: (TypespeedGame, QPaintEvent) -> None
        super().paintEvent(e)
        if not self.started:
            return
        (w, h) = (self.w, self.h)
        qp = QPainter()
        qp.begin(self)
        draw = qp.drawPixmap

        font = self._font
        qp.fillRect(0, 0, w, h, self.c.bg())

        if self.over:
            x = int(self.x_increment * 20)
            y = self.hper * 3
            for a, b in self.game_over_lines.items():
                size = self.fm.size(Qt.TextFlag.TextSingleLine, a)
                if len(a):
                    draw(x, y, textPixmap(
                        a, size.width(), size.height(), font, self.c.fg()))
                if len(b):
                    x2 = int(x + self.x_increment * 20)
                    x2_min = int(x + size.width() + self.x_increment)
                    if x2 < x2_min:
                        x2 = x2_min
                    size = self.fm.size(Qt.TextFlag.TextSingleLine, b)
                    c = self.c
                    if a == 'Rank:':
                        c = self._cRank()
                    elif a == 'Typorank:':
                        c = self._cTyporank()
                    draw(x2, y, textPixmap(
                        b, size.width(), size.height(), font, c.fg()))
                else:
                    y += int(self.hper * 1.2)
                y += int(self.hper * 1.2)
            return

        highest_x = -2
        highest_x_width = 0
        highest_x_length = 0
        for s in self.word_slots:
            (x, y, word) = (s['x'], s['y'], s['text'])
            size = self.fm.size(Qt.TextFlag.TextSingleLine, word)
            if x > highest_x:
                highest_x = x
                highest_x_width = size.width()
                highest_x_length = len(word)
            u = s.get('urgency')
            cl = self.c_u2.fg() if u == WordUrgency.high else (
                self.c_u1.fg() if u == WordUrgency.mid else self.c_u0.fg())
            if s['free'] is False and x < w:
                draw(x, y, textPixmap(
                    word, size.width(), size.height(), font, cl))

        # draw edge
        x = int(self.edge)
        if highest_x > -2:
            x = self.edge = int(79 * self.x_increment - (
                highest_x_length * self.x_increment - highest_x_width))
        qp.fillRect(x, 0, 1, self.h, self.c_u2.fg())


class TypespeedView(BookView):
    def __init__(self,  # type: TypespeedView
                 main_win,  # type: MainWin
                 main_controller,  # type: MainController
                 bookview_settings,  # type: BookViewSettings
                 user_dir  # type: str
                 ):
        # type: (...) -> None
        super().__init__(main_win, main_controller,
                         bookview_settings=bookview_settings, parent=main_win)
        self._console = main_controller.console
        self.wrong_start = None
        self.skip_action.setDisabled(True)
        self.return_entry = '0'
        self.stats_dock.deleteLater()

        # modeline adjustments
        self.modeline.pos_sep.setText(" ")
        self.modeline.chap_pre.setText("")
        self.modeline.chap_sep.setText("")
        self.modeline.vchap_pre.setText("")
        self.modeline.vchap_sep.setText("")
        self.modeline.viewed_chap_pos.setText("")
        self.modeline.chap_pos.setText("Misses:")
        self.modeline.chap_total_dupe.setText("")
        self.modeline.percent.setText("")
        self.modeline.l_group.setToolTip("Score and rank achieved")
        self.modeline.p_group.setToolTip("Calculated words per minute and\
 characters per second achieved")
        self.modeline.c_group.setToolTip("Number of words that slid off the\
 screen")
        self.modeline.v_group.setToolTip("")

        self.word_lists = {}  # type: dict[str, WordListData]
        self.words = []  # type: list[str]
        self._populateWordLists(
            getTypespeedWordsPath(), getTypespeedWordsPath(user_dir))
        self.game = TypespeedGame(self.display, self._console, self)
        self.game.hide()
        self.game.scoreChanged.connect(self.updateModeline)

        self._stageSelectionScreen()

    def maybeSave(self):
        # type: (TypespeedView) -> None
        pass

    def setCursor(self):  # type: ignore[override]
        # type: (TypespeedView) -> None
        pass

    def showEvent(self, e):
        # type: (TypespeedView, QShowEvent) -> None
        super().showEvent(e)
        self._console.returnPressed.connect(self._handleEntry)

    def hideEvent(self, e):
        # type: (TypespeedView, QHideEvent) -> None
        super().hideEvent(e)
        self._console.returnPressed.disconnect(self._handleEntry)

    def _populateWordLists(self, app_path, user_path):
        # type: (TypespeedView, str, str) -> None
        self.word_lists = {}
        paths = [app_path, user_path] if app_path != user_path else [app_path]
        for path in paths:
            for root, _, files in os.walk(path):
                for f in files:
                    if f not in self.word_lists:
                        if len(f) < 6 or f[0:6] != 'words.':
                            continue
                        key = f[6:]
                        p = os.path.join(root, f)
                        word_list = {'path': p}  # type: WordListData
                        try:
                            with open(p, 'r', encoding='utf-8') as _f:
                                words = _f.read().splitlines()
                                if not len(words):
                                    logger.warning(f'Empty word list {p}')
                                    continue
                                name = words[0]
                                word_list['name'] = name
                                words = words[1:]
                                filtered_words = []
                                for word in words:
                                    if ' ' in word:
                                        continue
                                    filtered_words.append(word)
                                word_list['words'] = filtered_words
                                if key in self.word_lists and\
                                   path == user_path:
                                    key += ' (user dir)'
                                self.word_lists[key] = word_list
                        except OSError as e:
                            logger.error(f'Cannot read word list file {p}', e)
                        except UnicodeDecodeError as e:
                            logger.error(f'Cannot decode word list file {p}',
                                         e)
                break  # do not recurse
        # sort alphabetically
        self.word_lists = dict(sorted(self.word_lists.items()))

    def _stageSelectionScreen(self, ended=False):
        # type: (TypespeedView, bool) -> None
        self.state = State.stage_selection
        lines = []
        lines.append("<h1>Typespeed</h1>")
        lines.append("<p>This is a reproduction of the classic terminal game\
 by Jani Ollikainen, Jaakko Manelius, and Tobias Stoeckmann. Test your speed!\
</p>")
        lines.append("<p>Choose a word list (enter prefix):</p>")
        for i, word_list in self.word_lists.items():
            lines.append(f'<span><b>{i}</b>: {word_list["name"]}</span><br/>')
        self.setBook(TypespeedBook(''.join(lines)))

    def _start(self):
        # type: (TypespeedView) -> None
        self._setDisplayGeom()
        self.game.start(self.words)
        self.game.show()

    def _stop(self):
        # type: (TypespeedView) -> None
        self.game.stop()
        self.game.hide()

    def _setStage(self, word_list):
        # type: (TypespeedView, WordListData) -> None
        html = f"<p><i>Enter {self.return_entry} to back out to\
 word list selection.</i></p>"
        self.setBook(TypespeedBook(html, f': {word_list["name"]}'))
        self.state = State.in_progress
        self.words = word_list['words']
        self._start()

    def _setDisplayGeom(self):
        # type: (TypespeedView) -> None
        doc_h = int(self.display.document().size().height())
        p = self.display.parent()
        y = p.y()  # type: int  # type: ignore[attr-defined]
        self.game.setGeometry(
            self.display.x(), y + doc_h,
            self.display.width(), self.display.height() - doc_h)

    def resizeEvent(self, e):
        # type: (TypespeedView, QResizeEvent) -> None
        super().resizeEvent(e)
        self._setDisplayGeom()

    def _handleEntry(self):
        # type: (TypespeedView) -> None
        text = self._console.text()
        if self.state == State.stage_selection:
            matching = self.word_lists.get(text)
            if matching:
                self._console.clear()
                self._setStage(matching)
        elif self.state == State.in_progress:
            if text == self.return_entry:
                self._stop()
                self._console.clear()
                self._stageSelectionScreen()

    def updateModeline(self):
        # type: (TypespeedView) -> None
        if self.book is None:
            return
        self.modeline.update_(
            title=self.book.title, path="", line_pos=self.game.score,
            cursor_pos=self.game.rank,
            progress=f"WPM:{self.game.wpm:.0f} CPS:{self.game.cps:.2f}",
            chap_total=f"{self.game.misses}")
        self.modeline.chap_total_dupe.setText("")
        self.modeline.cursor_pos.setStyleSheet(
            f'color:{self.game._cRank().fg.value}')


if TYPE_CHECKING:
    from qt import (  # noqa: F401
        QShowEvent, QHideEvent, QResizeEvent, QKeyEvent, QWheelEvent,
        QPaintEvent)
    from retype.ui import MainWin  # noqa: F401
    from retype.ui.book_view import BookDisplay  # noqa: F401
    from retype.controllers import MainController  # noqa: F401
    from retype.console import Console  # noqa: F401
    from retype.extras.metatypes import BookViewSettings, Chapter  # noqa: F401
    from typing import TypedDict
    Slot = TypedDict(
        'Slot',
        {'free': bool, 'text': str, 'cx': int, 'x': int, 'y': int,
         'urgency': WordUrgency})
    WordListData = TypedDict(
        'WordListData',
        {'path': str, 'name': str, 'words': list[str]}, total=False)
