import os
import json
import logging
from enum import Enum
from copy import deepcopy
from qt import QObject, QApplication, pyqtSignal, QUrl, QDesktopServices

from retype.ui import (MainWin, ShelfView, BookView, CustomisationDialog,
                       AboutDialog)
from retype.controllers import MenuController, LibraryController
from retype.console import Console
from retype.constants import default_config

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

        self.config_rel_path = 'config.json'
        self.config = self.loadConfig(self.config_rel_path)

        self.console = Console(self.config['prompt'])
        self._window = MainWin(self.console, self.getGeometry(self.config))

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

        rdict = self.config.get('rdict', None)
        bookview_settings = self.config.get('bookview', None)
        self.views[View.book_view] = BookView(self._window, self, rdict,
                                              bookview_settings)

        self.customisation_dialog = CustomisationDialog(
            self.config, self._window,
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
        if view is self._view:
            return
        self._prev_view = self._view
        self._setView(view)
        self._view = view

        # Clear console after view change
        self.console.clear()

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
        QApplication().quit()

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

    def isPathDefaultUserDir(self, path):
        return os.path.abspath(path) == \
            os.path.abspath(default_config['user_dir'])

    def loadConfig(self, path):
        config = self._loadConfig(path)
        user_dir = config['user_dir'] if config else None
        if user_dir and not self.isPathDefaultUserDir(user_dir):
            custom_path = os.path.join(user_dir, self.config_rel_path)
            logger.debug("Non-default user_dir: {}\n\
Attempting to load config from: {}".format(user_dir, custom_path))
            config = self._loadConfig(custom_path)
            if not config:
                config = deepcopy(default_config)
                config['user_dir'] = user_dir
                return config
        return config or default_config

    def _loadConfig(self, path):
        if os.path.exists(path):
            with open(path, 'r') as f:
                config = json.load(f)
                return config

    def saveConfig(self, config):
        user_dir = config['user_dir']
        path = os.path.join(user_dir, self.config_rel_path)
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
        if not self.isPathDefaultUserDir(user_dir):
            with open(self.config_rel_path, 'r') as f:
                dconfig = json.load(f)
                dconfig['user_dir'] = user_dir
            with open(self.config_rel_path, 'w') as f:
                json.dump(dconfig, f, indent=2)

        # Repopulate library if paths changed
        if config['library_paths'] != self.library.library_paths:
            logger.debug("Repopulating library")
            self._repopulateLibrary(user_dir, config['library_paths'])

        # Update prompt if changed
        if config['prompt'] != self.console.prompt:
            self.console.prompt = config['prompt']

        # Update rdict
        self.views[View.book_view].rdict = config['rdict']

        # Update library’s user_dir
        self.library.user_dir = config['user_dir']

    def getGeometry(self, config):
        return config.get('window', default_config['window'])

    def openUrl(self, url_str):
        url = QUrl(url_str)
        QDesktopServices.openUrl(url)

    def showAboutDialog(self, page_title=None):
        if self.about_dialog is None:
            self.about_dialog = AboutDialog(
                self.console.command_service.commands_info, self.config['prompt'], self.library.books, self._window)
        self.about_dialog.show()
        self.about_dialog.setActivePage(page_title)
