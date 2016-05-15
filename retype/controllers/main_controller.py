import logging
from enum import Enum
from PyQt5.QtWidgets import (qApp)
from PyQt5.QtCore import (QObject)
from ui import ShelfView, BookView
from controllers.menu_controller import MenuController
from controllers.library import LibraryController

logger = logging.getLogger(__name__)


class View(Enum):
    shelfview = 1
    bookview = 2


class MainController(QObject):
    views = {}

    def __init__(self, window):
        super().__init__()
        self._window = window
        self._window.switchViewSignal.connect(self.switchView)

        # this will have settings, qss etc
        self._initLibrary()
        self._initMenuBar()
        self._instantiateViews()
        self._initView()
        self._connectConsole()

    def _instantiateViews(self):
        self.views[View.shelfview] = ShelfView(self._window)
        self.views[View.bookview] = BookView(self._window, self)

    def _initView(self, view=View.shelfview):
        self._view = self.views[view]
        self._window.stacker.addWidget(self._view)
        self._window.stacker.setCurrentWidget(self._view)

    def getView(self):
        return self._view

    def switchView(self, intview):
        """gets the view instance and calls _initView with it"""
        self._initView(View(intview))

    def show(self):
        #self._initView()
        self._window.show()

    def _initMenuBar(self):
        menu = self._window.menuBar()
        self._menu_controller = MenuController(self, menu)

    def exit(self):
        qApp.quit

    def _initLibrary(self):
        self._library = LibraryController(self)

    def loadBook(self, book_id=0):
        bookview = self.views[View.bookview]
        if book_id in self._library._book_list:
            logger.info("Loading book {}".format(book_id))
            self._library.setBook(book_id, bookview)
        else:
            logging.error("book_id {} cannot be found".format(book_id))
            logging.debug("_book_list: {}".format(self._library._book_list))
            return

    def _connectConsole(self):
        console = self._window.console
        console.loadBookSignal.connect(self.loadBook)
