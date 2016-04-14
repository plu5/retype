from PyQt5.QtCore import pyqtSignal


class ConsoleService(object):
    def __init__(self, console, window):
        self._console = console
        self._window = window
        #self._entry = console.text()
        self._console.onReturnSignal.connect(self._handleCommands)
        self._console.textChanged.connect(self._handleHighlighting)
        self.prompt = '>'  # eh
        self._initCommands()

    def _initCommands(self):
        self.commands = {}
        self.commands['switchmain'] = self.switchMain
        self.commands['switchbook'] = self.switchBook
        #self._window.switchViewSignal.emit
        # they could be more complicated and then it won’t work
        # i really wish commands could have hyphens in them
        
    def _handleCommands(self, text):
        # e = self._entry.lower() #
        # # if e[1:] == 'switch-main':
        # #     self.switchViewSignal.emit(1)
        # if e == 'print':
        #     print('hello')
        #e = text.lower()
        e = text[len(self.prompt):].lower()
        if text.startswith(self.prompt) and e in self.commands:
            # #e = text[1:].lower()
            # if e == 'switch-main':
            #     self._window.switchViewSignal.emit(1)
            # if e == 'switch-book':
            #     #self._window.switchViewSignal.emit(2)
            #     self.commands[e](2)
            #     print(self.commands[e])
            self.commands[e]()
            self._console.clear()
            # how to only clear the console when a command exists?
            # also should these be connected to actual commands by thesamename?

    def _handleHighlighting(self, text):
        pass

    def switchMain(self):
        self._window.switchViewSignal.emit(1)

    def switchBook(self):
        self._window.switchViewSignal.emit(2)
