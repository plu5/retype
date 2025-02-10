from qt import QDialog, Qt, QTabWidget, QWidget, QVBoxLayout, QLabel

from typing import TYPE_CHECKING

from retype.resource_handler import getIcon
from retype.constants import (RETYPE_VERSION_STR, RETYPE_REPOSITORY_URL,
                              ACKNOWLEDGEMENTS, RETYPE_BUILDDATE_DESC)
from retype.extras.widgets import ReadOnlyTextWidget


class AboutDialog(QDialog):
    def __init__(self,  # type: AboutDialog
                 commands_info,  # type: CommandsInfo
                 prompt,  # type: str
                 books,  # type: dict[int, BookWrapper] | None
                 parent=None  # type: QWidget | None
                 ):
        # type: (...) -> None
        QDialog.__init__(self, parent, Qt.WindowType.WindowCloseButtonHint)

        self.commands_info = commands_info
        self.prompt = prompt
        self.books = books

        self.setWindowTitle("About retype")
        self.setModal(True)

        self.pages = {}  # type: dict[str, QWidget]
        self.pages['About'] = AboutPage()
        self.pages['Acknowledgements'] = self.acknowledgementsPage()
        self.pages['Console commands'] = self.consoleCommandsPage()
        self.pages['You'] = self.youPage()

        self.tab_widget = QTabWidget()
        for label, page in self.pages.items():
            self.tab_widget.addTab(page, label)

        lyt = QVBoxLayout(self)
        lyt.addWidget(self.tab_widget)

    def acknowledgementsPage(self):
        # type: (AboutDialog) -> ReadOnlyTextWidget
        return ReadOnlyTextWidget(format_page_details(ACKNOWLEDGEMENTS))

    def consoleCommandsPage(self):
        # type: (AboutDialog) -> ReadOnlyTextWidget
        commands = {}  # type: dict[str, str | dict[str, str]]

        for cmd in self.commands_info.values():
            aliases = [f'<tt>{self.prompt}{alias}</tt>'
                       for alias in cmd['aliases']]
            args_str = cmd['args'] or ''
            aliases_str = ' / '.join(aliases)
            aliases_str += ' ' if args_str != '' else ''
            aliases_str += args_str
            commands[aliases_str] = cmd['desc']

        return ReadOnlyTextWidget(format_page_details(commands))

    def youPage(self):
        # type: (AboutDialog) -> ReadOnlyTextWidget
        if not self.books:
            self.books = {}

        books_in_progress = 0
        books_completed = 0
        for book in self.books.values():
            if book.progress == 100:
                books_completed += 1
            elif book.progress > 0:
                books_in_progress += 1

        you = {'# of books': str(len(self.books)),
               '# of books in progress': str(books_in_progress),
               '# of books completed': str(books_completed)}

        return ReadOnlyTextWidget(format_page_details(you))

    def setActivePage(self, title):
        # type: (AboutDialog, str) -> None
        page = self.pages.get(title)
        if page:
            self.tab_widget.setCurrentWidget(page)


class AboutPage(QWidget):
    def __init__(self, parent=None):
        # type: (AboutPage, QWidget | None) -> None
        QWidget.__init__(self, parent)

        lyt = QVBoxLayout(self)

        def makel(text=""):
            # type: (str) -> QLabel
            label = QLabel(text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lyt.addWidget(label)
            return label

        img_l = makel()
        img_l.setPixmap(getIcon('retype').pixmap(400))

        makel(f"Version {RETYPE_VERSION_STR}")
        if (RETYPE_BUILDDATE_DESC != ''):
            makel(RETYPE_BUILDDATE_DESC)

        rep_l = makel(
            f'<a href="{RETYPE_REPOSITORY_URL}">GitHub repository</a>')
        rep_l.setOpenExternalLinks(True)


def format_page_details(details_dict):
    # type: (Mapping[str, str | Mapping[str, str]]) -> str
    def plus_newline(s, amount=1):
        # type: (str, int) -> str
        for i in range(0, amount):
            s += '<br/>'
        return s

    s = ''
    for item, details in details_dict.items():
        s += item
        s += "<blockquote>"
        i = 0
        if isinstance(details, str):
            s += details
        else:
            for title, info in details.items():
                if i > 0:
                    s = plus_newline(s)
                i += 1
                s += f'{title}: '
                if title == 'Web':
                    s += f'<a href="{info}">{info}</a>'
                else:
                    s += info
        s += "</blockquote>"

    return s


if TYPE_CHECKING:
    from retype.extras.metatypes import CommandInfo, CommandsInfo  # noqa: F401
    from retype.controllers.library import BookWrapper  # noqa: F401
    from typing import Mapping  # noqa: F401
