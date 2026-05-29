import os
import re
import json
import logging
import traceback
from qt import QObject, pyqtSignal

from typing import TYPE_CHECKING

from retype.extras.actions import makeAction

logger = logging.getLogger(__name__)


class K(QObject):
    changed = pyqtSignal()

    def __init__(self,  # type: K
                 shortcuts_no_argstr=None,  # type: list[str] | None
                 shortcuts_per_argstr=None  # type: dict[str, list[str]] | None
                 ):
        # type: (...) -> None
        QObject.__init__(self)
        self.name = ''
        self.entries_map = {'': shortcuts_no_argstr or []}
        if shortcuts_per_argstr is not None:
            self.entries_map = {**self.entries_map, **shortcuts_per_argstr}

    def entries(self):
        # type: (K) -> dict_items
        return self.entries_map.items()

    def s(self, argstr=''):
        # type: (K) -> list[str]
        """Get shortcuts list for an entry"""
        res = self.entries_map.get(argstr, [])
        assert type(res) is list
        return res

    def set_(self, entries_map):
        # type: (dict[str, list[str]]) -> bool
        if entries_map != self.entries_map:
            self.entries_map = entries_map
            self.changed.emit()
            return True
        return False


class Keymap:
    selectors = {}  # type: dict[str, K]
    notifier = K()
    keymaps = {}  # type: dict[str, KeymapData]
    custom_actions = []  # type: list[CustomAction]

    @staticmethod
    def s(selector_name):
        # type: (str) -> K
        ret = Keymap.selectors.get(selector_name)
        if ret is None:
            logger.warning(f'Invalid keymap selector name {selector_name}')
            ret = K()
        return ret

    @staticmethod
    def getValuesDict():
        # type: () -> ValuesDict
        values = {}  # type: ValuesDict
        for name, k in Keymap.selectors.items():
            values[name] = {**k.entries_map}
        return values

    @staticmethod
    def set_(values):
        # type: (ValuesDict) -> None
        changed = False
        for name, d in values.items():
            try:
                changed_ = Keymap.selectors[name].set_(d)
                changed = changed if changed else changed_
            except KeyError:
                logger.error(
                    f'Keymap.set_: Invalid keymap selector name {name}')
        if changed:
            Keymap.notifier.changed.emit()


def getKeymapValues(name, path):
    # type: (str, str) -> ValuesDict
    values = {n: {'': []} for n in Keymap.selectors.keys()}  # fallback
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                values.update(json.load(f))
        except OSError:
            logger.error(f'Failed to open keymap file {name} in {path}.'
                         f'{traceback.format_exc()}')
        except json.decoder.JSONDecodeError:
            logger.error(f'Failed to parse keymap file {name} in {path}.'
                         f'{traceback.format_exc()}')
    else:
        logger.warning(f'Keymap {name} in path {path} not found.')
    return values


def populateKeymaps(app_path, user_path):
    # type: (str, str) -> None
    Keymap.keymaps = {}
    paths = [app_path, user_path] if app_path != user_path else [app_path]
    for path in paths:
        for root, _, files in os.walk(path):
            for f in files:
                if f.lower().endswith('.json'):
                    p = os.path.join(root, f)
                    name = os.path.splitext(f.lower())[0]
                    if name in Keymap.keymaps and path == user_path:
                        name += ' (user dir)'
                    values = getKeymapValues(name, p)
                    Keymap.keymaps[name] = {'path': p, 'values': values}
            break  # do not recurse


def genActions(actions, widget=None):
    # type: (ActionsInfo, QWidget | None) -> None
    """Utility function to generate QActions from a ActionInfo dict"""
    for name, info in actions.items():
        n = name.split(':')
        selector_name = n[0]
        argstr = n[1] if len(n) > 1 else ''
        s = Keymap.s(selector_name).s(argstr)
        if info.get('condition', True):
            before = info.pop('before', None)
            if before:
                before()
            widget = info.pop('widget', None) or widget
            widget_ui = info.pop('widget_ui', None)
            func = info.pop('func', None)
            func_ui = info.pop('func_ui', None)
            if widget_ui and func_ui:
                action_ui = makeAction(**info, widget=widget_ui, func=func_ui)
                info['action_ui'] = action_ui
            action = makeAction(**info, widget=widget, func=func, shortcuts=s)
            info['action'] = action
            info['shortcuts'] = s


def keymapUpdate(actions, widget):
    # type: (ActionsInfo, QWidget) -> None
    """Utility function to update QActions shortcuts"""
    logger.debug(f'keymapUpdate for {type(widget)}')
    # 1. Remove previously created custom actions for widget
    i = len(Keymap.custom_actions) - 1
    while i >= 0:
        a = Keymap.custom_actions[i]
        if a['widget'] is widget:
            a['widget'].removeAction(a['action'])
            del Keymap.custom_actions[i]
        i -= 1
    # 2. Update bindings for actions in actions dictionary
    for name, d in actions.items():
        if not d.get('condition', True):
            continue
        n = name.split(':')
        selector_name = n[0]
        argstr = n[1] if len(n) > 1 else ''
        try:
            s = Keymap.s(selector_name).s(argstr)
            d['shortcuts'] = s
            action = d['action']
            action.setShortcuts(s)
        except (KeyError, AttributeError):
            logger.error(f"Updating k '{name}' failed. "
                         f"{traceback.format_exc()}")
        # Create custom actions based on bindings that lack actions
        for argstr, s in Keymap.s(selector_name).entries():
            if not s or s == ['']:
                continue
            combined_name = selector_name
            combined_name += f':{argstr}' if argstr else ''
            if combined_name in actions:
                continue
            regex = d.get('args_regex')
            func = d.get('args_func')
            if not (regex and func) or not re.match(regex, argstr):
                continue
            action = makeAction(
                combined_name, lambda _, f=func, a=argstr: f(a))
            action.setShortcuts(s)
            Keymap.custom_actions.append({'action': action, 'widget': widget})
            widget.addAction(action)
            logger.debug(
                f'keymapUpdate: Created custom action {combined_name}')
    logger.debug(
        'Keymap.custom_actions (len '
        f'{len(Keymap.custom_actions)}) = {Keymap.custom_actions}')


def keymap(selector, k):
    # type: (str, K) -> Callable[[type[T]], type[T]]
    def decorator(cls):
        # type: (type[T]) -> type[T]
        k.name = selector
        Keymap.selectors[selector] = k
        return cls
    return decorator


if TYPE_CHECKING:
    from typing import Callable, TypeVar, TypedDict  # noqa: F401
    from qt import QAction, QWidget  # noqa: F401
    from retype.extras.metatypes import ActionsInfo  # noqa: F401
    T = TypeVar('T')
    ValuesDict = dict[str, dict[str, list[str]]]
    KeymapData = TypedDict(
        'KeymapData',
        {'path': str, 'values': ValuesDict})
    CustomAction = TypedDict(
        'CustomAction',
        {'action': QAction, 'widget': QWidget})
