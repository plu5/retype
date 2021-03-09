from PyQt5.Qt import pyqtSignal, QObject

from retype.console import CommandService


class FakeSignal:
    def __init__(self, type_):
        self._reset()

    def connect(self, func):
        pass

    def emit(self, *args):
        self._emitted = args

    def _reset(self):
        self._emitted = None

    @property
    def emitted(self):
        return_value = self._emitted
        self._reset()
        return return_value


class FakeConsole(QObject):
    submitted = pyqtSignal(str)
    switchView = FakeSignal(int)

    def __init__(self):
        QObject.__init__(self)
        self._text = ''

    def text(self):
        return self._text

    def submitText(self, text):
        self._text = text
        self.submitted.emit(text)

    def clear(self):
        self._text = ''


class FakeBookView:
    def __init__(self):
        self._reset()

    def _reset(self):
        self._called = None

    @property
    def called(self):
        return_value = self._called
        self._reset()
        return return_value

    def isVisible(self):
        return True

    def setChapter(self, pos, move=False):
        self._called = ('setChapter', pos, move)

    def nextChapter(self, move=False):
        self._called = ('nextChapter', move)

    def previousChapter(self, move=False):
        self._called = ('previousChapter', move)


def setup():
    console = FakeConsole()
    book_view = FakeBookView()
    service = CommandService(console, book_view, console.switchView, None)
    return (console, book_view, service)


class TestCommandService:
    def test_switch(self):
        (console, _, _) = setup()
        switchView = console.switchView

        console.submitText(">switch main")
        assert switchView.emitted == (1,)

        console.submitText(">switch book")
        assert switchView.emitted == (2,)

        console.submitText(">switch")
        assert switchView.emitted == (1,)

        # Non-supported argument
        console.submitText(">switch nothing")
        assert switchView.emitted is None

        # Too many arguments
        console.submitText(">switch blah book")
        assert switchView.emitted is None

    def test_command_history(self):
        (console, _, service) = setup()

        console.submitText(">switch main")
        assert service.command_history == [">switch main"]

        console.submitText(">switch book")
        assert service.command_history == [">switch main", ">switch book"]

        # Same command again should move it to end
        console.submitText(">switch main")
        assert service.command_history == [">switch book", ">switch main"]

    def test_setChapter(self):
        (console, book_view, _) = setup()

        # No argument
        console.submitText(">chapter")
        assert book_view.called is None

        # Bad argument
        console.submitText(">chapter blah")
        assert book_view.called is None

        console.submitText(">chapter 2")
        assert book_view.called == ('setChapter', 2, False)

        console.submitText(">chapter 34092834 m")
        assert book_view.called == ('setChapter', 34092834, True)
