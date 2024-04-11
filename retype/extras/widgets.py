from qt import QTabWidget, QStyle, QStyleOptionTabWidgetFrame


class AdjustedTabWidget(QTabWidget):
    """QTabWidget descendent whose size adjusts to fit the selected tab.
By musicamante https://stackoverflow.com/a/72673580/18396947"""
    def minimumSizeHint(self):
        if self.count() < 0:
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
            QStyle.CT_TabWidget, opt, baseSize, self)

    def sizeHint(self):
        return self.minimumSizeHint()
