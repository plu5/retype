from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton)
from PyQt5.QtCore import (pyqtSignal)

class ShelfView(QWidget):
    switchViewSignal = pyqtSignal(int) # int/str/enum/list # or just 2?
    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        #self.switchViewSignal = pyqtSignal(int)
        self._initUI()

    def _initUI(self):
        self.layout = QVBoxLayout()
        self.temporary_label = QLabel('Shelf View', self)
        self.very_temporary_button = QPushButton('switch', self)
        self.very_temporary_button.clicked.connect(self.switchBookView)
        self.layout.addWidget(self.temporary_label)
        self.layout.addWidget(self.very_temporary_button)
        self.setLayout(self.layout)

    def switchBookView(self):
        self.switchViewSignal.emit(2)
        print('is printing working')
