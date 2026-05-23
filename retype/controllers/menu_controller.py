import logging
import traceback
from qt import QAction, QObject

from typing import TYPE_CHECKING

from retype.constants import (
    RETYPE_ISSUE_TRACKER_URL, RETYPE_DOCUMENTATION_URL, iswindows)
from retype.resource_handler import getIcon
from retype.services.keymap import keymap, K, Keymap

logger = logging.getLogger(__name__)


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

    def _initMenuBar(self):
        # type: (MenuController) -> None
        fileMenu = self._menu.addMenu('&File')
        viewMenu = self._menu.addMenu('&View')
        gamesMenu = self._menu.addMenu('&Games')
        optionsMenu = self._menu.addMenu('&Options')
        helpMenu = self._menu.addMenu('&Help')

        self.actions = {
            'Menu.quit': {
                'menu': fileMenu, 'name': '&Quit',
                'func': self.controller.quit, 'icon': 'door',
            },
            'Menu.setViewByEnum:1': {
                'menu': viewMenu, 'name': '&Shelf View',
                'func': lambda: self.controller.setViewByEnum(1),
                'icon': 'shelf_view',
            },
            'Menu.setViewByEnum:2': {
                'menu': viewMenu, 'name': '&Book View',
                'func': lambda: self.controller.setViewByEnum(2),
                'icon': 'open_book',
            },
            'Menu.toggleConsoleWindow': {
                'menu': viewMenu, 'name': 'Toggle System &Console',
                'func': lambda: self.controller.toggleConsoleWindow(),
                'icon': 'console', 'condition': iswindows,
                'before': viewMenu.addSeparator,
            },
            'Menu.showTypespeed': {
                'menu': gamesMenu, 'name': '&Typespeed',
                'func': self.controller.showTypespeed, 'icon': 'typespeed',
            },
            'Menu.showSteno': {
                'menu': gamesMenu, 'name': '&Learn Stenography',
                'func': self.controller.showSteno, 'icon': 'steno',
            },
            'Menu.showCustomisationDialog': {
                'menu': optionsMenu, 'name': '&Customise retype',
                'func': self.controller.showCustomisationDialog,
                'icon': 'customise',
            },
            'Menu.about': {
                'menu': helpMenu, 'name': "&About",
                'func': self.controller.showAboutDialog, 'icon': 'about',
            },
            'Menu.documentation': {
                'menu': helpMenu, 'name': "&Documentation (opens in browser)",
                'func': lambda: self.controller.openUrl(
                    RETYPE_DOCUMENTATION_URL),
                'icon': 'documentation',
            },
            'Menu.reportIssue': {
                'menu': helpMenu, 'name': '&Report issue (opens in browser)',
                'func': lambda: self.controller.openUrl(
                    RETYPE_ISSUE_TRACKER_URL),
                'icon': 'issue',
            },
        }  # type: dict[str, ActionInfo]

        for name, info in self.actions.items():
            n = name.split(':')
            selector_name = n[0]
            argstr = n[1] if len(n) > 1 else ''
            info['shortcuts'] = Keymap.s(selector_name).s(argstr)
            if info.pop('condition', True):
                before = info.pop('before', None)
                if before:
                    before()
                action = self._addAction(**info)
            info['action'] = action

    def _makeAction(self,  # type: MenuController
                    name,  # type: str
                    func,  # type: Callable[[], None]
                    shortcuts=None,  # type: list[str] | None
                    icon_name=None  # type: str | None
                    ):
        # type: (...) -> QAction
        action = QAction(name, self)
        action.triggered.connect(func)
        if shortcuts:
            action.setShortcuts(shortcuts)
        if icon_name:
            action.setIcon(getIcon(icon_name))
        return action

    def _addAction(self,  # type: MenuController
                   menu,  # type: QMenu
                   name,  # type: str
                   func,  # type: Callable[[], None]
                   shortcuts=None,  # type: list[str] | None
                   icon=None  # type: str | None
                   ):
        # type: (...) -> None
        action = self._makeAction(name, func, shortcuts, icon)
        menu.addAction(action)

    def keymapUpdate(self):
        # type: (MenuController) -> None
        if not hasattr(self, 'actions'):
            logger.warning("keymapUpdate called with no actions set")
            return
        for name, d in self.actions.items():
            n = name.split(':')
            selector_name = n[0]
            argstr = n[1] if len(n) > 1 else ''
            try:
                s = Keymap.s(selector_name).s(argstr)
                d['shortcuts'] = s
                d['action'].setShortcuts(s)
            except KeyError:
                logger.error(f"Updating k '{name}' failed with KeyError. "
                             f"{traceback.format_exc()}")


if TYPE_CHECKING:
    from qt import QMenu, QMenuBar, QKeySequence  # noqa: F401
    from retype.controllers import MainController  # noqa: F401
    from typing import Callable, TypedDict  # noqa: F401
    ActionInfo = TypedDict(
        'ActionInfo',
        {'menu': QMenu, 'name': str, 'func': Callable[[], None],
         'tooltip': str, 'shortcuts': list[str], 'icon': str,
         'action': QAction, 'condition': bool, 'before': Callable[[], None]},
        total=False)
