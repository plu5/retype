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
        
    def _handleCommands(self, text):
        e = text[len(self.prompt):].lower()
        if text.startswith(self.prompt) and e in self.commands:
            self.commands[e]()
            self._console.clear()

    def _handleHighlighting(self, text):
        pass

    def switchMain(self):
        self._window.switchViewSignal.emit(1)

    def switchBook(self):
        self._window.switchViewSignal.emit(2)

    def loadBook(self):
        self._console.loadBookSignal.emit()
