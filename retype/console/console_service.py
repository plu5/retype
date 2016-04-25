# put highlighting in a separate file
from views.book_view import BookView

class ConsoleService(object):
    def __init__(self, console, window):
        self._console = console
        self._window = window
        self._console.onReturnSignal.connect(self._handleCommands)
        self._console.textChanged.connect(self._handleHighlighting)
        self.prompt = '>'
        self._initCommands()

    def _initCommands(self):
        self.commands = {}
        self.commands['switchmain'] = self.switchMain
        self.commands['switchbook'] = self.switchBook
        self.commands['loadbook'] = self.loadBook
        self.commands['teststacker'] = self.testStacker
        
    def _handleCommands(self, text):
        e = text[len(self.prompt):].lower()
        if text.startswith(self.prompt) and e in self.commands:
            self.commands[e]()  # args
            self._console.clear()

    def _handleHighlighting(self, text):
        if type(self._window.currentView()) is BookView:
            v = self._window.currentView()
            for index, c in enumerate(text):
                if index + v.persistent_pos == v.cursor_pos:
                    try:
                        if text[index] == v.current_sentence[index]:
                            v.cursor_pos += 1
                            v.cursor.setPosition(v.cursor_pos,
                                                 v.cursor.KeepAnchor)
                            v.cursor.mergeCharFormat(v.highlight_format)
                    except IndexError:
                        print("debug: indexError")

            # remove highlighting
            if len(text) + v.persistent_pos < v.cursor_pos:
                v.cursor.mergeCharFormat(v.unhighlight_format)
                v.cursor_pos = v.persistent_pos + len(text)
                v.cursor.setPosition(v.cursor_pos, v.cursor.KeepAnchor)
                v.cursor.mergeCharFormat(v.highlight_format)

            # next line
            if text == v.current_sentence:
                self.advanceLine()
                # skip empty lines
                while v.current_sentence.isspace() or v.current_sentence == '':
                    self.advanceLine()

    def switchMain(self):
        self._window.switchViewSignal.emit(1)

    def switchBook(self):
        self._window.switchViewSignal.emit(2)

    def loadBook(self):
        self._console.loadBookSignal.emit()

    def testStacker(self):
        print(self._window.currentView())

    def advanceLine(self):  # this is a bad way of doing this
        v = self._window.currentView()
        v.line_pos += 1
        if v.cursor_pos - v.persistent_pos == len(v.current_sentence):
            v.cursor_pos += 1
        else:
            v.cursor_pos += len(v.current_sentence) + 1
        v.persistent_pos = v.cursor_pos
        v.setSentence(v.line_pos)
        v.cursor.setPosition(v.cursor_pos, v.cursor.KeepAnchor)
        v.cursor.mergeCharFormat(v.highlight_format)
        self._console.clear()
