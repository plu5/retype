from qt import (QDialog, Qt, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
                QLabel, QTextBrowser)

from retype.resource_handler import getIcon
from retype.constants import (RETYPE_VERSION_STR, RETYPE_REPOSITORY_URL,
                              ACKNOWLEDGEMENTS, RETYPE_BUILDDATE_DESC)


class AboutDialog(QDialog):
    def __init__(self, commands_info, prompt, books,
                 parent=None):
        QDialog.__init__(self, parent, Qt.WindowType.WindowCloseButtonHint)

        self.commands_info = commands_info
        self.prompt = prompt
        self.books = books

        self.setWindowTitle("About retype")
        self.setModal(True)

        self.pages = {}
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
        return ReadOnlyTextWidget(format_page_details(ACKNOWLEDGEMENTS))

    def consoleCommandsPage(self):
        commands = {}

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
        books_in_progress = 0
        books_completed = 0
        for book in self.books.values():
            if book.progress is not None:
                books_in_progress += 1
                if book.progress == 100:
                    books_completed += 1

        you = {'# of books': str(len(self.books)),
               '# of books in progress': str(books_in_progress),
               '# of books completed': str(books_completed)}

        return ReadOnlyTextWidget(format_page_details(you))

    def setActivePage(self, title):
        page = self.pages.get(title)
        if page:
            self.tab_widget.setCurrentWidget(page)


class AboutPage(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        lyt = QVBoxLayout(self)

        def makel(text=""):
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


class ReadOnlyTextWidget(QWidget):
    def __init__(self, text="", parent=None):
        QWidget.__init__(self, parent)

        box = QTextBrowser()
        box.setText(text)
        box.setOpenExternalLinks(True)
        lyt = QHBoxLayout(self)
        lyt.addWidget(box)
        lyt.setSpacing(0)
        lyt.setContentsMargins(0, 0, 0, 0)


def format_page_details(details_dict):
    def plus_newline(s, amount=1):
        for i in range(0, amount):
            s += '<br/>'
        return s

    s = ''
    for item, details in details_dict.items():
        s += item
        s += "<blockquote>"
        i = 0
        if isinstance(details, dict):
            for title, info in details.items():
                if i > 0:
                    s = plus_newline(s)
                i += 1
                s += f'{title}: '
                if title == 'Web':
                    s += f'<a href="{info}">{info}</a>'
                else:
                    s += info
        else:
            s += details
        s += "</blockquote>"

    return s
