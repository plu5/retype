"""PyQt5 grid layout that is like bookshelves; places each item at the bottom
centre of its cell, like a book resting on a shelf. Changes dynamically as
the window resizes to fit as many items as it can, accounting for
contentsMargins."""

# NOTE(plu5): spacing isn’t implemented because this is a grid-based layout
#  so it doesn’t really make sense to me. the spacing between items in this
#  layout then is only based on the given cell width and height, plus
#  contentsMargins at the edges.

from PyQt5.QtCore import QSize, QRect, QPoint
from PyQt5.QtWidgets import QWidget, QGridLayout, QScrollArea, QLayout
from math import floor, ceil


class ShelvesLayout(QLayout):
    def __init__(self, parent=None, cell_width=140, cell_height=140):
        super().__init__(parent)
        self.cell_width = cell_width
        self.cell_height = cell_height
        # Note that while the cell height will always be what you set,
        #  the cell width will vary a bit as the window is resized

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

    def hasHeightForWidth(self):
        """This layout’s height depends on its width"""
        return True

    def heightForWidth(self, width):
        """Return the preferred height for this layout"""
        margins = self.getContentsMargins()
        width -= margins[1] + margins[2]  # minus left and right margins
        # Get the height this width would result in
        height = self.doLayout(QRect(0, 0, width, 0), True)
        height += margins[0] + margins[3]  # plus top and bottom margins
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        margins = self.getContentsMargins()
        rect.setX(rect.x() + margins[1])  # plus left margin
        rect.setY(rect.y() + margins[0])  # plus top margin
        rect.setWidth(rect.width() - margins[2])  # minus right margin
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        margins = self.getContentsMargins()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        # Account for the margins
        size += QSize(margins[1] + margins[2], margins[0] + margins[3])
        return size

    def doLayout(self, rect, dry_run=False):
        """Lay out the items in `item_list' within bounding QRect `rect'.
If dry_run, only do the calculations and return the resulting grid’s height."""
        # Set the x and y to the top left corner of the bounding rect
        (x, y) = (rect.x(), rect.y())

        # Calculate number of columns that can fit
        columns = floor(rect.width() / self.cell_width) or 1
        # Calculate what the width of each cell is going to be,
        #  based on the number of columns
        cell_effective_width = rect.width() / columns
        # Calculate number of rows
        rows = ceil(len(self.item_list) / columns)

        row_height = self.cell_height

        item_index = 0
        for i in range(rows):
            # This variable is used to “move right” as we place each item in
            #  the row. as each item is placed the cell width is added to it,
            #  and then it is used to place the next one.
            added_width = 0
            for i in range(columns):
                item = self.item_list[item_index]
                if not dry_run:
                    # Some positioning variables to help place each item
                    #  at centre bottom of its cell, as if resting on a shelf
                    x_gap_to_centre = (cell_effective_width / 2) \
                        - (item.sizeHint().width() / 2)
                    y_gap_to_bottom = self.cell_height \
                        - item.sizeHint().height()
                    # Place item
                    item.setGeometry(QRect(
                        QPoint(x + added_width + x_gap_to_centre,
                               y + y_gap_to_bottom),
                        item.sizeHint()))
                    added_width += cell_effective_width
                item_index += 1
                # Exit out of loop if placed all items already
                if len(self.item_list) == item_index:
                    break
            if len(self.item_list) == item_index:
                break
            # Next row
            y = y + row_height

        # Return height of the resulting grid
        return y + row_height - rect.y()


class ShelvesWidget(QWidget):
    """
    A resizable and scrollable widget that uses ShelvesLayout.
    Use its addWidget() method to add children,
    setContentsMargins() to set the layout’s margins.
    """
    def __init__(self, parent=None, cell_width=140, cell_height=140):
        super().__init__(parent)
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        # Wrapper to contain shelves layout
        self.wrapper = QWidget(self.scrollArea)
        self.layout = ShelvesLayout(self.wrapper, cell_width, cell_height)
        self.wrapper.setLayout(self.layout)
        # Layout for us to put the scroll area in
        self.outer_layout = QGridLayout(self)
        self.scrollArea.setWidget(self.wrapper)
        self.outer_layout.addWidget(self.scrollArea)
        self.outer_layout.setSpacing(0)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)

    def addWidget(self, widget):
        self.layout.addWidget(widget)

    def setContentsMargins(self, left, top, right, bottom):
        self.layout.setContentsMargins(left, top, right, bottom)
