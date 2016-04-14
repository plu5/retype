from enum import Enum
from PyQt5.QtWidgets import (qApp)
from PyQt5.QtCore import (QObject)
from views import ShelfView, BookView
from controllers.menu_controller import MenuController


class View(Enum):
    shelfview = 1
    bookview = 2


class MainController(QObject):
    #view = View()
    views = {}

    def __init__(self, window):
        super().__init__()
        self._window = window
        self._window.switchViewSignal.connect(self.switchView)
        #self._view = view
        # this will have settings, qss etc
        self._instantiateViews()
        self._initView()
        self._initMenuBar()

    def _instantiateViews(self):
        self.views[View.shelfview] = ShelfView(self._window)
        self.views[View.shelfview].switchViewSignal.connect(self.switchView)
        self.views[View.bookview] = BookView(self._window)
        self.views[View.bookview].switchViewSignal.connect(self.switchView)

    def _initView(self, view=View.shelfview):
        self._view = self.views[view]
        self._window.stacker.addWidget(self._view)
        self._window.stacker.setCurrentWidget(self._view)

    def getView(self):
        return self._view

    def switchView(self, intview):###
        #self._initView(view)
        self._initView(View(intview))

    def show(self):
        #self._initView()
        self._window.show()

    def _initMenuBar(self):
        menu = self._window.menuBar()
        self._menu_controller = MenuController(self, menu)

    def exit(self):
        qApp.quit
