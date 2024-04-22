from qt import (QTabWidget, QStyle, QStyleOptionTabWidgetFrame, QStackedWidget,
                QWidget, QScrollArea, QLabel, QSize, QHBoxLayout,
                QTextDocument)


class AdjustedTabWidget(QTabWidget):
    """QTabWidget descendent whose size adjusts to fit the selected tab.
Adapted from musicamante https://stackoverflow.com/a/72673580/18396947"""
    def __init__(self, parent=None):
        QTabWidget.__init__(self, parent)

    def minimumSizeHint(self):
        if self.count() < 0 or not self.currentWidget():
            return super().sizeHint()

        baseSize = self.currentWidget().sizeHint().expandedTo(
            self.currentWidget().minimumSize())
        if not self.tabBar().isHidden():
            tabHint = self.tabBar().sizeHint()
            if self.tabPosition() in (self.North, self.South):
                baseSize.setHeight(baseSize.height() + tabHint.height())
            else:
                baseSize.setWidth(baseSize.width() + tabHint.width())

        opt = QStyleOptionTabWidgetFrame()
        self.initStyleOption(opt)
        return self.style().sizeFromContents(
            QStyle.ContentsType.CT_TabWidget, opt, baseSize, self)

    def sizeHint(self):
        return self.minimumSizeHint()


class ScrollTabWidget(AdjustedTabWidget):
    """AdjustedTabWidget where each tab contains a QScrollArea"""
    def __init__(self, parent=None):
        AdjustedTabWidget.__init__(self, parent)

    def addTab(self, widget, name):
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        AdjustedTabWidget.addTab(self, scroll, name)


class AdjustedStackedWidget(QStackedWidget):
    """QStackedWidget descendent whose size adjusts to fit the current
widget."""
    def __init__(self, parent=None):
        QStackedWidget.__init__(self, parent)

    def minimumSizeHint(self):
        current_widget = self.currentWidget()
        if self.count() < 0 or not current_widget:
            return super().sizeHint()

        current_widget.setMinimumSize(current_widget.sizeHint())
        baseSize = current_widget.sizeHint().expandedTo(
            current_widget.minimumSize())

        return baseSize

    def sizeHint(self):
        return self.minimumSizeHint()


class ScrollingStackedWidget(QScrollArea):
    """AdjustedStackedWidget in a QScrollArea"""
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.stack = AdjustedStackedWidget()
        self.setWidget(self.stack)
        self.setWidgetResizable(True)

    def addWidget(self, *args):
        self.stack.addWidget(*args)

    def setCurrentWidget(self, *args):
        self.stack.setCurrentWidget(*args)


class WrappedLabel(QWidget):
    """Workaround for word-wrapped QLabel size constraint bug.
Adapted from musicamante https://stackoverflow.com/a/70757504/18396947"""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        lyt = QHBoxLayout(self)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        lyt.addWidget(self.label)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.doc = QTextDocument(text, self)
        self.doc.setDocumentMargin(0)
        self.doc.setDefaultFont(self.label.font())

    def minimumSizeHint(self):
        self.doc.setTextWidth(self.label.width())
        height = self.doc.size().height()
        height += self.label.frameWidth() * 2
        return QSize(50, height)

    def sizeHint(self):
        return self.minimumSizeHint()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateGeometry()

    def hasHeightForWidth(self):
        """Without this, the sizeHint seems to be ignored"""
        return False


class MinWidget(QWidget):
    def __init__(self, min=100, width=True, height=True, parent=None):
        QWidget.__init__(self, parent)
        self.min = min
        self.width = width
        self.height = height

    def minimumSizeHint(self):
        size = QWidget.minimumSizeHint(self)
        if self.width:
            size.setWidth(self.min)
        if self.height:
            size.setHeight(self.min)
        return size

    def sizeHint(self):
        return self.minimumSizeHint()
