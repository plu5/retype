from ui.book_view import BookView

class HighlightingService(object):
    def __init__(self, console, window):
        self._console = console
        self._window = window
        self._console.textChanged.connect(self._handleHighlighting)

    def _handleHighlighting(self, text):
        v = self._window.currentView()
        try:  # exit if highlighting variables have not been initialised
            v.cursor_pos += 0
        except AttributeError:
            return
        if type(v) is BookView:
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

            # next line
            if text == v.current_sentence:
                self.advanceLine()
                # skip empty lines
                while v.current_sentence.isspace() or v.current_sentence == '':
                    self.advanceLine()

    def advanceLine(self):  # this is a bad way of doing this
        v = self._window.currentView()
        v.line_pos += 1
        if v.cursor_pos - v.persistent_pos == len(v.current_sentence):
            v.cursor_pos += 1
        else:
            v.cursor_pos += len(v.current_sentence) + 1
        v.persistent_pos = v.cursor_pos
        v.setSentence(v.line_pos)
        self.updateHighlighting()
        self._console.clear()

    def updateHighlighting(self):
        v = self._window.currentView()
        v.cursor.setPosition(v.cursor_pos, v.cursor.KeepAnchor)
        v.cursor.mergeCharFormat(v.highlight_format)
