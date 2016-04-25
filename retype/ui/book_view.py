from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton,
                             QTextBrowser)
from PyQt5.QtGui import (QTextCursor, QTextCharFormat, QColor)
from ui.modeline import Modeline


class BookView(QWidget):
    def __init__(self, main_win, main_controller, parent=None):
        super().__init__(parent)
        self._main_win = main_win
        self._controller = main_controller
        self._library = self._controller._library
        self._initUI()
        self._initHighlighting()

    def _initUI(self):
        self.display_text = QTextBrowser(self)

        self._initModeline()

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.display_text)
        self.layout.addWidget(self.modeline)
        self.setLayout(self.layout)

    def _initModeline(self):
        self.modeline = Modeline(self)
        self.modeline.setTitle('Testing')

    def _updateModeline(self):  # not _?
        pass

    def _initHighlighting(self):  # bad name
        self.cursor_pos = 0
        self.line_pos = 0
        self.persistent_pos = 0
        self.current_sentence = ''  #
        # self._cleanText()
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor('yellow'))
        self.unhighlight_format = QTextCharFormat()  # temp
        self.unhighlight_format.setBackground(QColor('white'))  #
        self.cursor = QTextCursor(self.display_text.document())
        self.cursor.setPosition(self.cursor_pos, self.cursor.KeepAnchor)

    def setContents(self, content):
        try:
            self.display_text.setHtml(str(content, 'utf-8'))
            self._initHighlighting()  # cursor has to be reinstantiated
            self._cleanText()
        except IndexError:
            self.display_text.setHtml("No book loaded")

    def _cleanText(self):  # bad name
        to_be_typed_raw = self.display_text.toPlainText()
        # replacements (do this better)
        to_be_typed_raw = to_be_typed_raw.replace('\ufffc', ' ')
        self.to_be_typed_list = to_be_typed_raw.splitlines()
        self.setSentence(self.line_pos)

    def setSentence(self, pos):
        self.current_sentence = self.to_be_typed_list[pos]
