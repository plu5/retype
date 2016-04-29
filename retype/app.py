import sys, logging
from PyQt5.QtWidgets import QApplication
from ui import MainWin
from controllers.main_controller import MainController
from resource_handler import getIcon


def run():
    app = QApplication(sys.argv)
    _configLog(0)
    controller = _createController()
    controller.show()
    sys.exit(app.exec_())


def _createController():
    window = MainWin()
    #view = ShelfView() #
    return MainController(window)

def _configLog(level):
    logging.basicConfig(
        format='{asctime}.{msecs:.0f} [{name}] {levelname}: {message}',
        level=level, style='{', datefmt='%H:%M:%S')

if __name__ == '__main__':
    run()
