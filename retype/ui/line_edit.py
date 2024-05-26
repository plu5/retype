"""QPlainTextEdit subclass which mimics QLineEdit. The idea is to make it
 hotswappable for QLineEdit with no changes needed, so that you can have a
 QLineEdit without its inherent limitations, like not being able to modify the
 undo behaviour, not being able to use QCursor, etc.
Adapted from ssokolow’s OneLineSpellTextEdit:
https://gist.github.com/ssokolow/abb20a30415fa4debce912c38060ca6a

NOTE:
* textEdited probably works differently from QLineEdit’s textEdited, because I
  am not sure yet how to replicate it exactly. For now it emits when the text
  changes by user key press.
* Unimplemented signals: editingFinished, inputRejected"""

import sys
from qt import (QPlainTextEdit, QWidget, QKeySequence,
                pyqtSlot, pyqtSignal, QFocusEvent, QShortcut, QTextOption,
                QTextCursor, Qt, QVBoxLayout,
                # for the demo only:
                QApplication, QLineEdit)


class LineEdit(QWidget):
    returnPressed = pyqtSignal()
    textChanged = pyqtSignal(str)
    textEdited = pyqtSignal(str)
    selectionChanged = pyqtSignal()
    cursorPositionChanged = pyqtSignal(int, int)

    def __init__(self, parent=None, *args):
        super().__init__(parent)
        self.edit = _LineEdit(self, *args)
        self.edit.textChanged.connect(self._emitTextChanged)
        self.edit.returnPressed.connect(self.returnPressed)
        self.edit.selectionChanged.connect(self.selectionChanged)
        self.edit.cursorPositionChanged.connect(
            self._emitCursorPositionChanged)
        self._oldPos = self.edit.textCursor().position()
        self.passed = False
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.edit)

    def setAccessibleName(self, name):
        self.edit.setAccessibleName(name)

    def setStyleSheet(self, ss):
        self.edit.setStyleSheet(ss)

    def setSizePolicy(self, hsp, vsp):
        self.edit.setSizePolicy(hsp, vsp)
        super().setSizePolicy(hsp, vsp)

    def keyPressEvent(self, e):
        if not self.passed:
            self.edit.transferFocus(e)
        self.passed = False

    def text(self):
        return self.edit.toPlainText()

    def setText(self, text):
        self.edit.setPlainText(text)

    def setPlainText(self, text):
        self.edit.setPlainText(text)

    def _emitTextChanged(self):
        text = self.edit.toPlainText()
        self.textChanged.emit(text)
        if self.edit._isUserModified:
            self.textEdited.emit(text)
            self.edit._isUserModified = False

    def _emitCursorPositionChanged(self):
        newPos = self.edit.textCursor().position()
        self.cursorPositionChanged.emit(self._oldPos, newPos)
        self._oldPos = newPos

    def minimumSizeHint(self):
        return self.edit.minimumSizeHint()

    def sizeHint(self):
        return self.edit.sizeHint()

    def font(self):
        return self.edit.font()

    def setFont(self, *args):
        self.edit.setFont(*args)

    def textCursor(self):
        return self.edit.textCursor()

    def setTextCursor(self, *args):
        self.edit.setTextCursor(*args)

    def moveCursor(self, *args):
        self.edit.moveCursor(*args)


class _LineEdit(QPlainTextEdit):
    returnPressed = pyqtSignal()
    overtype_changed = pyqtSignal(bool)

    def __init__(self, wrapper, *args):
        super().__init__(*args)

        # Internal QLineEdit element to get the minimum size hint from this
        #  instead of doing some crazy calculation which I cannot get
        #  working reliably. Perhaps a cheat.
        self.template = QLineEdit()

        # Set up expected Insert/Overwrite cursor mode toggle
        QShortcut(
            QKeySequence(
                self.tr("Insert", "Hotkey to toggle Insert/Overwrite")),
            self, self.cb_toggle_insert, context=Qt.WidgetShortcut)

        # Set up QPlainTextEdit to act like QLineEdit
        self.setSizePolicy(self.template.sizePolicy())
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWordWrapMode(QTextOption.NoWrap)
        self.setTabChangesFocus(True)
        self.textChanged.connect(self.cb_text_changed)

        self.wrapper = wrapper
        self._isUserModified = False  # used for textEdited signal logic

        self.setContentsMargins(0, 0, 0, 0)
        self.document().setDocumentMargin(3)

    def focusInEvent(self, e: QFocusEvent):
        """Override focusInEvent to mimic QLineEdit behaviour"""
        super().focusInEvent(e)

        # TODO: Are there any other things I'm supposed to be checking for?
        if e.reason() in (Qt.BacktabFocusReason, Qt.ShortcutFocusReason,
                          Qt.TabFocusReason):
            self.selectAll()

    def focusOutEvent(self, e: QFocusEvent):
        """Override focusOutEvent to mimic QLineEdit behaviour"""
        super().focusOutEvent(e)

        # TODO: Are there any other things I'm supposed to be checking for?
        if e.reason() in (Qt.BacktabFocusReason, Qt.MouseFocusReason,
                          Qt.ShortcutFocusReason, Qt.TabFocusReason):
            # De-select everything and move the cursor to the end
            cur = self.textCursor()
            cur.movePosition(QTextCursor.End)
            self.setTextCursor(cur)

    def minimumSizeHint(self):
        # """Redefine minimum size hint to match QLineEdit"""
        return self.template.minimumSizeHint()

    def setStyleSheet(self, ss):
        super().setStyleSheet(ss)
        self.template.setStyleSheet(ss)

    def sizeHint(self):
        """Reuse minimumSizeHint for sizeHint"""
        return self.minimumSizeHint()

    @pyqtSlot()
    def cb_text_changed(self):
        """Handler to enforce one-linedness on typing/pastes/etc.

        (Can't use self.setMaximumBlockCount(1) because it disables Undo/Redo)

        Feel free to subclass and override this for alternative behaviours
        such as converting a newline-separated list into a comma-separated list
        """
        if self.document().blockCount() > 1:
            self.document().setPlainText(
                self.document().firstBlock().text())

    @pyqtSlot()
    def cb_toggle_insert(self, target: bool = None):
        """Event handler for the Insert key"""
        if target is None:
            target = not self.overwriteMode()
        self.setOverwriteMode(target)
        self.overtype_changed.emit(target)

    def keyPressEvent(self, e):
        if e.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            self.returnPressed.emit()
        if e.text():
            self._isUserModified = True
        self.wrapper.passed = True
        self.wrapper.keyPressEvent(e)
        super().keyPressEvent(e)

    def transferFocus(self, e):
        """Like setFocus, except you can also pass a keyPress event from
 another widget. Only does so if no modifier keys (excluding Shift) are
 held."""
        if e.modifiers() in [Qt.KeyboardModifier.NoModifier,
                             Qt.KeyboardModifier.ShiftModifier]:
            self.setFocus()
            self.keyPressEvent(e)


# demo
if __name__ == '__main__':
    app = QApplication(sys.argv)

    win = QWidget()
    layout = QVBoxLayout()

    lineEdit = LineEdit()
    lineEdit.setPlainText("LineEdit")
    le = QLineEdit()
    le.setText("QLineEdit")
    print(lineEdit.sizeHint(), lineEdit.minimumSizeHint())
    print(le.sizeHint(), le.minimumSizeHint())

    layout.addWidget(lineEdit)
    layout.addWidget(le)
    win.setLayout(layout)
    win.show()

    sys.exit(app.exec_())
