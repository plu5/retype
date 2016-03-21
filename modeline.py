import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QSlider, QVBoxLayout,
                             QTextBrowser)
from PyQt5.QtGui import QPainter, QFont, QColor, QPen
from PyQt5.QtCore import Qt, QObject, pyqtSignal

class Modeline(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(1, 17) # 16, changed to fit border
        self.cursorPos = 0
        self.title = ""
        self.linePos = 0
        self.chapPos = 0
        self.chapTotal = 0
        self.percentage = 0

    def setCursorPos(self, value):
        self.cursorPos = value

    def setTitle(self, title):
        self.title = title

    def setLinePos(self, value):
        self.linePos = value

    def setChapPos(self, value):
        self.chapPos = value

    def setChapTotal(self, value):
        self.chapTotal = value

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        width = self.size().width()
        height = self.size().height()
        font = QFont('Courier New', 9) # change to a font that’s available on all systems?
        qp.setFont(font)
        fontHeight = qp.fontMetrics().ascent() - qp.fontMetrics().descent() - 1
        fontVerticalMiddle = (height + fontHeight) / 2

        posSeparator = ":"
        chapPretext = "chapter "
        chapSeparator = "/"
        modelineColour1 = QColor(223, 216, 202)
        modelineColour2 = QColor(198, 171, 120)
        modelineColour3 = QColor(190, 190, 190)
        mainTextPen = QPen(QColor(51, 51, 51), 1, Qt.SolidLine)
        secondaryTextPen = QPen(Qt.black, 1, Qt.SolidLine)

        elementWidth = {'linePos': qp.fontMetrics().width(str(self.linePos)),
                        'cursorPos': qp.fontMetrics().width(str(self.cursorPos)),
                        'title': qp.fontMetrics().width(str(self.title)),
                        'chapPretext': qp.fontMetrics().width(str(chapPretext)),
                        'chapPos': qp.fontMetrics().width(str(self.chapPos)),
                        'chapTotal': qp.fontMetrics().width(str(self.chapTotal))}
        padding = 10
        positionLinePos = padding
        positionCursorPos = positionLinePos + elementWidth['linePos'] + padding
        positionPosSeparator = positionLinePos + elementWidth['linePos']
        positionTitle = positionCursorPos + elementWidth['cursorPos'] + 3*padding #
        positionChapPretext = positionTitle + elementWidth['title'] + 3*padding
        positionChapPos = positionChapPretext + elementWidth['chapPretext']
        positionChapTotal = positionChapPos + elementWidth['chapPos'] + padding
        positionChapSeparator = (positionChapPos + positionChapTotal) / 2

        # main rect
        qp.setPen(modelineColour1)
        qp.setBrush(modelineColour1)
        qp.drawRect(0, 0, width, height)
        # top line
        qp.setBrush(modelineColour2)
        qp.setPen(modelineColour2)
        qp.drawLine(0, 0, width, 0)

        # seperator experimentation
        separatorStart1 = positionTitle - padding - padding #
        qp.setPen(modelineColour3)
        qp.setBrush(modelineColour3)
        qp.drawLine(separatorStart1, 1, separatorStart1, 2)
        qp.drawLine(separatorStart1, 2, separatorStart1 + 7, 9)
        qp.drawLine(separatorStart1 + 7, 9, separatorStart1, 17)
        # fill
        for r in range(7):
           qp.drawLine(separatorStart1 + r, r + 2, separatorStart1 + r, 15 - r) #r+1
        qp.drawRect(0, 1, separatorStart1, 17) #rect fill
        
        # secondsep
        separatorStart2 = positionTitle + elementWidth['title'] + padding#positionChapTotal + elementWidth['chapTotal'] + padding #
        qp.drawRect(separatorStart2, 1, width, 17)
        qp.setPen(modelineColour1)
        qp.setBrush(modelineColour1)
        qp.drawLine(separatorStart2, 1, separatorStart2, 2)
        qp.drawLine(separatorStart2, 2, separatorStart2 + 7, 9)
        qp.drawLine(separatorStart2 + 7, 9, separatorStart2, 17)
        # fill
        for r in range(7):
           qp.drawLine(separatorStart2 + r, r + 2, separatorStart2 + r, 15 - r) #r+1

        ##qp.drawLine(separatorStart1, 0, separatorStart1, 15)
        ##qp.drawLine(separatorStart1 + 1, 3, separatorStart1 + 1, 14)
        ##qp.drawLine(separatorStart1 + 2, 4, separatorStart1 + 2, 13)

        # elements
        qp.setPen(mainTextPen)
        qp.setBrush(Qt.NoBrush)
        qp.drawText(positionPosSeparator, fontVerticalMiddle, str(posSeparator))
        qp.drawText(positionCursorPos, fontVerticalMiddle, str(self.cursorPos))
        qp.drawText(positionChapPretext, fontVerticalMiddle, str("chapter "))
        qp.drawText(positionChapPos, fontVerticalMiddle, str(self.chapPos))
        qp.drawText(positionChapSeparator, fontVerticalMiddle, str(chapSeparator))
        qp.drawText(positionChapTotal, fontVerticalMiddle, str(self.chapTotal))
        qp.setPen(secondaryTextPen)
        qp.setBrush(Qt.NoBrush)
        qp.drawText(positionLinePos, fontVerticalMiddle, str(self.linePos))
        qp.drawText(positionTitle, fontVerticalMiddle, str(self.title))

        qp.end()


# class Communicate(QObject):
#     update = pyqtSignal(int)


# class Example(QWidget):
#     title = "book title"
#     # maybe in actual retype the title and book should be class variables
#     cursorPos = 5
#     def __init__(self):
#         super().__init__()
#         slider = QSlider(Qt.Horizontal, self)
#         slider.setFocusPolicy(Qt.NoFocus)
#         slider.setRange(1, 750)
# #        slider.setGeometry(30, 50, 200, 15)
#         slider.valueChanged[int].connect(self.changeValue)
#         self.displayText = QTextBrowser(self)
#         self.displayText.setText("2016-03-16 20:42")
#         self.modeline = Modeline(self)
#         self.c = Communicate()
#         self.c.update[int].connect(self.modeline.setValue)

#         self.qvlayout = QVBoxLayout()
#         self.qvlayout.setContentsMargins(0, 0, 0, 0)
#         self.qvlayout.setSpacing(0) # works
#         self.qvlayout.addWidget(self.displayText)
#         self.qvlayout.addWidget(self.modeline)
#         self.qvlayout.addWidget(slider)
        
#         self.setGeometry(300, 300, 390, 210)
#         self.setLayout(self.qvlayout)
#         self.setWindowTitle('testing custom widget')
#         self.show()

#     def changeValue(self, value):
#         self.c.update.emit(value)
#         self.modeline.repaint()


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = Example()
#     sys.exit(app.exec_())
