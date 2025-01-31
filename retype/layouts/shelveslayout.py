"""PyQt grid layout that is like bookshelves; places each item at the bottom
centre of its cell, like a book resting on a shelf. Changes dynamically as
the window resizes to fit as many items as it can, accounting for
contentsMargins."""

# NOTE(plu5): spacing isn’t implemented because this is a grid-based layout
#  so it doesn’t really make sense to me. the spacing between items in this
#  layout then is only based on the given cell width and height, plus
#  contentsMargins at the edges.

from qt import QSize, QRect, QPoint, QWidget, QGridLayout, QScrollArea, QLayout
from math import floor, ceil

from typing import TYPE_CHECKING


class ShelvesLayout(QLayout):
    def __init__(self, parent=None,
                 min_cell_width=140, max_cell_width=200, cell_height=140):
        # type: (ShelvesLayout, QWidget | None, int, int, int) -> None
        if parent:
            super().__init__(parent)
        else:
            super().__init__()
        self.item_list = []  # type: list[QLayoutItem]
        self.min_cell_width = min_cell_width
        self.max_cell_width = max_cell_width
        self.cell_height = cell_height
        # The cell height is static, whereas cell width varies between min to
        # max as the window is resized.

    def __del__(self):
        # type: (ShelvesLayout) -> None
        """Delete all items in this layout"""
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        # type: (ShelvesLayout, QLayoutItem) -> None
        """Add an item to the end of this layout"""
        self.item_list.append(item)

    def count(self):
        # type: (ShelvesLayout) -> int
        """Return number of items in this layout"""
        return len(self.item_list)

    def itemAt(self, index):
        # type: (ShelvesLayout, int) -> QLayoutItem | None
        """Return item at given index (non-destructively)"""
        if index >= 0 and index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index):
        # type: (ShelvesLayout, int) -> QLayoutItem | None
        """Remove and return item at given index"""
        if index >= 0 and index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def hasHeightForWidth(self):
        # type: (ShelvesLayout) -> bool
        """This layout’s height depends on its width"""
        return True

    def heightForWidth(self, width):
        # type: (ShelvesLayout, int) -> int
        """Return the preferred height for this layout"""
        margins = self.getContentsMargins()
        width -= margins[1] + margins[2]  # minus left and right margins
        # Get the height this width would result in
        height = self.doLayout(QRect(0, 0, int(width), 0), True)
        height += margins[0] + margins[3]  # plus top and bottom margins
        return height

    def setGeometry(self, rect):
        # type: (ShelvesLayout, QRect) -> None
        super().setGeometry(rect)
        margins = self.getContentsMargins()
        rect.setX(rect.x() + margins[1])  # plus left margin
        rect.setY(rect.y() + margins[0])  # plus top margin
        rect.setWidth(rect.width() - margins[2])  # minus right margin
        self.doLayout(rect, False)

    def sizeHint(self):
        # type: (ShelvesLayout) -> QSize
        return self.minimumSize()

    def minimumSize(self):
        # type: (ShelvesLayout) -> QSize
        size = QSize()
        margins = self.getContentsMargins()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        # Account for the margins
        size += QSize(margins[1] + margins[2], margins[0] + margins[3])
        return size

    def doLayout(self, rect, dry_run=False):
        # type: (ShelvesLayout, QRect, bool) -> int
        """Lay out the items in `item_list' within bounding QRect `rect'.
If dry_run, only do the calculations and return the resulting grid’s height."""
        # Set the x and y to the top left corner of the bounding rect
        (x, y) = (rect.x(), rect.y())

        # Calculate number of columns that can fit. No more than our number of
        #  items.
        columns = min(floor(rect.width() / self.min_cell_width),
                      len(self.item_list)) or 1
        # Calculate what the width of each cell is going to be,
        #  based on the number of columns. No more than max_cell_width.
        cell_effective_width = int(rect.width() / columns)
        if cell_effective_width > self.max_cell_width:
            cell_effective_width = self.max_cell_width
            columns = min(floor(rect.width() / cell_effective_width),
                          len(self.item_list)) or 1
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
                    x_gap_to_centre = int((cell_effective_width / 2) -
                                          (item.sizeHint().width() / 2))
                    y_gap_to_bottom = self.cell_height \
                        - item.sizeHint().height()
                    # Place item
                    item.setGeometry(QRect(
                        QPoint(int(x + added_width + x_gap_to_centre),
                               int(y + y_gap_to_bottom)),
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
    def __init__(self, parent=None,
                 min_cell_width=140, max_cell_width=200, cell_height=140):
        # type: (ShelvesWidget, QWidget | None, int, int, int) -> None
        super().__init__(parent)
        self._scroll = QScrollArea(self)
        # Unlike widgets and layouts, scroll areas have a solid background you
        #  can’t draw behind by default.
        self._scroll.setStyleSheet('background: transparent')
        self._scroll.setWidgetResizable(True)
        # Wrapper widget to contain shelves layout
        self.container = QWidget(self._scroll)
        self._layout = ShelvesLayout(
            self.container, min_cell_width, max_cell_width, cell_height)
        self.container.setLayout(self._layout)
        self._scroll.setWidget(self.container)
        # Layout for us (this very widget) to put the scroll area in
        outer_layout = QGridLayout(self)
        outer_layout.addWidget(self._scroll)
        outer_layout.setSpacing(0)
        outer_layout.setContentsMargins(0, 0, 0, 0)

    def addWidget(self, widget):
        # type: (ShelvesWidget, QWidget) -> None
        self._layout.addWidget(widget)

    def clearWidgets(self):
        # type: (ShelvesWidget) -> None
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

    def setContentsMargins(  # type: ignore[override]
            self, left, top, right, bottom):
        # type: (ShelvesWidget, int, int, int, int) -> None
        self._layout.setContentsMargins(left, top, right, bottom)


if TYPE_CHECKING:
    from qt import QLayoutItem  # noqa: F401
