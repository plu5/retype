from PyQt5.QtWidgets import (QAction)
from PyQt5.QtCore import (QObject)

class MenuController(QObject):
    def __init__(self, main_controller, menu):
        super().__init__()
        self._main_controller = main_controller
        self._menu = menu
        self._initMenuBar()

    def _initMenuBar(self):
        self._fileMenu()
        self._switchMenu()
        self._optionsMenu()
        self._helpMenu()

    def _fileMenu(self):
        fileMenu = self._menu.addMenu('&file')
        fileMenu.addAction(self._exitAction())

    def _switchMenu(self):
        switchMenu = self._menu.addMenu('&switch')

    def _optionsMenu(self):
        optionsMenu = self._menu.addMenu('&options')
        optionsMenu.addAction(self._customiseAction())

    def _helpMenu(self):
        helpMenu = self._menu.addMenu('&help')

    def _exitAction(self):
        action = QAction('e&xit', self)
        action.setShortcuts(["Alt+F4"])
        action.triggered.connect(self._main_controller.exit)
        return action

    def _customiseAction(self):
        action = QAction('&customise retype', self)
        return action
