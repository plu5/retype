from PyQt5.Qt import pyqtSignal, QObject

from retype.console import CommandService


class FakeConsole(QObject):
    submitted = pyqtSignal(str)
    fakeSwitch = pyqtSignal(int)

    def __init__(self):
        QObject.__init__(self)
        self._text = ''

    def text(self):
        return self._text

    def setText(self, text):
        self._text = text
        self.submitted.emit(text)

    def clear(self):
        self._text = ''


class TestCommandService:
    def test_command_history(self):
        console = FakeConsole()
        service = CommandService(console, None, console.fakeSwitch)

        console.setText(">switchmain")
        assert service.command_history == [">switchmain"]

        console.setText(">switchbook")
        assert service.command_history == [">switchmain", ">switchbook"]

        # Same command again should move it to end
        console.setText(">switchmain")
        assert service.command_history == [">switchbook", ">switchmain"]
