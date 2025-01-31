import os
import sys
from qt import QIcon

from retype.services.icon_set import Icons


_frozen = getattr(sys, 'frozen', False)  # type: ignore[misc]
_meipass = getattr(sys, '_MEIPASS', False)  # type: ignore[misc]


def __getRoot():
    # type: () -> str
    root = ''
    if _frozen or _meipass:  # type: ignore[misc]
        root = os.path.dirname(sys.executable)
    else:
        file = None
        try:
            file = __file__
        except NameError:
            file = sys.argv[0]
        root = os.path.join(os.path.dirname(os.path.abspath(file)), '..')
    return os.path.abspath(root)


root_path = __getRoot()
temp_path_or_none = str(_meipass) if _meipass else None  # type: ignore[misc]


def getLibraryPath():
    # type: () -> str
    return os.path.join(root_path, 'library')


def getStylePath(user_dir=None):
    # type: (str | None) -> str
    return os.path.join(user_dir if user_dir else root_path, 'style')


def getIconsPath(user_dir=None):
    # type: (str | None) -> str
    return os.path.join(getStylePath(user_dir), 'icons')


def getIcon(icon_name, extension='png'):
    # type: (str, str) -> QIcon
    return QIcon(Icons.getIconPath(f'{icon_name}.{extension}'))


def getTypespeedWordsPath(user_dir=None):
    # type: (str | None) -> str
    return os.path.join(getStylePath(user_dir), 'typespeed_words')


def getIncludePath():
    # type: () -> str
    root = temp_path_or_none or root_path
    if os.path.split(root)[1] == 'include':
        root = os.path.abspath(os.path.join(root, '..'))
    return os.path.join(root, 'include')
