import sys
import logging
from PyQt5.QtWidgets import QApplication

from retype.controllers.main_controller import MainController
from retype.resource_handler import getIcon


def run():
    app = QApplication(sys.argv)
    _configLog(0)
    controller = MainController()
    controller.show()
    sys.exit(app.exec_())

def _configLog(level):
    logging.basicConfig(
        format='{asctime}.{msecs:.0f} [{name}] {levelname}: {message}',
        level=level, style='{', datefmt='%H:%M:%S')

if __name__ == '__main__':
    run()
