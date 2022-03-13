import sys
import logging
import argparse
from qt import QApplication

from retype.controllers import MainController


_logging_levels = logging._levelToName  # FIXME: bad
_logging_levels_names = [n for n in _logging_levels.values()]


def run():
    app = QApplication(sys.argv)

    args = _parseArgs()
    _configLog(args.loglevel[0])

    controller = MainController()
    controller.show()
    sys.exit(app.exec())


def _parseArgs():
    parser = argparse.ArgumentParser(description='retype')
    parser.add_argument(
        '-l', '--loglevel', type=str, nargs=1, metavar='LOGLEVEL',
        default=['WARNING'], choices=_logging_levels_names,
        help=f'Set logging output level to one of:\
 {", ".join(_logging_levels_names)}')
    return parser.parse_args()


def _configLog(level):
    logging.basicConfig(
        format='{asctime}.{msecs:.0f} [{name}] {levelname}: {message}',
        level=level, style='{', datefmt='%H:%M:%S')


if __name__ == '__main__':
    run()
