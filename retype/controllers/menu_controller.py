from qt import QAction, QObject

from typing import TYPE_CHECKING

from retype.constants import (
    RETYPE_ISSUE_TRACKER_URL, RETYPE_DOCUMENTATION_URL, iswindows)
from retype.resource_handler import getIcon


class MenuController(QObject):
    def __init__(self, main_controller, menu):
        # type: (MenuController, MainController, QMenuBar) -> None
        super().__init__()
        self.controller = main_controller
        self._menu = menu
        self._initMenuBar()

    def _initMenuBar(self):
        # type: (MenuController) -> None
        self._fileMenu()
        self._viewMenu()
        self._gamesMenu()
        self._optionsMenu()
        self._helpMenu()

    def _makeAction(self,  # type: MenuController
                    name,  # type: str
                    connect_to,  # type: Callable[[], None]
                    shortcuts=None,  # type: list[str] | None
                    icon_name=None  # type: str | None
                    ):
        # type: (...) -> QAction
        action = QAction(name, self)
        action.triggered.connect(connect_to)
        if shortcuts:
            action.setShortcuts(shortcuts)
        if icon_name:
            action.setIcon(getIcon(icon_name))
        return action

    def _addAction(self,  # type: MenuController
                   menu,  # type: QMenu
                   action_name,  # type: str
                   connect_to,  # type: Callable[[], None]
                   shortcuts=None,  # type: list[str] | None
                   icon_name=None  # type: str | None
                   ):
        # type: (...) -> None
        action = self._makeAction(action_name, connect_to, shortcuts,
                                  icon_name)
        menu.addAction(action)

    def _fileMenu(self):
        # type: (MenuController) -> None
        fileMenu = self._menu.addMenu('&File')
        self._addAction(fileMenu, '&Quit', self.controller.quit,
                        ['Alt+F4'], 'door')

    def _viewMenu(self):
        # type: (MenuController) -> None
        viewMenu = self._menu.addMenu('&View')
        self._addAction(viewMenu, '&Shelf View',
                        lambda: self.controller.setViewByEnum(1), ['Ctrl+1'],
                        'shelf_view')
        self._addAction(viewMenu, '&Book View',
                        lambda: self.controller.setViewByEnum(2), ['Ctrl+2'],
                        'open_book')

        if iswindows:
            viewMenu.addSeparator()
            self._addAction(viewMenu, 'Toggle System &Console',
                            lambda: self.controller.toggleConsoleWindow(),
                            icon_name='console')

    def _gamesMenu(self):
        # type: (MenuController) -> None
        gamesMenu = self._menu.addMenu('&Games')
        self._addAction(gamesMenu, '&Typespeed', self.controller.showTypespeed,
                        icon_name='typespeed')
        self._addAction(gamesMenu, '&Learn Stenography',
                        self.controller.showSteno, icon_name='steno')

    def _optionsMenu(self):
        # type: (MenuController) -> None
        optionsMenu = self._menu.addMenu('&Options')
        self._addAction(optionsMenu, '&Customise retype',
                        self.controller.showCustomisationDialog, ['Ctrl+O'],
                        'customise')

    def _helpMenu(self):
        # type: (MenuController) -> None
        helpMenu = self._menu.addMenu('&Help')
        self._addAction(helpMenu, "&About", self.controller.showAboutDialog,
                        icon_name='about')
        self._addAction(helpMenu, "&Documentation (opens in browser)", lambda:
                        self.controller.openUrl(RETYPE_DOCUMENTATION_URL),
                        icon_name='documentation')
        self._addAction(helpMenu,
                        '&Report issue (opens in browser)', lambda:
                        self.controller.openUrl(RETYPE_ISSUE_TRACKER_URL),
                        icon_name='issue')


if TYPE_CHECKING:
    from qt import QMenu, QMenuBar  # noqa: F401
    from retype.controllers import MainController  # noqa: F401
    from typing import Callable  # noqa: F401
