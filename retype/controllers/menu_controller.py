from PyQt5.Qt import QAction, QObject

from retype.constants import issue_tracker


class MenuController(QObject):
    def __init__(self, main_controller, menu):
        super().__init__()
        self._main_controller = main_controller
        self._menu = menu
        self._initMenuBar()

    def _initMenuBar(self):
        self._fileMenu()
        self._viewMenu()
        self._optionsMenu()
        self._helpMenu()

    def _makeAction(self, name, connect_to, shortcuts=None):
        action = QAction(name, self)
        action.triggered.connect(connect_to)
        if shortcuts:
            action.setShortcuts(shortcuts)
        return action

    def _addAction(self, menu, action_name, connect_to, shortcuts=None):
        action = self._makeAction(action_name, connect_to, shortcuts)
        menu.addAction(action)

    def _fileMenu(self):
        fileMenu = self._menu.addMenu('&File')
        self._addAction(fileMenu, '&Quit', self._main_controller.quit,
                        ['Alt+F4'])

    def _viewMenu(self):
        viewMenu = self._menu.addMenu('&View')
        self._addAction(viewMenu, '&Shelf View',
                        lambda: self._main_controller.setViewByEnum(1))
        self._addAction(viewMenu, '&Book View',
                        lambda: self._main_controller.setViewByEnum(2))

    def _optionsMenu(self):
        optionsMenu = self._menu.addMenu('&Options')
        self._addAction(optionsMenu, '&Customise retype',
                        self._main_controller.showCustomisationDialog)

    def _helpMenu(self):
        helpMenu = self._menu.addMenu('&Help')
        self._addAction(helpMenu,
                        '&Report issue (opens in browser)',
                        lambda: self._main_controller.openUrl(issue_tracker))
