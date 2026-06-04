from qt import pyqtSignal, QObject
from unittest.mock import patch, MagicMock

from retype.ui import BookView


class FakeBook:
    chapters = [{'html': 'waeofiaw', 'plain': 'waeofiaw', 'images': []}]*5
    title = 'wefoiw'
    path = 'awoeifjawei'


class PartiallyFakeBookView(BookView):
    @patch('retype.ui.book_view.BookDisplay')
    @patch('retype.ui.book_view.QTextCursor')
    @patch('retype.ui.book_view.keymapUpdate')
    @patch('retype.ui.book_view.Keymap')
    def __init__(self, win, ctrlr, *_):
        self.modeline = MagicMock()
        super().__init__(win, ctrlr)
        self._reset()
        self.book = FakeBook()
        self.tobetypedlist = ['abcdef']*5
        self.chapter_pos = 0

    def _initUI(self):
        pass

    def setCursor(self):
        pass

    def updateToolbarActions(self):
        pass

    def _reset(self):
        self._called = None

    @property
    def called(self):
        return_value = self._called
        self._reset()
        return return_value

    def setChapter(self, pos, move_cursor=False, reset=True):
        self._called = ('setChapter', pos, move_cursor, reset)
        super().setChapter(pos, move_cursor, reset)


class FakeWin(QObject):
    closing = pyqtSignal()

    def denoteSplitter(*_):
        pass

    def maybeRestoreSplitterState(*_):
        pass


class FakeConsole:
    def transferFocus():
        pass


class FakeController:
    library = None
    console = FakeConsole()


def _setup():
    return PartiallyFakeBookView(FakeWin(), FakeController())


class TestBookView:
    def test_setChapterAction(self):
        book_view = _setup()

        # No argument
        book_view.setChapterAction()
        assert book_view.called is None

        # Bad argument
        book_view.setChapterAction('blah')
        assert book_view.called is None

        book_view.setChapterAction('2')
        assert book_view.called == ('setChapter', 2, False, True)

        book_view.setChapterAction('34092834', 'm')
        assert book_view.called == ('setChapter', 34092834, True, True)

    def test_setChapterNegativeValues(self):
        book_view = _setup()

        # Negative
        book_view.setChapter(-1, move_cursor=True)
        assert book_view.chapter_pos == len(book_view.book.chapters) - 1

        # Large negative
        book_view.setChapter(
            0 - len(book_view.book.chapters) - 23094823, move_cursor=True)
        # Should not have changed bc it's out of range
        assert book_view.chapter_pos == len(book_view.book.chapters) - 1

        # 0
        book_view.setChapter(0, move_cursor=True)
        assert book_view.chapter_pos == 0
