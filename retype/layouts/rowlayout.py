"""PyQt5 horizontal layout that simply lays out items from left to right based
 on their size, accounting for spacing and contents margins. Similar to the way
 items on a menu or toolbar are positioned."""

from PyQt5.Qt import QRect, QPoint, QSize, QLayout, Qt


class RowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_list = []

    def __del__(self):
        """Delete all items in this layout"""
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        """Add an item to the end of this layout"""
        self.item_list.append(item)

    def count(self):
        """Return number of items in this layout"""
        return len(self.item_list)

    def itemAt(self, index):
        """Return item at given index (non-destructively)"""
        if index >= 0 and index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index):
        """Remove and return item at given index"""
        if index >= 0 and index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Horizontal

    def setGeometry(self, rect):
        super().setGeometry(rect)
        margins = self.getContentsMargins()
        rect.setX(rect.x() + margins[1])  # plus left margin
        rect.setY(rect.y() + margins[0])  # plus top margin
        rect.setWidth(rect.width() - margins[2])  # minus right margin
        self.doLayout(rect, False)

    def sizeHint(self):
        size = self.minimumSize()
        size.setWidth(self.doLayout(QRect(0, 0, 0, 0), True))
        # Add left and right margins again
        margins = self.getContentsMargins()
        size += QSize(margins[1] + margins[2], 0)
        return size

    def minimumSize(self):
        size = QSize()
        margins = self.getContentsMargins()
        size = size.expandedTo(self.item_list[0].minimumSize())
        # Account for the margins
        size += QSize(margins[1] + margins[2], margins[0] + margins[3])
        return size

    def doLayout(self, rect, dry_run=False):
        """Lay out the items in `item_list' within bounding QRect `rect'.
If dry_run, only do the calculations and return the resulting width."""
        # Set the x and y to the top left corner of the bounding rect
        (x, y) = (rect.x(), rect.y())
        height = rect.height()

        # This variable is used to “move right” as we place each item in
        #  the row. as each item is placed its width + spacing is added to it,
        #  and then it is used to place the next one.
        added_width = 0
        for item in self.item_list:
            if not dry_run:
                y_gap_to_centre = (height / 2) - (item.sizeHint().height() / 2)
                item.setGeometry(QRect(
                    QPoint(x + added_width,
                           y + y_gap_to_centre),
                    item.sizeHint()))
            added_width += item.sizeHint().width() + self.spacing()

        return added_width - self.spacing()
