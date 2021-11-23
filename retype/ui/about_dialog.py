from PyQt5.Qt import (QDialog, Qt, QTabWidget, QWidget, QVBoxLayout,
                      QHBoxLayout, QLabel, QTextBrowser)

from retype.resource_handler import getIcon
from retype.constants import (RETYPE_VERSION_STR, RETYPE_REPOSITORY_URL,
                              ACKNOWLEDGEMENTS)


class AboutDialog(QDialog):
    def __init__(self, commands_info, prompt, books,
                 parent=None):
        QDialog.__init__(self, parent, Qt.WindowCloseButtonHint)

        self.commands_info = commands_info
        self.prompt = prompt
        self.books = books

        self.setWindowTitle("About retype")
        self.setModal(True)

        pages = {}
        pages['About'] = AboutPage()
        pages['Acknowledgements'] = self.acknowledgementsPage()
        pages['Console commands'] = self.consoleCommandsPage()
        pages['You'] = self.youPage()

        tabw = QTabWidget()
        for label, page in pages.items():
            tabw.addTab(page, label)

        lyt = QVBoxLayout(self)
        lyt.addWidget(tabw)

    def acknowledgementsPage(self):
        return ReadOnlyTextWidget(format_page_details(ACKNOWLEDGEMENTS))

    def consoleCommandsPage(self):
        commands = {}

        for desc, obj in self.commands_info.items():
            aliases = [f'<tt>{self.prompt}{alias}</tt>'
                       for alias in obj['aliases']]
            aliases_str = ' / '.join(aliases)
            commands[aliases_str] = desc

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


class AboutPage(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        lyt = QVBoxLayout(self)

        def makel(text=""):
            label = QLabel(text)
            label.setAlignment(Qt.AlignCenter)
            lyt.addWidget(label)
            return label

        img_l = makel()
        img_l.setPixmap(getIcon('retype').pixmap(400))

        makel(f"Version {RETYPE_VERSION_STR}")

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
