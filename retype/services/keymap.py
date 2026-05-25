import os
import json
import logging
import traceback
from qt import QObject, pyqtSignal

from typing import TYPE_CHECKING

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
    T = TypeVar('T')
    ValuesDict = dict[str, dict[str, list[str]]]
    KeymapData = TypedDict(
        'KeymapData',
        {'path': str, 'values': ValuesDict})
