import os
import sys
from sys import version as PYTHON_VERSION_STR
from sys import platform
from ebooklib import VERSION as EBOOKLIB_VERSION
from qt import QT_VERSION_STR, PYQT_VERSION_STR, QT_WRAPPER, sip

from typing import TYPE_CHECKING

from retype.resource_handler import root_path, getLibraryPath, getIncludePath
from retype import __version__


iswindows = platform.lower() in ['win32', 'win64']
ismacos = 'darwin' in platform.lower()

default_steno_kdict = {
    'S': ['A', 'Q'], 'K': ['S'], 'W': ['D'], 'R': ['F'],
    '-R': ['J'], '-B': ['K'], '-G': ['L'], '-S': [';'], '-Z': ["'"],
    'T': ['W'], 'P': ['E'], 'H': ['R'],
    '-F': ['U'], '-P': ['I'], '-L': ['O'], '-T': ['P'], '-D': ['['],
    'A': ['C'], 'O': ['V'], 'E': ['N'], 'U': ['M'],
    '*': ['G', 'H', 'T', 'Y']
}

default_font_family = 'Georgia'
default_font_size = 16

default_config = {
    "user_dir": root_path,
    "library_paths": [getLibraryPath()],
    "icon_set": "0_default",
    "prompt": ">",
    "console_font": "Default",
    "sdict": {
        '\r\n': {'keep': False},
        '\n': {'keep': False},
        '\r': {'keep': False},
        '\v': {'keep': False},
        '\f': {'keep': False},
        '\x1c': {'keep': False},
        '\x1d': {'keep': False},
        '\x1e': {'keep': False},
        '\x85': {'keep': False},
        '\u2028': {'keep': False},
        '\u2029': {'keep': False},
        '. ': {'keep': True},
        '。': {'keep': True}
    },
    "rdict": {
        "\ufffc": [" "],
        "\u00ae": ["r", "R"],
        "\u00a9": ["c", "C"],
        "\u201c": ["\""],
        "\u201d": ["\""],
        "\u2018": ["'"],
        "\u2019": ["'"],
        "\u2032": ["'"],
        "\u2013": ["-"],
        "\u2014": ["-"],
        "\u00f2": ["o"],
        "\u00b0": ["o"]
    },
    "bookview": {
        "save_font_size_on_quit": True,
        "font_size": default_font_size,
        "font": default_font_family
    },
    "window": {
        "x": None,
        "y": None,
        "w": 600,
        "h": 600,
        "save_on_quit": True,
        "save_splitters_on_quit": True
    },
    "auto_newline": True,
    "steno": {
        "kdict": default_steno_kdict
    }
}  # type: Config

if iswindows:
    default_config["hide_sysconsole"] = True


SIP_VERSION_STR = sip.SIP_VERSION_STR

ACKNOWLEDGEMENTS = {
    'Python':
    {
        'Version': PYTHON_VERSION_STR,
        'Organisation': 'Python Software Foundation',
        'Web': 'https://www.python.org/'
    },
    'Qt':
    {
        'Version': QT_VERSION_STR,
        'Company': 'Qt Group',
        'Web': 'https://www.qt.io/'
    },
    f'{QT_WRAPPER}':
    {
        'Version': PYQT_VERSION_STR,
        'Company': 'Riverbank Computing',
        'Web': 'https://riverbankcomputing.com/software/pyqt'
    },
    'SIP':
    {
        'Version': SIP_VERSION_STR,
        'Company': 'Riverbank Computing',
        'Web': 'https://riverbankcomputing.com/software/sip'
    },
    'ebooklib':
    {
        'Version': '.'.join(str(i) for i in EBOOKLIB_VERSION),
        'Author': 'Aleksandar Erkalovic',
        'Web': 'https://github.com/aerkalov/ebooklib'
    }
}


def getBuilddate():
    # type: () -> str | None
    builddate = None
    if not getattr(sys, 'frozen', False) and not hasattr(  # type: ignore[misc]
            sys, '_MEIPASS'):
        return builddate
    path = os.path.join(getIncludePath(), 'builddate.txt')
    if os.path.exists(path):
        with open(path, 'r') as f:
            builddate = f.read()
    return builddate


RETYPE_VERSION_STR = __version__
RETYPE_BUILDDATE_STR = getBuilddate()
RETYPE_BUILDDATE_DESC = f' built @ {RETYPE_BUILDDATE_STR}' \
    if RETYPE_BUILDDATE_STR else ''
RETYPE_REPOSITORY_URL = "https://www.github.com/plu5/retype"
RETYPE_ISSUE_TRACKER_URL = "https://www.github.com/plu5/retype/issues"
RETYPE_DOCUMENTATION_URL = "https://retype.readthedocs.io/"


if TYPE_CHECKING:
    from retype.extras.metatypes import Config  # noqa: F401
