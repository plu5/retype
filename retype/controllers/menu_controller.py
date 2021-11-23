from PyQt5.Qt import QAction, QObject

from retype.constants import RETYPE_ISSUE_TRACKER_URL, RETYPE_DOCUMENTATION_URL


class MenuController(QObject):
    def __init__(self, main_controller, menu):
        super().__init__()
        self.controller = main_controller
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
        self._addAction(fileMenu, '&Quit', self.controller.quit,
                        ['Alt+F4'])

    def _viewMenu(self):
        viewMenu = self._menu.addMenu('&View')
        self._addAction(viewMenu, '&Shelf View',
                        lambda: self.controller.setViewByEnum(1), ['Ctrl+1'])
        self._addAction(viewMenu, '&Book View',
                        lambda: self.controller.setViewByEnum(2), ['Ctrl+2'])

    def _optionsMenu(self):
        optionsMenu = self._menu.addMenu('&Options')
        self._addAction(optionsMenu, '&Customise retype',
                        self.controller.showCustomisationDialog, ['Ctrl+O'])

    def _helpMenu(self):
        helpMenu = self._menu.addMenu('&Help')
        self._addAction(helpMenu, "&About", self.controller.showAboutDialog)
        self._addAction(helpMenu, "&Documentation (opens in browser)", lambda:
                        self.controller.openUrl(RETYPE_DOCUMENTATION_URL))
        self._addAction(helpMenu,
                        '&Report issue (opens in browser)', lambda:
                        self.controller.openUrl(RETYPE_ISSUE_TRACKER_URL))
