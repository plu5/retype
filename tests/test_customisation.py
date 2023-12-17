import sys
from qt import pyqtSignal, QObject, QApplication
from retype.ui import CustomisationDialog
from retype.constants import default_config


class FakeWindow(QObject):
    closing = pyqtSignal()


# This is here to be able to use CustomisationDialog, as without a
#  QApplication Qt doesn’t let you instantiate QWidgets.
app = QApplication(sys.argv)


def _setup():
    dialog = CustomisationDialog(default_config, FakeWindow(), *[None]*3)
    return dialog


class TestCustomisation:
    def test_auto_newline_default_value(self):
        dialog = _setup()
        key = 'auto_newline'
        assert (dialog.selectors[key].isChecked() == default_config[key])

    def test_auto_newline_check_uncheck(self):
        dialog = CustomisationDialog(default_config, FakeWindow(),
                                     None, None, None)
        key = 'auto_newline'

        dialog.selectors[key].set_(True)
        assert dialog.selectors[key].isChecked() is True
        assert dialog.config_edited[key] is True

        dialog.selectors[key].set_(False)
        assert dialog.selectors[key].isChecked() is False
        assert dialog.config_edited[key] is False
