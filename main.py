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
    tobetypedraw = 0 # probably doesn’t need to be class var (it can just be private)
    tobetypedlist = 0
    tobetyped = 0
    currentSentence = 0
    cursorPos = 0
    linePos = 0
    persistentPos = 0
    def __init__(self, parent=None):
        super().__init__(parent)

        #global tobetyped
        #BookView.tobetyped = "text to be typed" # <i>text</i>
        #BookView.tobetyped = strip_tags(str(chapters[1].content, 'utf-8'))
        #print(BookView.tobetyped)
        
        self.displayText = QTextBrowser(self)
        #self.displayText.setHtml(str(chapters[1].content))
        #self.displayText.setSource(QUrl('file:test/OEBPS/fm01.html'))
        #self.displayText.setSource(QUrl('file:test/OEBPS/bm02.html'))
        #self.displayText.setHtml("<b>text</b> to be typed ‘’ “” –—…—\r\ntest <p>\r\ntest2</p> hello anotherline<p>why</p>")
        #self.displayText.setHtml(str(chapters[1].content, 'utf-8')) # AH!
        self.displayText.setHtml("first line<br />second line<br />third line<br />fourth line<br />fifth line")
        #self.displayText.setHtml(BookView.tobetyped)
        # get display text display text
        BookView.tobetypedraw = self.displayText.toPlainText()
        BookView.tobetypedraw = BookView.tobetypedraw.replace('\ufffc', ' ') # with a space so we can account for it
        BookView.tobetypedlist = BookView.tobetypedraw.splitlines()
        #BookView.tobetypedlist = map(str.rstrip, BookView.tobetypedlist)
        #BookView.tobetypedlist = [s.rstrip() for s in BookView.tobetypedlist] #
        # print(BookView.tobetypedlist[0])
        # print(BookView.tobetypedlist[0].rstrip())
        BookView.currentSentence = BookView.tobetypedlist[BookView.linePos]
        # split it into sentences at /n or something
        # should do like type where it highlights the line once
        # have a counter for current sentence and it will be the index? it’ll be tobetyped
        # if you’re at the last character move on to the next line

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
        print("debug: len(BookView.tobetypedlist) is " + str(len(BookView.tobetypedlist)))

        self.modeline = QLabel("this will be the modeline", self)
        self.modeline.setAccessibleName("modeline")

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.displayText)
        self.layout.addWidget(self.modeline)
        self.setLayout(self.layout)

    def advanceLine():
        BookView.linePos += 1
        if BookView.cursorPos - BookView.persistentPos == len(BookView.currentSentence):
            #BookView.cursorPos += 1
            print("debug: advanceLine equals currentSentence")
        else:
            BookView.cursorPos += len(BookView.currentSentence) + 1 # not good
        # BookView.cursorPos = len(BookView.currentSentence) - BookView.cursorPos + BookView.persistentPos + 1
        BookView.persistentPos = BookView.cursorPos
        BookView.currentSentence = BookView.tobetypedlist[BookView.linePos]
        BookView.cursor.setPosition(BookView.cursorPos, BookView.cursor.KeepAnchor)
        BookView.cursor.mergeCharFormat(BookView.highlight)

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


def handleEntry(): # get where it’s been called from
    global isbookview

    if isbookview: # all of these are being ignored after the 2nd line
        for index, c in enumerate(console.text()):
            if index + BookView.persistentPos == BookView.cursorPos: #doesnt work with multiple lines
                try:
                    if console.text()[index] == BookView.currentSentence[index]:  # change console.text()[index] to just c?
                        BookView.cursorPos += 1
                        BookView.cursor.setPosition(BookView.cursorPos,
                                                    BookView.cursor.KeepAnchor)
                        BookView.cursor.mergeCharFormat(BookView.highlight)
                        print("debug: by-char")
                except IndexError:
                    print("debug: indexError")
                    pass
        # remove highlighting
        #try:
        #    if console.text()[0] != '>':
        if len(console.text()) + BookView.persistentPos < BookView.cursorPos: #
            # try:
            #     if console.text()[0] == '>':
            #         return #unfortunately once you delete > it erases all temp highlighting which actually doesn’t matter probably, as the cursor movement functions should be debug-only
            # except IndexError:
            #     pass
            BookView.cursor.mergeCharFormat(BookView.unhighlight) # pls
            BookView.cursorPos = BookView.cursorPos - len(console.text()) -1 #
            BookView.cursor.setPosition(BookView.cursorPos,
                                        BookView.cursor.KeepAnchor)
            BookView.cursor.mergeCharFormat(BookView.highlight)
        #except IndexError:
        #    pass
        # next line
        if console.text() == BookView.currentSentence:
            BookView.advanceLine()
            print("debug: normal next line; " + BookView.currentSentence)
            console.setText('')
            # while BookView.currentSentence == '':
            #     print("debug: empty next line; " + BookView.currentSentence)
            #     BookView.advanceLine()
            #     console.setText('')
            # check if all characters in sentence are white space
            # while BookView.currentSentence.isspace():
            #     print("debug: isspace next line")
            #     BookView.advanceLine()
            #     console.setText('')
        return


def handleEntryReturn():
    entry = console.text()

    try:
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
            if entry == '>l':
                BookView.advanceLine()
            if entry == '>c.f':
                BookView.advanceCursor()
            if entry == '>c.b':
                BookView.recedeCursor()
            if entry == '>h':
                BookView.updateHighlighting()
            if entry == '>p.f':
                BookView.persistentPos += 1
                print(BookView.persistentPos)
            if entry == '>p.b':
                BookView.persistentPos -= 1
                print(BookView.persistentPos)
                
        # if entry == '>cursor':
        #     BookView.cursor.setPosition(1, BookView.cursor.KeepAnchor)
        #console.setText('') # probably not good
    except IndexError:
        print("debug: handleEntryReturn.indexError")
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    qss_file = open('style/default.qss').read()
    retype = Main()
    retype.show()
    #print(BookView.end)
    sys.exit(app.exec_())
