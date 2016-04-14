import sys
from PyQt5.QtWidgets import QApplication
from views import MainWin
from controllers.main_controller import MainController
from resource_handler import getIcon


def run():
    app = QApplication(sys.argv)
    controller = _createController()
    controller.show()
    sys.exit(app.exec_())


def _createController():
    window = MainWin()
    #view = ShelfView() #
    return MainController(window)


if __name__ == '__main__':
    run()
