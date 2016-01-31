import sys
from PyQt5.QtWidgets import (QPushButton, QMainWindow, QApplication, QWidget,
                             QDialog, QStackedWidget, QLineEdit, QHBoxLayout,
                             QVBoxLayout, QLabel, qApp, QAction, QTextBrowser,
                             QTextEdit)
from PyQt5.QtCore import Qt, QUrl#, QString
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor
from ebooklib import epub
import ebooklib

book = epub.read_epub('test.epub')
chapters = []
title = book.title
for document in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
    #print(document.content)
    chapters.append(document)
#print(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
#print(chapters[0].content)


class Main(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        global console

        console = QLineEdit(self)
        console.setStyleSheet("background-color: #BEBEBE; color: #333; border: 1px outset; border-color: #4A4A4A white white; selection-background-color: white; selection-color: #333")
        console.textChanged.connect(handleEntry)
        console.returnPressed.connect(handleEntryReturn)

        self.stacked = QStackedWidget()
        self.consistentLayout = QVBoxLayout()
        self.consistentLayout.setContentsMargins(0, 0, 0, 0)
        self.consistentLayout.addWidget(self.stacked)
        self.consistentLayout.addWidget(console)
        mainWidget = QWidget()
        mainWidget.setLayout(self.consistentLayout)
        self.switchBookView() #

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&file')
        exitAction = QAction('&exit', self)
        exitAction.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAction)
        switchMenu = menubar.addMenu('&switch')
        switchMainAction = QAction('&Main Menu', self)
        switchMainAction.triggered.connect(self.switchMainView)
        switchMenu.addAction(switchMainAction)
        switchBookAction = QAction('&Book1', self)
        switchBookAction.triggered.connect(self.switchBookView)
        switchMenu.addAction(switchBookAction)
        helpMenu = menubar.addMenu('&help')
        # menubar.setStyleSheet("border-bottom: 1px outset white")
        # fileMenu.setStyleSheet("background: black;")
        # i need to set these in a stylesheet for it to work. QMenuBar::item
        # these menus are temporary

        self.setCentralWidget(mainWidget)
        self.setGeometry(100, 300, 800, 600)
        self.setWindowTitle('retype')

    def switchMainView(self):
        mainView = MainView(self)
        self.stacked.addWidget(mainView)
        self.stacked.setCurrentWidget(mainView)

    def switchBookView(self):
        bookView = BookView(self)
        self.stacked.addWidget(bookView)
        self.stacked.setCurrentWidget(bookView)


class MainView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout()
        self.label = QLabel('Main View', self)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)


class BookView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        global tobetyped
        tobetyped = "text to be typed"
        self.testtextedit = QTextEdit(self)
        begin = 2
        end = 5
        fmt = QTextCharFormat()
        fmt.setBackground(QColor('yellow'))
        cursor = QTextCursor()
        cursor.setPosition(begin, cursor.MoveAnchor)
        cursor.setCharFormat(fmt)
        
        self.displayText = QTextBrowser(self)
        self.displayText.setStyleSheet("background-color: #F6F1DE; border: 1px outset white; font-family: Iowan Old Style, Courier New; selection-background-color: grey; font-size: 13px")
        #self.displayText.setHtml(str(chapters[1].content))
        #self.displayText.setSource(QUrl('file:test/OEBPS/fm01.html'))
        #self.displayText.setSource(QUrl('file:test/OEBPS/bm02.html'))
        #self.displayText.setHtml("<b>text</b> to be typed ‘’ “” –—…—\r\ntest <p>\r\ntest2</p>")
        # chapters[1].content gives ‘unexpected type 'bytes'’
        self.displayText.setHtml(str(chapters[1].content, 'utf-8')) # AH!
        #print(chapters[1].content)

        self.modeLine = QLabel("this will be the modeline", self)
        self.modeLine.setStyleSheet("background-color: #DFD8CA; font-family: Courier New, Consolas; border: 1px outset #847250;")

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.displayText)
        self.layout.addWidget(self.modeLine)
        self.setLayout(self.layout)
        
def handleEntry():
    #print(console.text())
    # entry = console.text()
    # for index, c in enumerate(entry):
    #     if entry[index] == tobetyped[index]
    return
# i guess this really needs to be in bookview to work. does it?


def handleEntryReturn():
    entry = console.text()

    if entry[0] == ">":
        if entry == '>switch.main': # make it case-insensitive
            retype.switchMainView()
        if entry == '>switch.book1':
            retype.switchBookView()
        console.setText('')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    retype = Main()
    retype.show()
    sys.exit(app.exec_())
