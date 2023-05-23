import logging
from enum import Enum
from qt import QObject, pyqtSignal, QUrl, QDesktopServices

from retype.ui import (MainWin, ShelfView, BookView, CustomisationDialog,
                       AboutDialog)
from retype.controllers import SafeConfig, MenuController, LibraryController
from retype.console import Console
from retype.constants import iswindows

logger = logging.getLogger(__name__)


class View(Enum):
    shelf_view = 1
    book_view = 2


class MainController(QObject):
    views = {}
    switchViewRequested = pyqtSignal(int)
    prevViewRequested = pyqtSignal()
    loadBookRequested = pyqtSignal(int)
    saveConfigRequested = pyqtSignal(dict)
    customisationDialogRequested = pyqtSignal()
    aboutDialogRequested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.config = SafeConfig()

        self.console = Console(
            self.config['prompt'], self.config['console_font'])
        self._window = MainWin(self.console, self.getGeometry(self.config))
        if iswindows:
            self._window.opened.connect(self.maybeHideConsoleWindow)
            self.console_status = None

        self._view = None
        self._prev_view = None
        self.about_dialog = None

        self.switchViewRequested.connect(self.switchView)
        self.prevViewRequested.connect(self.prevView)
        self.loadBookRequested.connect(self.loadBook)
        self.saveConfigRequested.connect(self.saveConfig)
        self.customisationDialogRequested.connect(self.showCustomisationDialog)
        self.aboutDialogRequested.connect(self.showAboutDialog)

        self._initLibrary()
        self._initMenuBar()
        self._instantiateViews()
        self.setViewByEnum(View.shelf_view)
        self._connectConsole()
        self._populateLibrary()

    def _instantiateViews(self):
        self.views[View.shelf_view] = ShelfView(self._window, self)

        rdict = self.config['rdict']
        bookview_settings = self.config['bookview']
        self.views[View.book_view] = BookView(self._window, self, rdict,
                                              bookview_settings)

        self.customisation_dialog = CustomisationDialog(
            self.config.raw, self._window,
            self.saveConfigRequested, self.prevViewRequested,
            self.views[View.book_view].getFontSize, self._window)

    def _viewFromEnumOrInt(self, view):
        if isinstance(view, View):
            return self.views[view]
        elif isinstance(view, int):
            return self.views[View(view)]
        else:
            logger.error("Improper view identifier {}".format(view))

    def _setView(self, view):
        """Brings the view instance to the fore"""
        self._window.stacker.addWidget(view)
        self._window.stacker.setCurrentWidget(view)

    def setView(self, view):
        # Clear console before view change
        self.console.clear()

        if view is self._view:
            return
        self._prev_view = self._view
        self._setView(view)
        self._view = view

    def setViewByEnum(self, view_e=View.shelf_view):
        self.setView(self._viewFromEnumOrInt(view_e))

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
        self.setViewByEnum(view)

    def showCustomisationDialog(self):
        self.customisation_dialog.show()

    def prevView(self):
        self.setView(self._prev_view)

    def show(self):
        self._window.show()

    def _initMenuBar(self):
        menu = self._window.menuBar()
        self._menu_controller = MenuController(self, menu)

    def quit(self):
        self._window.close()

    def _initLibrary(self):
        self.library = LibraryController(self.config['user_dir'],
                                         self.config['library_paths'])

    def _populateLibrary(self):
        """Instantiate all the book wrappers and shelf items"""
        shelf_view = self.views[View.shelf_view]
        self.library.instantiateBooks()
        shelf_view._populate()

    def _repopulateLibrary(self, user_dir, library_paths):
        self.library.__init__(user_dir, library_paths)
        shelf_view = self.views[View.shelf_view]
        self.library.instantiateBooks()
        shelf_view.repopulate()

    def loadBook(self, book_id=0):
        book_view = self.views[View.book_view]
        self.library.setBook(book_id, book_view, self.switchViewRequested)

    def _connectConsole(self):
        """Pass some signals console services need access to"""
        self.console.initServices(self.views[View.book_view],
                                  self.switchViewRequested,
                                  self.loadBookRequested,
                                  self.customisationDialogRequested,
                                  self.aboutDialogRequested)

    def saveConfig(self, config):
        self.config.save(config)

        # Repopulate library if paths changed
        if config['library_paths'] != self.library.library_paths:
            logger.debug("Repopulating library")
            self._repopulateLibrary(config['user_dir'],
                                    config['library_paths'])

        # Update prompt if changed
        if config['prompt'] != self.console.prompt:
            self.console.prompt = config['prompt']

        # Update rdict
        self.views[View.book_view].rdict = config['rdict']

        # Update library’s user_dir
        self.library.user_dir = config['user_dir']

        # Update book display font
        if not config['bookview']['save_font_size_on_quit']:
            self.views[View.book_view].setFontSize(
                config['bookview']['font_size'])
        self.views[View.book_view].setFontFamily(config['bookview']['font'])

        # Update console font
        self.console.font_family = config['console_font']

    def getGeometry(self, config):
        return config['window']

    def openUrl(self, url_str):
        url = QUrl(url_str)
        QDesktopServices.openUrl(url)

    def showAboutDialog(self, page_title=None):
        if self.about_dialog is None:
            self.about_dialog = AboutDialog(
                self.console.command_service.commands_info,
                self.config['prompt'], self.library.books, self._window)
        self.about_dialog.show()
        self.about_dialog.setActivePage(page_title)

    if iswindows:
        def hideConsoleWindow(self, show=False):
            try:
                from win32gui import ShowWindow
                from win32console import GetConsoleWindow
                from win32con import SW_HIDE, SW_SHOW
                action = SW_SHOW if show else SW_HIDE
                ShowWindow(GetConsoleWindow(), action)
                self.console_status = show
            except ImportError:
                logger.info("No pywin32")

        def toggleConsoleWindow(self):
            if self.console_status is not None:
                self.hideConsoleWindow(not self.console_status)

        def maybeHideConsoleWindow(self):
            hide = self.config['hide_sysconsole']
            if hide:
                self.hideConsoleWindow()
