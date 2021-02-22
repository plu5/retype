import logging

logger = logging.getLogger(__name__)


class CommandService(object):
    def __init__(self, console, book_view, switchView):
        self._console = console
        self.book_view = book_view
        self.switchView = switchView
        self._console.submitted.connect(self._handleCommands)
        self.prompt = '>'
        self._initCommands()
        self._initCommandHistory()

    def _initCommands(self):
        self.commands = {}
        self.commands['switchmain'] = self.switchMain
        self.commands['switchbook'] = self.switchBook
        self.commands['loadbook'] = self.loadBook
        self.commands['booklist'] = self.bookList
        self.commands['nextchapter'] = self.nextChapter
        self.commands['previouschapter'] = self.previousChapter
        # next chapter, previous chapter. set chapter?
        self.commands['advanceline'] = self.advanceLine
        self.commands['l'] = self.advanceLine

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
            if text not in self.command_history:
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

    def switchMain(self):
        self.switchView.emit(1)

    def switchBook(self):
        self.switchView.emit(2)

    def loadBook(self, book_id=0):
        try:
            self._console.loadBook.emit(int(book_id))
        except ValueError:
            logger.error('{} is not a valid book_id'.format(book_id))

    def bookList(self):
        print()
        # get main_controller’s library’s booklist, and id of each book
        # actually, it’d be better to connect it to a function elsewhere.
        # how would i show it? some way to print it to users not in the console
        # TODO: a function to refresh booklist if users have added a book while
        # the program was running

    def nextChapter(self):  # not the best
        if self.book_view.isVisible():
            self.book_view.nextChapter()
        else:
            logger.error('not in BookView')

    def previousChapter(self):
        if self.book_view.isVisible():
            self.book_view.previousChapter()
        else:
            logger.error('not in BookView')

    def advanceLine(self):
        self._console._highlighting_service.advanceLine()
