from qt import (QTabWidget, QStyle, QStyleOptionTabWidgetFrame, QStackedWidget,
                QWidget, QScrollArea, QLabel, QSize, QHBoxLayout,
                QTextDocument, QTextBrowser)

from typing import TYPE_CHECKING


class AdjustedTabWidget(QTabWidget):
    """QTabWidget descendent whose size adjusts to fit the selected tab.
Adapted from musicamante https://stackoverflow.com/a/72673580/18396947"""
    def __init__(self, parent=None):
        # type: (AdjustedTabWidget, QWidget | None) -> None
        QTabWidget.__init__(self, parent)

    def minimumSizeHint(self):
        # type: (AdjustedTabWidget) -> QSize
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
        # type: (AdjustedTabWidget) -> QSize
        return self.minimumSizeHint()


class ScrollTabWidget(AdjustedTabWidget):
    """AdjustedTabWidget where each tab contains a QScrollArea"""
    def __init__(self, parent=None):
        # type: (ScrollTabWidget, QWidget | None) -> None
        AdjustedTabWidget.__init__(self, parent)

    def addTab(self, widget, label, icon=None):  # type: ignore[override]
        # type: (ScrollTabWidget, QWidget, str, QIcon | None) -> int
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        if icon:
            return AdjustedTabWidget.addTab(self, scroll, icon, label)
        return AdjustedTabWidget.addTab(self, scroll, label)


class AdjustedStackedWidget(QStackedWidget):
    """QStackedWidget descendent whose size adjusts to fit the current
widget."""
    def __init__(self, parent=None):
        # type: (AdjustedStackedWidget, QWidget | None) -> None
        QStackedWidget.__init__(self, parent)

    def minimumSizeHint(self):
        # type: (AdjustedStackedWidget) -> QSize
        current_widget = self.currentWidget()
        if self.count() < 0 or not current_widget:
            return super().sizeHint()

        current_widget.setMinimumSize(current_widget.sizeHint())
        baseSize = current_widget.sizeHint().expandedTo(
            current_widget.minimumSize())

        return baseSize

    def sizeHint(self):
        # type: (AdjustedStackedWidget) -> QSize
        return self.minimumSizeHint()


class ScrollingStackedWidget(QScrollArea):
    """AdjustedStackedWidget in a QScrollArea"""
    def __init__(self, parent=None):
        # type: (ScrollingStackedWidget, QWidget | None) -> None
        QWidget.__init__(self, parent)
        self.stack = AdjustedStackedWidget()
        self.setWidget(self.stack)
        self.setWidgetResizable(True)

    def addWidget(self, w):
        # type: (ScrollingStackedWidget, QWidget) -> int
        return self.stack.addWidget(w)

    def setCurrentWidget(self, w):
        # type: (ScrollingStackedWidget, QWidget) -> None
        self.stack.setCurrentWidget(w)


class WrappedLabel(QWidget):
    """Workaround for word-wrapped QLabel size constraint bug.
Adapted from musicamante https://stackoverflow.com/a/70757504/18396947"""
    def __init__(self, text, parent=None):
        # type: (WrappedLabel, str, QWidget | None) -> None
        super().__init__(parent)
        lyt = QHBoxLayout(self)
        self.label = QLabel(text)  # type: QLabel
        self.label.setWordWrap(True)
        lyt.addWidget(self.label)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.doc = QTextDocument(text, self)  # type: QTextDocument
        self.doc.setDocumentMargin(0)
        self.doc.setDefaultFont(self.label.font())

    def minimumSizeHint(self):
        # type: (WrappedLabel) -> QSize
        self.doc.setTextWidth(self.label.width())
        height = int(self.doc.size().height())  # type: int
        height += self.label.frameWidth() * 2
        return QSize(50, height)

    def sizeHint(self):
        # type: (WrappedLabel) -> QSize
        return self.minimumSizeHint()

    def resizeEvent(self, event):
        # type: (WrappedLabel, QResizeEvent) -> None
        super().resizeEvent(event)
        self.updateGeometry()

    def hasHeightForWidth(self):
        # type: (WrappedLabel) -> bool
        """Without this, the sizeHint seems to be ignored"""
        return False


class MinWidget(QWidget):
    def __init__(self, min=100, width=True, height=True, parent=None):
        # type: (MinWidget, int, bool, bool, QWidget | None) -> None
        QWidget.__init__(self, parent)
        self.min = min  # type: int
        self.for_width = width  # type: bool
        self.for_height = height  # type: bool

    def minimumSizeHint(self):
        # type: (MinWidget) -> QSize
        size = QWidget.minimumSizeHint(self)  # type: QSize
        if self.for_width:
            size.setWidth(self.min)
        if self.for_height:
            size.setHeight(self.min)
        return size

    def sizeHint(self):
        # type: (MinWidget) -> QSize
        return self.minimumSizeHint()


class ReadOnlyTextWidget(QWidget):
    def __init__(self, text="", parent=None):
        # type: (ReadOnlyTextWidget, str, QWidget | None) -> None
        QWidget.__init__(self, parent)

        box = QTextBrowser()
        box.setText(text)
        box.setOpenExternalLinks(True)
        lyt = QHBoxLayout(self)
        lyt.addWidget(box)
        lyt.setSpacing(0)
        lyt.setContentsMargins(0, 0, 0, 0)


if TYPE_CHECKING:
    from qt import QResizeEvent, QIcon  # noqa: F401
