import logging

logger = logging.getLogger(__name__)


commands_info = {
    'switch':
    {
        'desc': 'Switch view between Shelf View and Book View',
        'aliases': ['switch', 'view'],
        'args': None,
        # 'func': self.switch
    },
    'load':
    {
        'desc': 'Load book with a given numerical ID. 0 if none passed',
        'aliases': ['load', 'book'],
        'args': 'ID',
        # 'func': self.load
    },
    'gotoCursorPosition':
    {
        'desc': 'Go to cursor position. If followed by \'m\' or \'move\', move\
 cursor to your current position',
        'aliases': ['cursor'],
        'args': '[m / move ?]',
        # 'func': self.gotoCursorPosition
    },
    'advanceLine':
    {
        'desc': 'Skip line',
        'aliases': ['line', 'advanceline', 'skipline', 'l'],
        'args': None,
        # 'func': self.advanceLine
    },
    'setChapter':
    {
        'desc': 'Set chapter to the chapter of the given numerical POS.\
 Ignored if none passed. If followed by \'m\' or \'move\', move the cursor too',
        'aliases': ['setchapter', 'chapter'],
        'args': 'POS [m / move ?]',
        # 'func': self.setChapter
    },
    'typespeed':
    {
        'desc': 'Launch Typespeed game',
        'aliases': ['typespeed'],
        'args': None
    },
    'steno':
    {
        'desc': 'Launch Learn Stenography game',
        'aliases': ['steno', 'stenography'],
        'args': None
    },
    'customise':
    {
        'desc': 'Open customisation dialog',
        'aliases': ['config', 'customise', 'customisation'],
        'args': None,
        # 'func': self.customise
    },
    'help_':
    {
        'desc': 'Show dialog with available console commands',
        'aliases': ['?', 'help'],
        'args': None,
        # 'func': self.help_
    }
}


class CommandService(object):
    def __init__(self, console, book_view, switchView, loadBook, prompt,
                 customise, about):
        self._console = console
        self.book_view = book_view
        self.switchView = switchView
        self.loadBook = loadBook
        self.prompt = prompt
        self._console.submitted.connect(self._handleCommands)
        self.customise_signal = customise
        self.about_signal = about
        self._initCommands()
        self._initCommandHistory()

    def _initCommands(self):
        self.commands_info = commands_info

        for f in self.commands_info.keys():
            self.commands_info[f]['func'] = getattr(self, f)

        self.commands = {}
        for cmd in self.commands_info.values():
            for alias in cmd['aliases']:
                self.commands[alias] = cmd['func']

    def _handleCommands(self, text):
        e = text[len(self.prompt):].lower()
        el = e.split(' ')  #
        if text.startswith(self.prompt) and el[0] in self.commands:
            if len(el) == 1:
                self.commands[el[0]]()
            else:
                try:
                    logger.debug('Command arguments: {}'.format(el[1:]))
                    self.commands[el[0]](*el[1:])
                except TypeError:
                    logger.error('Invalid arguments')

            # Insert into history
            try:
                # If already in history, pop and reappend (moves it to end)
                i = self.command_history.index(text)
                self.command_history.append(self.command_history.pop(i))
            except ValueError:
                # Otherwise, simply append
                self.command_history.append(text)

            self.command_history_pos = None
            self._console.clear()

    def _initCommandHistory(self):
        self.command_history = []
        self.command_history_pos = None

    def commandHistoryUp(self):
        if not self.command_history:
            return
        if not self.command_history_pos:
            self._current_input = self._console.text()
            self.command_history_pos = -1
        else:
            if len(self.command_history) <= abs(self.command_history_pos):
                return
            self.command_history_pos -= 1
        self._console.setText(self.command_history[self.command_history_pos])
        logger.debug("command_history_pos: %s, command_history: %s" %
                     (self.command_history_pos, self.command_history))

    def commandHistoryDown(self):
        if not self.command_history_pos:
            return
        if self.command_history_pos == -1:
            self._console.setText(self._current_input)
            self.command_history_pos = None
            return
        else:
            self.command_history_pos += 1
        self._console.setText(self.command_history[self.command_history_pos])
        logger.debug("command_history_pos: %s, command_history: %s" %
                     (self.command_history_pos, self.command_history))

    def onBookView(self):
        return self.book_view.isVisible()

    def switch(self, view_name=None):
        v = 0
        if view_name in ['shelf', 'shelves', 'main']:
            v = 1
        elif view_name == 'book':
            v = 2
        elif view_name is not None:
            return logger.error("Unrecognised view name '{}'"
                                .format(view_name))
        self.switchView.emit(v)

    def customise(self):
        self.customise_signal.emit()

    def load(self, book_id=0):
        try:
            self.loadBook.emit(int(book_id))
        except ValueError:
            logger.error('{} is not a valid book_id'.format(book_id))

    def setChapter(self, pos=None, move=None):
        if pos is None:
            return
        if self.onBookView():
            m = True if move in ['move', 'm'] else False
            try:
                p = int(pos)
                self.book_view.setChapter(p, m)
            except (TypeError, ValueError):
                if pos in ['next', 'n']:
                    self.book_view.nextChapter(m)
                elif pos in ['previous', 'prev', 'p']:
                    self.book_view.previousChapter(m)

    def advanceLine(self):
        self._console.highlighting_service.advanceLine()

    def gotoCursorPosition(self, move=None):
        if self.onBookView():
            m = True if move == 'move' else False
            self.book_view.gotoCursorPosition(m)

    def help_(self):
        self.about_signal.emit('Console commands')

    def typespeed(self):
        self.switchView.emit(3)

    def steno(self):
        self.switchView.emit(4)
