import logging

from typing import TYPE_CHECKING

from retype.extras.space import nrspacerstrip, endsinn

logger = logging.getLogger(__name__)


def compareStrings(str1, str2):
    # type: (str | UserString, str | UserString) -> int
    """Compare strings `str1' and `str2', returning index at which they stop
 matching"""
    length_of_shorter_str = min([len(str1), len(str2)])
    for i, a, b in zip(range(length_of_shorter_str), str1, str2):
        if a != b:
            # Found character that doesn’t match; return index at which the
            #  strings stopped matching
            return i
    # Full match up to end of shorter string
    return length_of_shorter_str


class HighlightingService(object):
    def __init__(self, console, book_view, auto_newline=True):
        # type: (HighlightingService, Console, BookView, bool) -> None
        self._console = console
        self.book_view = book_view
        self._console.textChanged.connect(self._handleHighlighting)
        self.setAutoNewline(auto_newline)
        self.wrong = False
        self.wrong_start = None  # type: int | None
        self.wrong_end = None  # type: int | None
        self.wrong_text = ""

    def valid(self, v):
        # type: (HighlightingService, BookView) -> bool
        if not v.isVisible() or v.progress == 100:
            return False
        # In case there is no book loaded / variables not been initialised
        if any([getattr(
                v, 'persistent_pos', False) is False,  # type: ignore[misc]
                v.persistent_pos is None]):
            return False
        return True

    def _handleHighlighting(self, text):
        # type: (HighlightingService, str) -> None
        v = self.book_view

        if not self.valid(v):
            return
        if v.persistent_pos is None:
            return

        # Cursor position in the line
        end_correctness_index = compareStrings(text, v.current_line)
        v.cursor_pos = v.persistent_pos + end_correctness_index

        self._handleMistakes(v, text, end_correctness_index)

        self.updateHighlighting()

        self._maybeAdvance(v, text, not self.auto_newline)

    def _maybeAdvance(self, v, text, require_enter=False):
        # type: (HighlightingService, BookView, str, bool) -> None
        # Next line / chapter, skipping trailing spaces if present
        if text == v.current_line or text == nrspacerstrip(v.current_line):
            if require_enter and endsinn(v.current_line):
                return
            self.advanceLine()

    def _handleMistakes(self, v, text, end_correctness_index):
        # type: (HighlightingService, BookView, str, int) -> None
        if v.cursor_pos is None or v.persistent_pos is None:
            logger.error('_handleMistakes: Unexpected None. cursor_pos: '
                         f'{v.cursor_pos}, persistent_pos: {v.persistent_pos}')
            return
        # The way this works is if there’s any previous wrong_text it gets
        #  entirely removed, then readded as necessary.
        if self.wrong_start is not None and self.wrong_end is not None:
            self._removeWrongText(v, self.wrong_start, self.wrong_end)
        else:
            self.wrong_start = v.persistent_pos + end_correctness_index

        self.wrong_text = text[end_correctness_index:]

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
        # type: (HighlightingService, BookView, int, str) -> None
        v.mistake_cursor.setPosition(pre_pos, v.mistake_cursor.MoveAnchor)
        v.mistake_cursor.insertText(text, v.mistake_format)

    def _removeWrongText(self, v, start, end):
        # type: (HighlightingService, BookView, int, int) -> None
        v.mistake_cursor.setPosition(start, v.mistake_cursor.MoveAnchor)
        v.mistake_cursor.setPosition(end, v.mistake_cursor.KeepAnchor)
        v.mistake_cursor.removeSelectedText()

    def advanceLine(self):
        # type: (HighlightingService) -> None
        v = self.book_view

        if v.cursor_pos is None or v.persistent_pos is None or \
           v.line_pos is None:
            logger.error('_advanceLine: Unexpected None. cursor_pos: '
                         f'{v.cursor_pos}, persistent_pos: {v.persistent_pos},'
                         f' line_pos: {v.line_pos}')
            return

        # Get out of here if there is no line to advance to
        if v.onLastChapter():
            if len(v.tobetyped_list)-1 == v.line_pos:
                v.markComplete()
                return logger.debug("On last line, marking complete")
            elif len(v.tobetyped_list)-1 < v.line_pos:
                return logger.error("line_pos ({}) larger than the list ({})\
 for some reason  ".format(len(v.tobetyped_list), v.line_pos))

        v.line_pos += 1

        # Compensate
        len_typed = v.cursor_pos - v.persistent_pos
        difference = len(v.current_line) - len_typed
        v.cursor_pos += difference

        v.persistent_pos = v.cursor_pos

        # Reached last line of this chapter, move to next one
        if len(v.tobetyped_list) == v.line_pos:
            v.nextChapter(True)

        # Set the line that needs to be typed next
        try:
            v._setLine(v.line_pos)
        except Exception as e:
            logger.error('can’t advance line {}/{}\n\
error: {}'.format(v.line_pos, len(v.tobetyped_list), e))
            return

        self.updateHighlighting()
        self._console.clear()
        v.display.centreAroundCursor()
        v.updateProgress()

    def setAutoNewline(self, auto_newline):
        # type: (HighlightingService, bool) -> None
        self.auto_newline = auto_newline
        if auto_newline:
            try:
                self._console.submitted.disconnect(self.handleSubmit)
            except TypeError:
                # Occurs when not previously connected
                pass
        else:
            self._console.submitted.connect(self.handleSubmit)

    def handleSubmit(self, text):
        # type: (HighlightingService, str) -> None
        v = self.book_view

        if not self.valid(v):
            return

        self._maybeAdvance(v, text)

    def updateHighlighting(self):
        # type: (HighlightingService) -> None
        v = self.book_view
        v.updateCursorPosition()

        if self.wrong:
            v.mistake_cursor.mergeCharFormat(v.mistake_format)
            return

        v.updateModeline()


if TYPE_CHECKING:
    from retype.console import Console  # noqa: F401
    from retype.ui import BookView  # noqa: F401
    from collections import UserString  # noqa: F401
