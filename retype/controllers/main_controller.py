import os
import json
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

        self.switchViewRequested.connect(self.switchView)
        self.loadBookRequested.connect(self.loadBook)

        self.config_file = 'config.json'
        self.config = self.loadConfig()

        self._initLibrary()
        self._initMenuBar()
        self._instantiateViews()
        self.setView()
        self._connectConsole()
        self._populateLibrary()

    def _instantiateViews(self):
        self.views[View.shelf_view] = ShelfView(self._window, self)

        rdict = self.config.get('rdict', None)
        self.views[View.book_view] = BookView(self._window, self,
                                              rdict)

    def _viewFromEnumOrInt(self, view):
        if isinstance(view, View):
            return self.views[view]
        elif isinstance(view, int):
            return self.views[View(view)]
        else:
            logger.error("Improper view identifier {}".format(view))

    def setView(self, view=View.shelf_view):
        """Gets the view instance and and brings it to fore"""
        self._view = self._viewFromEnumOrInt(view)
        self._window.stacker.addWidget(self._view)
        self._window.stacker.setCurrentWidget(self._view)

    def view(self):
        return self._view

    def isVisible(self, view):
        return self._viewFromEnumOrInt(view).isVisible()

    def switchView(self, view=None):
        # If no argument (or 0), switch to shelf view if not on it, otherwise
        #  switch to book view
        if not view:
            view = View.shelf_view if not self.isVisible(View.shelf_view)\
                else View.book_view
        self.setView(view)

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

    def loadConfig(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config
