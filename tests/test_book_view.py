from qt import pyqtSignal, QObject

from retype.ui import BookView


class PartiallyFakeBookView(BookView):
    def __init__(self, *args):
        super().__init__(*args)
        self._reset()

    def _reset(self):
        self._called = None

    @property
    def called(self):
        return_value = self._called
        self._reset()
        return return_value

    def setChapter(self, pos, move_cursor=False, reset=True):
        self._called = ('setChapter', pos, move_cursor, reset)


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
