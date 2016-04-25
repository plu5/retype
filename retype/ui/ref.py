import sys
from PyQt5.QtWidgets import (QPushButton, QMainWindow, QApplication, QWidget,
                             QDialog, QStackedWidget, QLineEdit, QHBoxLayout,
                             QVBoxLayout, QLabel, qApp, QAction, QTextBrowser,
                             QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, QUrl, QObject, QEvent#, QString
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor
from ebooklib import epub
import ebooklib
import os
from modeline import Modeline
from console import *

book = 0
chapters = []
title = "No book loaded"

pathlist = []
for root, dirs, files in os.walk("library"):
                    for f in files:
                        if f.lower().endswith(".epub"):
                            pathlist.append(os.path.join(root, f))


class Main(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        global console
        console = Console(self)

        self.stacked = QStackedWidget()
        self.consistentLayout = QVBoxLayout()
        self.consistentLayout.setContentsMargins(0, 0, 0, 0)
        self.consistentLayout.setSpacing(0) #
        self.consistentLayout.addWidget(self.stacked)
        self.consistentLayout.addWidget(console)
        mainWidget = QWidget()
        mainWidget.setLayout(self.consistentLayout)
        self.switchMainView()
        #self.switchBookView() #

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

    def loadBook(self, path):#path):
        global book, chapters, title
        # book = epub.read_epub(path)
        # chapters = []
        # title = book.title
        # for document in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        #     chapters.append(document)
        # Main.switchBookView(self)
        book = epub.read_epub(path)#'library\test.epub')
        title = book.title
        for document in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            chapters.append(document)
        Main.switchBookView(self)
        try:
            BookView.displayText.setHtml(str(chapters[1].content, 'utf-8'))
        except IndexError:
            BookView.displayText.setHtml("No book loaded")
        #Main.switchBookView(self)


class EventFilter(QObject):
    def eventFilter(self, source, event):
        if(event.type() == QEvent.KeyPress):
            if event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
                BookView.displayText.verticalScrollBar().setValue(
                    BookView.displayText.verticalScrollBar().value() + 500)
                return True
            if event.key() == Qt.Key_V and event.modifiers() == Qt.AltModifier:
                BookView.displayText.verticalScrollBar().setValue(
                    BookView.displayText.verticalScrollBar().value() - 500)
                return True
            else:
                return super().eventFilter(source, event)
        else:
            return super().eventFilter(source, event)


class Console(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAccessibleName("console")
        self.textChanged.connect(handleEntry)
        self.returnPressed.connect(handleEntryReturn)
        self.consoleFilter = EventFilter()
        self.installEventFilter(self.consoleFilter)


class MainView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout()
        self.label = QLabel('Main View', self)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)


class BookView(QWidget):
    # displayText, cursor, endcursor, highlight, unhighlight, debug, \
    #     tobetypedlist, tobetyped, currentSentence, cursorPos, linePos, \
    #     persistentPos = 0 # should these be object vars instead of class?
    displayText, cursor, endcursor, highlight, unhighlight, debug, \
        tobetypedlist, tobetyped, currentSentence, cursorPos, linePos, \
        persistentPos, modeline = [0] * 13
    # cursor = 0
    # endcursor = 0
    # highlight = 0
    # unhighlight = 0
    # debug = 0
    # tobetypedlist = 0
    # tobetyped = 0
    # currentSentence = 0
    # cursorPos = 0
    # linePos = 0
    # persistentPos = 0
    def __init__(self, parent=None):
        super().__init__(parent)
        
        BookView.displayText = QTextBrowser(self)
        try:
            BookView.displayText.setHtml(str(chapters[1].content, 'utf-8'))
        except IndexError:
            BookView.displayText.setHtml("No book loaded")

        tobetypedraw = BookView.displayText.toPlainText()
        tobetypedraw = tobetypedraw.replace('\ufffc', ' ') # with a space so we can account for it
        BookView.tobetypedlist = tobetypedraw.splitlines()
        #BookView.tobetypedlist = map(str.rstrip, BookView.tobetypedlist)
        #BookView.tobetypedlist = [s.rstrip() for s in BookView.tobetypedlist] #
        # print(BookView.tobetypedlist[0])
        # print(BookView.tobetypedlist[0].rstrip())
        BookView.currentSentence = BookView.tobetypedlist[BookView.linePos]

        BookView.highlight = QTextCharFormat()
        BookView.highlight.setBackground(QColor('yellow'))
        BookView.unhighlight = QTextCharFormat()
        BookView.unhighlight.setBackground(QColor(246, 241, 222)) #
        #BookView.unhighlight.clearBackground()
        BookView.debug = QTextCharFormat()
        BookView.debug.setBackground(QColor('red'))
        #global cursor #
        BookView.cursor = QTextCursor(BookView.displayText.document())
        #BookView.cursor.setPosition(0, BookView.cursor.MoveAnchor)
        BookView.cursor.movePosition(0)
        BookView.cursor.movePosition(4, BookView.cursor.KeepAnchor)
        BookView.cursor.setCharFormat(BookView.debug)
        #BookView.cursor.setPosition(10, BookView.cursor.KeepAnchor)
        #BookView.cursor.setCharFormat(BookView.highlight)
        ##print("debug: len(BookView.tobetypedlist) is " + str(len(BookView.tobetypedlist)))

        BookView.endcursor = QTextCursor(BookView.displayText.document())

        #self.modeline = QLabel("<i>"+title+"</i>" + " - " + str(BookView.cursorPos), self)
        #self.modeline.setAccessibleName("modeline")
        BookView.modeline = Modeline(self) #
        BookView.modeline.setTitle(title)
        BookView.modeline.setCursorPos(BookView.cursorPos)

        self.bookviewFilter = EventFilter()
        self.installEventFilter(self.bookviewFilter)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0) # pls
        self.layout.addWidget(BookView.displayText)
        self.layout.addWidget(BookView.modeline)
        self.setLayout(self.layout)

    def updateModeline():
        BookView.modeline.setCursorPos(BookView.cursorPos)
        BookView.modeline.setLinePos(BookView.linePos)        
        BookView.modeline.repaint()

    def advanceLine():
        BookView.linePos += 1
        if BookView.cursorPos - BookView.persistentPos == len(BookView.currentSentence):
            BookView.cursorPos += 1
            print("debug: advanceLine equals currentSentence")
        else:
            BookView.cursorPos += len(BookView.currentSentence) + 1 # not good
        # BookView.cursorPos = len(BookView.currentSentence) - BookView.cursorPos + BookView.persistentPos + 1
        BookView.persistentPos = BookView.cursorPos
        BookView.currentSentence = BookView.tobetypedlist[BookView.linePos]
        BookView.cursor.setPosition(BookView.cursorPos, BookView.cursor.KeepAnchor)
        BookView.cursor.mergeCharFormat(BookView.highlight)
        BookView.updateModeline()

    def advanceCursor():
        BookView.cursorPos += 1
        BookView.cursor.setPosition(BookView.cursorPos, BookView.cursor.KeepAnchor)
        #BookView.cursor.mergeCharFormat(BookView.highlight)
        print(BookView.cursorPos)

    def recedeCursor():
        BookView.cursorPos -= 1
        BookView.cursor.setPosition(BookView.cursorPos, BookView.cursor.KeepAnchor)
        #BookView.cursor.mergeCharFormat(BookView.highlight)
        print(BookView.cursorPos)

    def updateHighlighting():
        global isbookview
        BookView.cursor.mergeCharFormat(BookView.unhighlight)
        BookView.cursor.mergeCharFormat(BookView.highlight)
        print(BookView.cursorPos)

    def automaticScrolling(): # wip
        #self.displayText.setCenterOnScroll(true) # QTextBrowser object has no attribute 'SetCenterOnScroll
        # think about how to do this
        #BookView.displayText.textCursor().movePosition(BookView.cursorPos)
        #BookView.endcursor.setPosition(10000)#BookView.cursorPos + 50) #????????????
        BookView.endcursor.setPosition(BookView.cursorPos - 300)
        print(BookView.endcursor.position())
        BookView.displayText.setTextCursor(BookView.endcursor) #
        BookView.displayText.ensureCursorVisible() # seemingly does nothing


def handleEntry():
    global isbookview

    if isbookview:
        # by-char
        for index, c in enumerate(console.text()):
            if index + BookView.persistentPos == BookView.cursorPos:
                try:
                    if console.text()[index] == BookView.currentSentence[index]:  # change console.text()[index] to just c?
                        BookView.cursorPos += 1
                        BookView.cursor.setPosition(BookView.cursorPos,
                                                    BookView.cursor.KeepAnchor)
                        BookView.cursor.mergeCharFormat(BookView.highlight)
                        BookView.updateModeline()
                        # print("debug: by-char")
                except IndexError:
                    print("debug: indexError")
                    pass

        # remove highlighting
        if len(console.text()) + BookView.persistentPos < BookView.cursorPos: #
            BookView.cursor.mergeCharFormat(BookView.unhighlight) # pls
            BookView.cursorPos = BookView.persistentPos + len(console.text()) #
            BookView.cursor.setPosition(BookView.cursorPos,
                                        BookView.cursor.KeepAnchor)
            BookView.cursor.mergeCharFormat(BookView.highlight)
            BookView.updateModeline()
            # print("debug: remove highlighting " + str(BookView.cursorPos))

        # next line
        if console.text() == BookView.currentSentence:
            BookView.advanceLine()
            print("debug: normal next line; " + BookView.currentSentence)
            console.setText('')
            BookView.updateModeline()
            # skip lines composed entirely of whitespace and empty lines
            while BookView.currentSentence.isspace() or BookView.currentSentence == '':
                print("debug: isspace or empty next line")
                BookView.advanceLine()
                console.setText('')
        #BookView.automaticScrolling()
        return


def handleEntryReturn():
    entry = console.text()
    if entry.startswith(">"):
        e = entry.lower()
        if e[1:] == 'switch-main':
            retype.switchMainView()
        elif e[1:] == 'switch-book': # debug
            retype.switchBookView()
        elif e[1:] == 'l': # debug?
            BookView.advanceLine()
        elif e[1:] == 'cf': # debug
            BookView.advanceCursor()
        elif e[1:] == 'cb': # debug
            BookView.recedeCursor()
        elif e[1:] == 'h': # debug
            BookView.updateHighlighting()
        elif e[1:] == 'pf': # debug
            BookView.persistentPos += 1
            print(BookView.persistentPos)
        elif e[1:] == 'pb': # debug
            BookView.persistentPos -= 1
            print(BookView.persistentPos)
        elif e[1:] == 's': # debug
            BookView.automaticScrolling()
        elif e[1:] == 'file': # debug
                # for root, dirs, files in os.walk("library"):
                #     for f in files:
                #         if f.lower().endswith(".epub"):
                #             print(os.path.join(root, f))
            print(pathlist)
        elif e[1:5] == 'load': # debug
            if '(' and ')' in e:
                path = e[e.find("(") + 1:e.find(")")]
                #if path in pathlist:
                Main.loadBook(retype, path)#pathlist[1])
                #else:
                #    print("handleEntryReturn:>load: file not found")
            else:
                print("handleEntryReturn:>load: no file specified")
        console.setText('')


if __name__ == '__main__':
    app = QApplication(sys.argv)

    qss_file = open('style/default.qss').read()
    retype = Main()
    retype.show()

    sys.exit(app.exec_())
