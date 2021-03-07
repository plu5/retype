import logging
from PyQt5.Qt import QWidget, QVBoxLayout

from retype.layouts import ShelvesWidget
from retype.ui import Cover

logger = logging.getLogger(__name__)


class ShelfView(QWidget):
    def __init__(self, main_win, main_controller, parent=None):
        super().__init__(parent)
        self._controller = main_controller
        self._library = self._controller._library
        self._initUI()
        self._populate()

    def _initUI(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.shelves = ShelvesWidget(self, 130, 225)
        self.shelves.setContentsMargins(0, 5, 5, 0)
        self.layout.addWidget(self.shelves)

    def _populate(self):
        for book in self._library._book_list:
            book_wrapper = self._library._instantiateBook(book)
            loadBook = self._controller.console.loadBook
            item = ShelfItem(book_wrapper, loadBook)
            self.shelves.addWidget(item)

    def keyPressEvent(self, e):
        self._controller.console.transferFocus(e)
        QWidget.keyPressEvent(self, e)


class ShelfItem(QWidget):
    """"""
    def __init__(self, book, loadBook, parent=None):
        super().__init__(parent)
        self.book = book
        self.cover = Cover(book, self)
        self.loadBook = loadBook
        self._initUI()

    def _initUI(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.layout.addWidget(self.cover)

    def mouseReleaseEvent(self, e):
        self.loadBook.emit(self.book.idn)
