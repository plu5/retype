from qt import QObject

from typing import TYPE_CHECKING

from retype.constants import (
    RETYPE_ISSUE_TRACKER_URL, RETYPE_DOCUMENTATION_URL, iswindows)
from retype.services.keymap import keymap, K, Keymap, genActions, keymapUpdate


@keymap('Menu.quit', K(['Alt+F4']))
@keymap('Menu.setViewByEnum', K([], {'1': ['Ctrl+1'], '2': ['Ctrl+2']}))
@keymap('Menu.showCustomisationDialog', K(['Ctrl+O']))
@keymap('Menu.toggleConsoleWindow', K())
@keymap('Menu.showTypespeed', K())
@keymap('Menu.showSteno', K())
@keymap('Menu.about', K())
@keymap('Menu.documentation', K())
@keymap('Menu.reportIssue', K())
class MenuController(QObject):
    def __init__(self, main_controller, menu):
        # type: (MenuController, MainController, QMenuBar) -> None
        super().__init__()
        self.controller = main_controller
        self._menu = menu
        self._initMenuBar()
        Keymap.notifier.changed.connect(
            lambda: keymapUpdate(self.actions, self._menu))

    def _initMenuBar(self):
        # type: (MenuController) -> None
        fileMenu = self._menu.addMenu('&File')
        viewMenu = self._menu.addMenu('&View')
        gamesMenu = self._menu.addMenu('&Games')
        optionsMenu = self._menu.addMenu('&Options')
        helpMenu = self._menu.addMenu('&Help')

        self.actions = {
            'Menu.quit': {
                'widget': fileMenu, 'name': '&Quit',
                'func': self.controller.quit, 'icon': 'door',
            },
            'Menu.setViewByEnum:1': {
                'widget': viewMenu, 'name': '&Shelf View',
                'func': lambda: self.controller.setViewByEnum(1),
                'icon': 'shelf_view',
                'args_regex': r'[1-2]',
                'args_func': lambda d: self.controller.setViewByEnum(int(d)),
            },
            'Menu.setViewByEnum:2': {
                'widget': viewMenu, 'name': '&Book View',
                'func': lambda: self.controller.setViewByEnum(2),
                'icon': 'open_book',
            },
            'Menu.toggleConsoleWindow': {
                'widget': viewMenu, 'name': 'Toggle System &Console',
                'func': lambda: self.controller.toggleConsoleWindow(),
                'icon': 'console', 'condition': iswindows,
                'before': viewMenu.addSeparator,
            },
            'Menu.showTypespeed': {
                'widget': gamesMenu, 'name': '&Typespeed',
                'func': self.controller.showTypespeed, 'icon': 'typespeed',
            },
            'Menu.showSteno': {
                'widget': gamesMenu, 'name': '&Learn Stenography',
                'func': self.controller.showSteno, 'icon': 'steno',
            },
            'Menu.showCustomisationDialog': {
                'widget': optionsMenu, 'name': '&Customise retype',
                'func': self.controller.showCustomisationDialog,
                'icon': 'customise',
            },
            'Menu.about': {
                'widget': helpMenu, 'name': "&About",
                'func': self.controller.showAboutDialog, 'icon': 'about',
            },
            'Menu.documentation': {
                'widget': helpMenu,
                'name': "&Documentation (opens in browser)",
                'func': lambda: self.controller.openUrl(
                    RETYPE_DOCUMENTATION_URL),
                'icon': 'documentation',
            },
            'Menu.reportIssue': {
                'widget': helpMenu, 'name': '&Report issue (opens in browser)',
                'func': lambda: self.controller.openUrl(
                    RETYPE_ISSUE_TRACKER_URL),
                'icon': 'issue',
            },
        }  # type: ActionsInfo

        genActions(self.actions)


if TYPE_CHECKING:
    from qt import QMenu, QMenuBar  # noqa: F401
    from retype.controllers import MainController  # noqa: F401
    from retype.extras.metatypes import ActionsInfo  # noqa: F401
