import sys
import logging
from qt import QApplication

from retype.controllers import MainController


def run():
    app = QApplication(sys.argv)
    _configLog(0)
    controller = MainController()
    controller.show()
    sys.exit(app.exec())


def _configLog(level):
    logging.basicConfig(
        format='{asctime}.{msecs:.0f} [{name}] {levelname}: {message}',
        level=level, style='{', datefmt='%H:%M:%S')


if __name__ == '__main__':
    run()
