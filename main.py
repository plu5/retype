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
        global console # unnecessary? only at the beginning of functions?

        console = QLineEdit(self)
        console.setAccessibleName("console")
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
        optionsMenu = menubar.addMenu('&options')
        optionsCustomiseAction = QAction('&customise retype', self)
        optionsMenu.addAction(optionsCustomiseAction)
        switchMenu = menubar.addMenu('&switch')
        switchMainAction = QAction('&Main Menu', self)
        switchMainAction.triggered.connect(self.switchMainView)
        switchMenu.addAction(switchMainAction)
        switchBookAction = QAction('&Book1', self)
        switchBookAction.triggered.connect(self.switchBookView)
        switchMenu.addAction(switchBookAction)
        helpMenu = menubar.addMenu('&help')
        # i need to set these in a stylesheet for it to work. QMenuBar::item
        # these menus are temporary

        self.setCentralWidget(mainWidget)
        self.setGeometry(-900, 300, 800, 600)
        self.setStyleSheet(qss_file)
        self.setWindowTitle('retype')

    def switchMainView(self):
        global isbookview
        mainView = MainView(self)
        self.stacked.addWidget(mainView)
        self.stacked.setCurrentWidget(mainView)
        isbookview = 0

    def switchBookView(self):
        global isbookview
        bookView = BookView(self)
        self.stacked.addWidget(bookView)
        self.stacked.setCurrentWidget(bookView)
        isbookview = 1


class MainView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout()
        self.label = QLabel('Main View', self)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)


class BookView(QWidget):
    end = 0
    cursor = 0
    highlight = 0
    unhighlight = 0
    debug = 0
    tobetyped = 0
    cursorPos = 0
    def __init__(self, parent=None):
        super().__init__(parent)

        #global tobetyped
        BookView.tobetyped = "text to be typed" # <i>text</i>
        
        self.displayText = QTextBrowser(self)
        #self.displayText.setHtml(str(chapters[1].content))
        #self.displayText.setSource(QUrl('file:test/OEBPS/fm01.html'))
        #self.displayText.setSource(QUrl('file:test/OEBPS/bm02.html'))
        #self.displayText.setHtml("<b>text</b> to be typed ‘’ “” –—…—\r\ntest <p>\r\ntest2</p>")
        # chapters[1].content gives ‘unexpected type 'bytes'’
        self.displayText.setHtml(str(chapters[1].content, 'utf-8')) # AH!
        #print(chapters[1].content)
        #self.displayText.setHtml(BookView.tobetyped)

        BookView.highlight = QTextCharFormat()
        BookView.highlight.setBackground(QColor('yellow'))
        BookView.unhighlight = QTextCharFormat()
        BookView.unhighlight.setBackground(QColor(246, 241, 222)) #
        #BookView.unhighlight.clearBackground()
        BookView.debug = QTextCharFormat()
        BookView.debug.setBackground(QColor('red'))
        #global cursor #
        BookView.cursor = QTextCursor(self.displayText.document())
        #BookView.cursor.setPosition(0, BookView.cursor.MoveAnchor)
        BookView.cursor.movePosition(0)
        BookView.cursor.movePosition(4, BookView.cursor.KeepAnchor)
        BookView.cursor.setCharFormat(BookView.debug)
        #BookView.cursor.setPosition(10, BookView.cursor.KeepAnchor)
        #BookView.cursor.setCharFormat(BookView.highlight)
        
        self.modeline = QLabel("this will be the modeline", self)
        self.modeline.setAccessibleName("modeline")

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.displayText)
        self.layout.addWidget(self.modeline)
        self.setLayout(self.layout)

        
def handleEntry(): # get where it’s been called from
    global isbookview
    #global console
    #global bookView
    #print(console.text())
    # entry = console.text()
    # for index, c in enumerate(entry):
    #     if entry[index] == tobetyped[index]

    #bookView.cursor.setPosition(10, cursor.KeepAnchor)
    #bookView.cursor.setCharFormat(highlight)
    #print(bookView.end) # name 'bookView' is not defined
    if isbookview:
            #self.cursor.setPosition(10, cursor.KeepAnchor)
            #self.cursor.setCharFormat(highlight)
        #print(BookView.end)
        #for index, c in enumerate(BookView.tobetyped):
            # if BookView.tobetyped[index] == console.text()[index]:
            #     print("hi")
        for index, c in enumerate(console.text()):
            if index == BookView.cursorPos:
                try:
                    if console.text()[index] == BookView.tobetyped[index]:
                        BookView.cursorPos += 1
                        BookView.cursor.setPosition(BookView.cursorPos,
                                                    BookView.cursor.KeepAnchor)
                        BookView.cursor.mergeCharFormat(BookView.highlight)
                except IndexError:
                    pass
        if len(console.text()) < BookView.cursorPos:
            BookView.cursor.mergeCharFormat(BookView.unhighlight) # pls
            BookView.cursorPos -= BookView.cursorPos - len(console.text())
            BookView.cursor.setPosition(BookView.cursorPos,
                                        BookView.cursor.KeepAnchor)
            BookView.cursor.mergeCharFormat(BookView.highlight)
    return
## i feel like i’m not doing this the right way.
## and surely there’ll be an error when things are typed from the main view


def handleEntryReturn():
    entry = console.text()

    if entry[0] == ">":
        if entry == '>switch.main': # make it case-insensitive
            retype.switchMainView()
            console.setText('')
        if entry == '>switch.book1':
            retype.switchBookView()
            console.setText('')
        if entry == '>print':
            print('console')
            console.setText('')
        # if entry == '>cursor':
        #     BookView.cursor.setPosition(1, BookView.cursor.KeepAnchor)
        #console.setText('') # probably not good

if __name__ == '__main__':
    app = QApplication(sys.argv)
    qss_file = open('style/default.qss').read()
    retype = Main()
    retype.show()
    #print(BookView.end)
    sys.exit(app.exec_())
