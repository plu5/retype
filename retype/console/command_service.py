class CommandService(object):
    def __init__(self, console, window):
        self._console = console
        self._window = window
        self._console.onReturnSignal.connect(self._handleCommands)
        self.prompt = '>'
        self._initCommands()

    def _initCommands(self):
        self.commands = {}
        self.commands['switchmain'] = self.switchMain
        self.commands['switchbook'] = self.switchBook
        self.commands['loadbook'] = self.loadBook
        
    def _handleCommands(self, text):
        e = text[len(self.prompt):].lower()
        el = e.split(' ')  #
        if text.startswith(self.prompt) and el[0] in self.commands:
            if len(el) == 1:
                self.commands[el[0]]()
            else:
                try:
                    print(el[1:])  # should log this info
                    self.commands[el[0]](*el[1:])
                except TypeError:
                    print("debug: invalid arguments")  # log this in future
            self._console.clear()

    def switchMain(self):
        self._window.switchViewSignal.emit(1)

    def switchBook(self):
        self._window.switchViewSignal.emit(2)

    def loadBook(self, book_id=0):
        self._console.loadBookSignal.emit(int(book_id))
