import logging
from enum import Enum
from PyQt5.Qt import QObject, qApp, pyqtSignal

from retype.ui import MainWin, ShelfView, BookView
from retype.controllers import MenuController, LibraryController
from retype.console import Console

logger = logging.getLogger(__name__)


class View(Enum):
    shelf_view = 1
    book_view = 2


class MainController(QObject):
    views = {}
    switchViewRequested = pyqtSignal(int)
    loadBookRequested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.console = Console()
        self._window = MainWin(self.console)

        self.switchViewRequested.connect(self.setView)
        self.loadBookRequested.connect(self.loadBook)

        self._initLibrary()
        self._initMenuBar()
        self._instantiateViews()
        self.setView()
        self._connectConsole()
        self._populateLibrary()

    def _instantiateViews(self):
        self.views[View.shelf_view] = ShelfView(self._window, self)
        self.views[View.book_view] = BookView(self._window, self)

    def setView(self, view=View.shelf_view):
        """Gets the view instance and and brings it to fore"""
        if type(view) is View:
            self._view = self.views[view]
        elif type(view) is int:
            self._view = self.views[View(view)]
        else:
            logger.error("Improper view identifier {}".format(view))
        self._window.stacker.addWidget(self._view)
        self._window.stacker.setCurrentWidget(self._view)

    def getView(self):
        return self._view

    def show(self):
        self._window.show()

    def _initMenuBar(self):
        menu = self._window.menuBar()
        self._menu_controller = MenuController(self, menu)

    def quit(self):
        qApp.quit()

    def _initLibrary(self):
        self.library = LibraryController(self)

    def _populateLibrary(self):
        """Instantiate all the book wrappers and shelf items"""
        shelf_view = self.views[View.shelf_view]
        self.library.instantiateBooks()
        shelf_view._populate()

    def loadBook(self, book_id=0):
        book_view = self.views[View.book_view]
        self.library.setBook(book_id, book_view, self.switchViewRequested)

    def _connectConsole(self):
        """Pass some signals console services need access to"""
        console = self._window.console
        console.initServices(self.views[View.book_view],
                             self.switchViewRequested,
                             self.loadBookRequested)
