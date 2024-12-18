import sys
import logging
import argparse
from qt import QApplication

from retype.controllers import MainController
from retype.constants import RETYPE_VERSION_STR as version
from retype.constants import RETYPE_BUILDDATE_DESC, ismacos


_logging_levels = logging._levelToName  # FIXME: bad
_logging_levels_names = [n for n in _logging_levels.values()]


def run():
    app = QApplication(sys.argv)

    # MacOS Qt5 bug workaround https://forum.qt.io/post/613499
    if ismacos:
        app.setStyle('Fusion')

    ver_str = f'retype {version}' + RETYPE_BUILDDATE_DESC

    args = _parseArgs(ver_str)
    _configLog(args.loglevel[0])

    logging.info(ver_str)

    controller = MainController()
    controller.show()
    sys.exit(app.exec())


def _parseArgs(desc):
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        '-l', '--loglevel', type=str, nargs=1, metavar='LOGLEVEL',
        default=['INFO'], choices=_logging_levels_names,
        help=f'Set logging output level to one of:\
 {", ".join(_logging_levels_names)}')
    return parser.parse_args()


def _configLog(level):
    logging.basicConfig(
        format='{asctime}.{msecs:.0f} [{name}] {levelname}: {message}',
        level=level, style='{', datefmt='%H:%M:%S')
    # Turn third-party warnings into DEBUG-level logs
    logging.captureWarnings(True)
    logging.getLogger('py.warnings').addFilter(
        lambda record: logging.getLevelName(level) == logging.DEBUG)


if __name__ == '__main__':
    run()
