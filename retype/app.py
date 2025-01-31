import sys
import logging
import argparse
from qt import QApplication

from retype.controllers import MainController
from retype.constants import RETYPE_VERSION_STR as version
from retype.constants import RETYPE_BUILDDATE_DESC, ismacos
from retype.extras.log import level_names, default_level, configLog


def run():
    # type: () -> None
    app = QApplication(sys.argv)

    # MacOS Qt5 bug workaround https://forum.qt.io/post/613499
    if ismacos:
        app.setStyle('Fusion')

    ver_str = f'retype {version}' + RETYPE_BUILDDATE_DESC

    args = _parseArgs(ver_str)
    configLog(args.loglevel[0])  # type: ignore[misc]

    logging.info(ver_str)

    controller = MainController()
    controller.show()
    sys.exit(app.exec())


def _parseArgs(desc):
    # type: (str) -> argparse.Namespace
    parser = argparse.ArgumentParser(description=desc)
    default_loglevel = [default_level]
    parser.add_argument(
        '-l', '--loglevel', type=str, nargs=1, metavar='LOGLEVEL',
        default=default_loglevel, choices=level_names,
        help=f'Set logging output level to one of:\
 {", ".join(level_names)}')
    return parser.parse_args()


if __name__ == '__main__':
    run()
