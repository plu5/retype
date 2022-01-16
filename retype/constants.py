from sys import version as PYTHON_VERSION_STR
from PyQt6.sip import SIP_VERSION_STR
from ebooklib import VERSION as EBOOKLIB_VERSION
from qt import QT_VERSION_STR, PYQT_VERSION_STR, QT_WRAPPER

from retype.resource_handler import root_path, getLibraryPath


default_config = {
    "user_dir": root_path,
    "library_paths": [getLibraryPath()],
    "prompt": ">",
    "rdict": {
        "\ufffc": [" "],
        "\u00ae": ["r", "R"],
        "\u00a9": ["c", "C"],
        "\u201c": ["\""],
        "\u201d": ["\""],
        "\u2018": ["'"],
        "\u2019": ["'"],
        "\u2013": ["-"],
        "\u2014": ["-"]
    },
    "bookview": {
        "save_font_size_on_quit": True,
        "font_size": 12
    },
    "window": {
        "x": None,
        "y": None,
        "w": 600,
        "h": 600,
        "save_on_quit": True,
        "save_splitters_on_quit": True
    }
}


RETYPE_VERSION_STR = "1.0.0"


RETYPE_REPOSITORY_URL = "https://www.github.com/plu5/retype"


RETYPE_ISSUE_TRACKER_URL = "https://www.github.com/plu5/retype/issues"


RETYPE_DOCUMENTATION_URL = "https://www.github.com/plu5/retype/wiki"


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
