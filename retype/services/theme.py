import os
import logging
from qt import QColor, QObject, pyqtSignal
from tinycss2.parser import parse_stylesheet, parse_declaration_list

from typing import TYPE_CHECKING

from retype.extras.qss import findSelector, getCValue, serialiseValuesDict

logger = logging.getLogger(__name__)


class ThemeCProp():
    def __init__(self, qss_property, value=None):
        # type: (ThemeCProp, str, str | None) -> None
        self.used = value is not None
        self.qss_property = qss_property
        self.value = value
        self.c = QColor(value)

    def __call__(self):
        # type: (ThemeCProp) -> QColor
        return self.c

    def set_(self, value):
        # type: (ThemeCProp, str) -> None
        self.value = value
        self.c = QColor(value)


class C(QObject):
    changed = pyqtSignal()

    def __init__(self,  # type: C
                 fg=None,  # type: str | None
                 bg=None,  # type: str | None
                 outline=None,  # type: str | None
                 l_border=None,  # type: str | None
                 r_border=None,  # type: str | None
                 t_border=None,  # type: str | None
                 b_border=None,  # type: str | None
                 sel=None,  # type: str | None
                 sel_bg=None  # type: str | None
                 ):
        # type: (...) -> None
        QObject.__init__(self)
        self.name = ''
        self.fg = ThemeCProp('color', fg)
        self.bg = ThemeCProp('background-color', bg)
        self.outline = ThemeCProp('outline-color', outline)
        self.l_border = ThemeCProp('border-left-color', l_border)
        self.r_border = ThemeCProp('border-right-color', r_border)
        self.t_border = ThemeCProp('border-top-color', t_border)
        self.b_border = ThemeCProp('border-bottom-color', b_border)
        self.sel = ThemeCProp('selection-color', sel)
        self.sel_bg = ThemeCProp('selection-background-color', sel_bg)
        self.props = [self.fg, self.bg, self.outline, self.l_border,
                      self.r_border, self.t_border, self.b_border, self.sel,
                      self.sel_bg]


class Theme:
    selectors = {}  # type: dict[str, C]
    themes = {}  # type: dict[str, ThemeData]
    # ^ Theme.themes[name] = {'path': p, 'values': values}
    # TEMP: dict[str, dict[str, str | ValuesDict]]

    @staticmethod
    def get(selector_name):
        # type: (str) -> C
        ret = Theme.selectors.get(selector_name)
        if ret is None:
            logger.warning(f'Invalid theme selector name {selector_name}')
            ret = C()
        return ret

    @staticmethod
    def connect_changed(selector_name, f):
        # type: (str, Callable[[], None]) -> None
        s = Theme.get(selector_name)
        if isinstance(s, C):
            s.changed.connect(f)

    @staticmethod
    def getValuesDict():
        # type: () -> ValuesDict
        return selectorsToValuesDict(Theme.selectors)

    @staticmethod
    def getQss(selector_name=None):
        # type: (str | None) -> str
        qss = ''
        values = Theme.getValuesDict()
        if selector_name is None:
            qss = serialiseValuesDict(values)
        else:
            s = values.get(selector_name)
            if s:
                qss = serialiseValuesDict({selector_name: s})
            else:
                logger.warning(f'getQss: Selector name {selector_name} not '
                               'found')
        return qss

    @staticmethod
    def set_(values):
        # type: (ValuesDict) -> None
        changed_selectors = []
        for name, s in Theme.selectors.items():
            changed = False
            for p in s.props:
                if p.used:
                    new_value = values.get(s.name, {}).get(p.qss_property)
                    if new_value is not None:
                        p.set_(new_value)
                        changed = True
            if changed:
                changed_selectors.append(s)
        for s in changed_selectors:
            s.changed.emit()


def getThemeValues(name, path):
    # type: (str, str) -> ValuesDict
    values = {}
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                qss = f.read()
                values = valuesFromQss(Theme.getValuesDict(), qss)
        except OSError as e:
            logger.error(f'Failed to open theme file {name} in {path}')
            logger.error(f'{type(e)}: {e}')
    else:
        logger.warning(f'Theme {name} in path {path} not found.')
    return values


def populateThemes(app_path, user_path):
    # type: (str, str) -> None
    Theme.themes = {}
    paths = [app_path, user_path] if app_path != user_path else [app_path]
    for path in paths:
        for root, _, files in os.walk(path):
            for f in files:
                if f.lower().endswith('.qss'):
                    p = os.path.join(root, f)
                    name = os.path.splitext(f.lower())[0]
                    if name in Theme.themes and path == user_path:
                        name += ' (user dir)'
                    values = getThemeValues(name, p)
                    Theme.themes[name] = {'path': p, 'values': values}
            break  # do not recurse


def selectorsToValuesDict(selectors):
    # type: (dict[str, C]) -> ValuesDict
    values = {}  # type: ValuesDict
    for name, s in selectors.items():
        values[name] = {}
        for p in s.props:
            if p.used and p.value is not None:
                values[name][p.qss_property] = p.value
    return values


def valuesFromQss(needed_values_dict, qss):
    # type: (ValuesDict, str) -> ValuesDict
    ss = parse_stylesheet(qss)
    output_values_dict = {}  # type: ValuesDict
    for selector_name, props in needed_values_dict.items():
        s = findSelector(selector_name, ss)
        if not s:
            continue
        output_values_dict[selector_name] = {}
        declarations = parse_declaration_list(s)
        for prop_name in props:
            c = getCValue(prop_name, declarations)
            if not c:
                continue
            output_values_dict[selector_name][prop_name] = c
    return output_values_dict


def theme(selector, props_obj):
    # type: (str, C) -> Callable[[type[T]], type[T]]
    def decorator(cls):
        # type: (type[T]) -> type[T]
        props_obj.name = selector
        Theme.selectors[selector] = props_obj
        return cls
    return decorator


if TYPE_CHECKING:
    from typing import Callable, TypeVar, TypedDict  # noqa: F401
    T = TypeVar('T')
    ValuesDict = dict[str, dict[str, str]]
    ThemeData = TypedDict(
        'ThemeData',
        {'path': str, 'values': ValuesDict})
