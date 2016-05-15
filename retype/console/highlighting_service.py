import logging
from ui.book_view import BookView

logger = logging.getLogger(__name__)


class HighlightingService(object):
    def __init__(self, console, window):
        self._console = console
        self._window = window
        self._console.textChanged.connect(self._handleHighlighting)

    def _handleHighlighting(self, text):
        v = self._window.currentView()

        if type(v) is BookView:
            try:  # exit if highlighting variables have not been initialised
                v.cursor_pos += 0
            except AttributeError:
                return
            for index, c in enumerate(text):
                if index + v.persistent_pos == v.cursor_pos:
                    try:
                        if text[index] == v.current_sentence[index]:
                            v.cursor_pos += 1
                            self.updateHighlighting()
                    except IndexError:
                        print("debug: indexError")

            # remove highlighting
            if len(text) + v.persistent_pos < v.cursor_pos:
                v.cursor.mergeCharFormat(v.unhighlight_format)
                v.cursor_pos = v.persistent_pos + len(text)
                self.updateHighlighting()

            # next line / chapter
            if text == v.current_sentence:
                self.advanceLine()
                # skip empty lines
                while v.current_sentence.isspace() or \
                      v.current_sentence == '':
                    try:
                        self.advanceLine()
                    except:
                        logger.error('empty lines loop exit')
                        return  #

    def advanceLine(self):  # this is a bad way of doing this
        v = self._window.currentView()
        v.line_pos += 1

        # compensate
        if v.cursor_pos - v.persistent_pos == len(v.current_sentence):
            v.cursor_pos += 1
        else:
            v.cursor_pos += len(v.current_sentence) + 1
        v.persistent_pos = v.cursor_pos

        if len(v.to_be_typed_list) == v.line_pos:
                    v.nextChapter()
        try:
            v.setSentence(v.line_pos)
        except:
            logger.error('can’t advance line \
            {}/{}'.format(v.line_pos, len(v.to_be_typed_list)),
                         exc_info=True)
            return
        self.updateHighlighting()
        self._console.clear()

    def updateHighlighting(self):
        v = self._window.currentView()
        v.cursor.setPosition(v.cursor_pos, v.cursor.KeepAnchor)
        v.cursor.mergeCharFormat(v.highlight_format)
