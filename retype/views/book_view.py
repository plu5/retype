from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton,
                             QTextBrowser)
from PyQt5.QtCore import (pyqtSignal) #
import os #
from resource_handler import getLibraryPath
from views.modeline import Modeline
#from controllers.library import BookWrapper, LibraryController


class BookView(QWidget):
    switchViewSignal = pyqtSignal(int)

    def __init__(self, main_win, library, parent=None):
        super().__init__(parent)
        self._main_win = main_win
        self._library = library
        self._initUI()

    def _initUI(self):
        self.display_text = QTextBrowser(self)

        self.loadBook(1)

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

    def _setContents(self, content):
        try:
            self.display_text.setHtml(str(content, 'utf-8'))
        except IndexError:
            self.display_text.setHtml("No book loaded")

    def loadBook(self, book_name):
        self.book = self._library.loadBook(book_name)
        self._setContents(self.book.chapters[1].content)
