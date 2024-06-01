import os
import logging
from qt import QColor, QObject, pyqtSignal
from tinycss2 import parse_stylesheet, parse_declaration_list

from retype.extras.qss import findSelector, getCValue, serialiseValuesDict

logger = logging.getLogger(__name__)


class ThemeCProp():
    def __init__(self, qss_property, value=None):
        self.used = value is not None
        self.qss_property = qss_property
        self.value = value
        self.c = QColor(value)

    def __call__(self):
        return self.c

    def set_(self, value):
        self.value = value
        self.c = QColor(value)


class C(QObject):
    changed = pyqtSignal()

    def __init__(self, fg=None, bg=None, outline=None, l_border=None,
                 r_border=None, t_border=None, b_border=None, sel=None,
                 sel_bg=None):
        QObject.__init__(self)
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
    selectors = {}
    themes = {}

    def get(selector_name):
        return Theme.selectors.get(selector_name)

    def getValuesDict():
        return selectorsToValuesDict(Theme.selectors)

    def getQss(selector_name=None):
        qss = ''
        values = Theme.getValuesDict()
        if selector_name is None:
            qss = serialiseValuesDict(values)
        else:
            s = values.get(selector_name)
            if s:
                qss = serialiseValuesDict({selector_name: s})
            else:
                logger.warn(f'getQss: Selector name {selector_name} not found')
        return qss

    def set_(values):
        changed_selectors = []
        for name, s in Theme.selectors.items():
            changed = False
            for p in s.props:
                if p.used:
                    new_value = values.get(s.name, {}).get(p.qss_property)
                    p.set_(new_value)
                    changed = True
            if changed:
                changed_selectors.append(s)
        for s in changed_selectors:
            s.changed.emit()


def getThemeValues(name, path):
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
        logger.warn(f'Theme {name} in path {path} not found.')
    return values


def populateThemes(app_path, user_path):
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
    values = {}
    for name, s in selectors.items():
        values[name] = {}
        for p in s.props:
            if p.used:
                values[name][p.qss_property] = p.value
    return values


def valuesFromQss(needed_values_dict, qss):
    ss = parse_stylesheet(qss)
    output_values_dict = {}
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
    def decorator(cls):
        props_obj.name = selector
        Theme.selectors[selector] = props_obj
        return cls
    return decorator
