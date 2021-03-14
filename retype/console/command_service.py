import logging

logger = logging.getLogger(__name__)


class CommandService(object):
    def __init__(self, console, book_view, switchView, loadBook):
        self._console = console
        self.book_view = book_view
        self.switchView = switchView
        self.loadBook = loadBook
        self._console.submitted.connect(self._handleCommands)
        self.prompt = '>'
        self._initCommands()
        self._initCommandHistory()

    def _initCommands(self):
        self.commands = {}

        def add(commands_list, func):
            for command in commands_list:
                self.commands[command] = func

        add(['switch', 'view'], self.switch)
        add(['load', 'book'], self.load)
        add(['cursor'], self.gotoCursorPosition)
        add(['line', 'advanceline', 'skipline', 'l'], self.advanceLine)
        add(['chapter'], self.setChapter)

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
        logger.info("{} {}".format(self.command_history_pos,
                                   self.command_history))

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
        logger.info("{} {}".format(self.command_history_pos,
                                   self.command_history))

    def onBookView(self):
        return self.book_view.isVisible()

    def switch(self, view=None):
        v = 0
        if view in ['shelf', 'shelves', 'main']:
            v = 1
        elif view == 'book':
            v = 2
        self.switchView.emit(v)

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
