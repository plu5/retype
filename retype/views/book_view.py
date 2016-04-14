from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton,
                             QTextBrowser)
from PyQt5.QtCore import (pyqtSignal) #
import os #
from resource_handler import getLibraryPath
from views.modeline import Modeline
from controllers.library import BookWrapper


class BookView(QWidget):
    switchViewSignal = pyqtSignal(int)

    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self._initUI()

    def _initUI(self):
        self.display_text = QTextBrowser(self)
        self.bookwrapper = BookWrapper('/cygdrive/b/google~1/dev/'
                                       'retype/library/test.epub')
        self.display_text.setHtml(str(self.bookwrapper.chapters[1].content, 'utf-8')) #  should probably be a function to do this more easily, wrapped with try except

        self._initModeline()

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.display_text)
        self.layout.addWidget(self.modeline)
        self.setLayout(self.layout)

    def switchShelfView(self):
        self.switchViewSignal.emit(1)

    def _initModeline(self):
        self.modeline = Modeline(self)
        self.modeline.setTitle('Testing')

    def _updateModeline(self):  # not _?
        pass
