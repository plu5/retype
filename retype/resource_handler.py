# i think there may be problems with this implementation when it’s packaged

import os
import sys
from qt import QIcon


def __getRoot():
    root = ''
    if sys.argv[0].lower().endswith('.exe'):
        root = os.path.dirname(sys.argv[0])
    elif getattr(sys, 'frozen', False):
        root = os.environ['RESOURCEPATH']
    else:
        file = None
        try:
            file = __file__
        except NameError:
            file = sys.argv[0]
        root = os.path.dirname(os.path.abspath(file))
    return os.path.abspath((os.path.join(root, '..')))


root_path = __getRoot()


def getLibraryPath():
    return os.path.join(root_path, 'library')


def getStylePath():
    return os.path.join(root_path, 'style')


def getIconsPath():
    return os.path.join(root_path, 'retype/icons')


def getIcon(icon_name, extension='png'):
    return QIcon(os.path.join(getIconsPath(), icon_name + f'.{extension}'))
