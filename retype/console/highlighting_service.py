import logging

logger = logging.getLogger(__name__)


def compareStrings(str1, str2):
    """Compare strings `str1' and `str2', returning index at which they stop
 matching"""
    length_of_shorter_str = len(min([str1, str2]))
    for i, a, b in zip(range(length_of_shorter_str), str1, str2):
        if a != b:
            # Found character that doesn’t match; return index at which the
            #  strings stopped matching
            return i
    # Full match up to end of shorter string
    return length_of_shorter_str


class HighlightingService(object):
    def __init__(self, console, book_view):
        self._console = console
        self.book_view = book_view
        self._console.textChanged.connect(self._handleHighlighting)

    def _handleHighlighting(self, text):
        v = self.book_view

        if v.isVisible():
            # Remove highlighting if things were deleted
            if len(text) + v.persistent_pos < v.cursor_pos:
                v.cursor.mergeCharFormat(v.unhighlight_format)

            # Cursor position in the line
            v.cursor_pos = v.persistent_pos + \
                compareStrings(text, v.current_line)
            self.updateHighlighting()

            # Next line / chapter
            if text == v.current_line:
                self.advanceLine()
                # Skip empty lines
                while v.current_line.isspace() or v.current_line == '':
                    try:
                        self.advanceLine()
                    except e as e:
                        logger.error('empty lines loop exit', e)
                        return

    def advanceLine(self):  # this is a bad way of doing this
        v = self.book_view
        v.line_pos += 1

        # compensate
        if v.cursor_pos - v.persistent_pos == len(v.current_line):
            v.cursor_pos += 1
        else:
            v.cursor_pos += len(v.current_line) + 1
        v.persistent_pos = v.cursor_pos

        if len(v.to_be_typed_list) == v.line_pos:
            v.nextChapter()
        try:
            v.setLine(v.line_pos)
        except e as e:
            logger.error('can’t advance line \
            {}/{}'.format(v.line_pos, len(v.to_be_typed_list)),
                         exc_info=True)
            return
        self.updateHighlighting()
        self._console.clear()

    def updateHighlighting(self):
        v = self.book_view
        v.cursor.setPosition(v.cursor_pos, v.cursor.KeepAnchor)
        v.cursor.mergeCharFormat(v.unhighlight_format)
        v.cursor.mergeCharFormat(v.highlight_format)
        v.updateModeline()
