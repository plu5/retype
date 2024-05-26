import os
import logging


logger = logging.getLogger(__name__)


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

    def setIconSet(name='0_default'):
        if name in Icons.icon_sets:
            path = Icons.icon_sets[name]
            for icon in Icons.icons:
                p = os.path.join(path, icon)
                if os.path.exists(p):
                    Icons.icons[icon] = p
        else:
            logger.warn(f'Unknown icon set \'{name}\'')

    def populateSets(paths):
        populateIconSets(paths)


def populateIconSets(paths):
    Icons.icon_sets = {}
    for path in paths:
        for root, dirs, _ in os.walk(path):
            for d in dirs:
                if d not in Icons.icon_sets:
                    Icons.icon_sets[d] = os.path.join(root, d)
            break  # do not recurse
