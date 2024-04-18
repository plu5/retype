"""PyQt horizontal layout that simply lays out items from left to right based
 on their size, accounting for spacing and contents margins. Similar to the way
 items on a menu or toolbar are positioned."""

from math import floor
from qt import QRect, QPoint, QSize, QLayout, Qt, QSizePolicy


def _isExpanding(policy):
    return policy in [
        QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding]


def _calcItemGeom(item, x, y, height):
    v = _isExpanding(item.widget().sizePolicy().verticalPolicy())
    y_gap_to_centre = 0 if v else (height / 2) - (item.sizeHint().height() / 2)
    size = item.sizeHint()
    if v:
        size.setHeight(height)
        # Using heightForWidth to get width for height instead. Which is maybe
        #  improper but i don't know how else to do it
        if item.hasHeightForWidth():
            size.setWidth(item.heightForWidth(height))
    return QRect(QPoint(x, y + y_gap_to_centre), size)


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
        return Qt.Orientation.Horizontal

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

        expand_horizontally = []
        saved_x = 0

        for i in range(len(self.item_list)):
            item = self.item_list[i]
            if _isExpanding(item.widget().sizePolicy().horizontalPolicy()):
                expand_horizontally.append(i)
                if len(expand_horizontally) == 1:
                    saved_x = x
            item_rect = _calcItemGeom(item, x, y, height)
            if not dry_run:
                # Once we have any widgets that have to expand horizontally,
                #  we are going to have to setGeometry on all those items
                #  and the ones that follow the second loop, so avoid calling
                #  it twice
                if not len(expand_horizontally):
                    item.setGeometry(item_rect)
            x += item_rect.width() + self.spacing()

        total_width = x - self.spacing()

        # Account for expanding horizontal size policy; expand items if we
        #  have width left
        if len(expand_horizontally):
            left = rect.width() - total_width
            each = 0 if left <= 0 else floor(left / len(expand_horizontally))
            x = saved_x
            for i in range(expand_horizontally[0], len(self.item_list)):
                item = self.item_list[i]
                item_rect = _calcItemGeom(item, x, y, height)
                if i in expand_horizontally and each > 0:
                    item_rect.setWidth(each)
                if not dry_run:
                    item.setGeometry(item_rect)
                x += item_rect.width() + self.spacing()
        total_width -= self.spacing()

        return total_width
