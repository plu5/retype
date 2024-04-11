import os
import sys
from qt import QIcon


def __getRoot():
    root = ''
    if getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS'):
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
temp_path_or_none = sys._MEIPASS if hasattr(sys, '_MEIPASS') else None


def getLibraryPath():
    return os.path.join(root_path, 'library')


def getStylePath(user_dir=None):
    return os.path.join(user_dir if user_dir else root_path, 'style')


def getIconsPath():
    return os.path.join(getStylePath(), 'icons')


def getIcon(icon_name, extension='png'):
    return QIcon(os.path.join(getIconsPath(), icon_name + f'.{extension}'))


def getIncludePath():
    root = temp_path_or_none or root_path
    if os.path.split(root)[1] == 'include':
        root = os.path.abspath(os.path.join(root, '..'))
    return os.path.join(root, 'include')
