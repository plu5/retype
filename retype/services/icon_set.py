import os
import logging


logger = logging.getLogger(__name__)

DEFAULT_SET_NAME = '0_default'


class Icons:
    icons = {'about.png': '', 'arrow-left.png': '', 'arrow-right.png': '',
             'console.png': '', 'cursor.png': '', 'customise.png': '',
             'documentation.png': '', 'door.png': '', 'issue.png': '',
             'open_book.png': '', 'retype.ico': '', 'retype.png': '',
             'shelf_view.png': '', 'skip.png': '', 't-down.png': '',
             't-up.png': '', 'typespeed.png': '', 'steno.png': ''}
    icon_sets = {}

    def getIconPath(name):
        p = Icons.icons.get(name, '')
        if p == '':
            logger.warn(f'Icon \'{name}\' not set')
        return p

    def setIconSet(name=DEFAULT_SET_NAME, path=None):
        if path or name in Icons.icon_sets:
            path = path or Icons.icon_sets[name]
            for icon in Icons.icons:
                p = os.path.join(path, icon)
                if os.path.exists(p):
                    Icons.icons[icon] = p
        else:
            logger.warn(f'Unknown icon set \'{name}\'')

    def populateSets(path, fallback):
        populateIconSets(path, fallback)


def populateIconSets(app_path, user_path):
    Icons.icon_sets = {}
    paths = [app_path, user_path] if app_path != user_path else [app_path]
    for path in paths:
        for root, dirs, _ in os.walk(path):
            for d in dirs:
                key = d
                if key in Icons.icon_sets and path == user_path:
                    key = d + ' (user dir)'
                Icons.icon_sets[key] = os.path.join(root, d)
            break  # do not recurse
    Icons.setIconSet(path=os.path.join(app_path, DEFAULT_SET_NAME))
