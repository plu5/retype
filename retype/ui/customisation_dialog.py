import os
import logging
from copy import deepcopy
from base64 import b64encode
from qt import (QWidget, QFormLayout, QVBoxLayout, QLabel, QLineEdit,
                QHBoxLayout, QFrame, QPushButton, QToolBox, QCheckBox,
                QSpinBox, QListView, QToolButton, QDialogButtonBox,
                QAbstractListModel, Qt, QStyledItemDelegate, QStyle,
                QApplication, QRectF, QTextDocument, QFileDialog, pyqtSignal,
                QModelIndex, QItemSelectionModel, QMessageBox, QDialog, QSize,
                QFont, QFontComboBox)

from retype.extras.dict import SafeDict
from retype.constants import default_config, iswindows

logger = logging.getLogger(__name__)

DEFAULTS = default_config
NESTED_RAW_DICT_KEYS = ['rdict', 'sdict']


def hline():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


def pxspinbox(value=0, suffix=" px"):
    sb = QSpinBox()
    sb.setSuffix(suffix)
    sb.setMaximum(10000)
    sb.setValue(value)
    return sb


def npxspinbox(value):
    sb = pxspinbox()
    sb.setMinimum(-10000)
    sb.setValue(value)
    return sb


def descl(text):
    desc = QLabel(text)
    desc.setWordWrap(True)
    return desc


class CustomisationDialog(QDialog):
    def __init__(self, config, window, saveConfig, prevView,
                 getBookViewFontSize, parent=None):
        QDialog.__init__(self, parent, Qt.WindowType.WindowCloseButtonHint)
        # The base config (no uncommitted modifications)
        self.config = SafeDict(deepcopy(DEFAULTS), {}, NESTED_RAW_DICT_KEYS)
        self.config.update(config)
        # The config with uncommitted modifications (any modifications will be
        #  applied to this one)
        self.config_edited = self.config.deepcopy()

        self.saveConfig = saveConfig
        self.prevView = prevView
        self.window = window
        self.getBookViewFontSize = getBookViewFontSize

        self._initUI()
        self.setModal(True)
        self.setWindowTitle("Customise retype")

    def sizeHint(self):
        return QSize(400, 500)

    def _initUI(self):
        self.selectors = {}

        tbox = QToolBox()
        tbox.addItem(self._pathSettings(), "Paths")
        tbox.addItem(self._consoleSettings(), "Console")
        tbox.addItem(self._bookviewSettings(), "Book View")
        tbox.addItem(self._sdictSettings(), "Line splits")
        tbox.addItem(self._rdictSettings(), "Replacements")
        tbox.addItem(self._windowSettings(), "Window geometry")

        lyt = QVBoxLayout(self)
        lyt.addWidget(tbox)
        lyt.addWidget(hline())
        self.revert_btn = QPushButton("Revert")
        self.revert_btn.setToolTip("Revert changes")
        self.revert_btn.setEnabled(False)
        StandardButton = QDialogButtonBox.StandardButton
        btnbox = QDialogButtonBox(StandardButton.Close |
                                  StandardButton.Save |
                                  StandardButton.RestoreDefaults)
        btnbox.addButton(self.revert_btn,
                         QDialogButtonBox.ButtonRole.DestructiveRole)
        lyt.addWidget(btnbox)
        btnbox.accepted.connect(self.accept)
        btnbox.rejected.connect(self.reject)
        self.revert_btn.clicked.connect(self.revert)
        self.restore_btn = btnbox.button(StandardButton.RestoreDefaults)
        self.restore_btn.clicked.connect(self.restoreDefaults)
        self.restore_btn.setEnabled(self.config.raw != DEFAULTS)


    def _pathSettings(self):
        plib = QWidget()
        lyt = QFormLayout(plib)

        # user_dir
        lyt.addRow(QLabel("Location for the save and config files."))
        self.selectors['user_dir'] = PathSelector(
            self.config_edited['user_dir'])
        self.selectors['user_dir'].changed.connect(
            lambda t: self.update("user_dir", t))
        lyt.addRow("User dir:", self.selectors['user_dir'])
        lyt.addRow(hline())
        # library_paths
        lyt.addRow(QLabel("Library search paths:"))
        self.selectors['library_paths'] = LibraryPathsWidget(
            self.config_edited['library_paths'])
        self.selectors['library_paths'].changed.connect(
            lambda paths: self.update("library_paths", paths))
        lyt.addRow(self.selectors['library_paths'])

        return plib

    def _consoleSettings(self):
        pcon = QWidget()
        lyt = QFormLayout(pcon)

        # prompt
        lyt.addRow(descl("Prompt console commands must be prefixed by. Can be\
 any length, including empty if you do not want to prefix them with anything."
                         ))
        self.selectors['prompt'] = PromptEdit(self.config_edited['prompt'])
        self.selectors['prompt'].textChanged.connect(
            lambda t: self.update("prompt", t))
        lyt.addRow("Prompt:", self.selectors['prompt'])

        # console font
        self.selectors['console_font'] = ConsoleFontSelector(
            self.config_edited['console_font'])
        self.selectors['console_font'].currentFontChanged.connect(
            lambda f: self.update("console_font", f.family()))
        lyt.addRow("Console font:", self.selectors['console_font'])

        # Windows-only: system console
        if iswindows:
            lyt.addRow(hline())
            hide_sysconsole_checkbox = CheckBox(
                "Hide System Console window on UI load (Windows-only)")
            hide_sysconsole_checkbox.setChecked(
                self.config_edited.get('hide_sysconsole', True))
            hide_sysconsole_checkbox.stateChanged.connect(
                lambda t: self.update("hide_sysconsole", t))
            self.selectors['hide_sysconsole'] = hide_sysconsole_checkbox
            lyt.addRow(hide_sysconsole_checkbox)

        return pcon

    def _sdictSettings(self):
        psep = QWidget()
        lyt = QFormLayout(psep)
        lyt.addRow(descl("Configure substrings that split the text into lines.\
 The 'keep' argument determines whether the substring still needs to be typed\
 or gets skipped over."))
        self.selectors['sdict'] = SDictWidget(
            deepcopy(self.config_edited['sdict']))
        self.selectors['sdict'].changed.connect(
            lambda sdict: self.update("sdict", sdict))
        lyt.addRow(self.selectors['sdict'])

        lyt.addRow(hline())
        enter_newline_checkbox = CheckBox(
            "Newline characters advance automatically\n\
(if off, requires pressing Enter at the end of a line)")
        enter_newline_checkbox.setChecked(
            not self.config_edited.get('enter_newline', False))
        enter_newline_checkbox.stateChanged.connect(
            lambda t: self.update("enter_newline", not t))
        self.selectors['enter_newline'] = enter_newline_checkbox
        lyt.addRow(enter_newline_checkbox)

        return psep

    def _rdictSettings(self):
        prep = QWidget()
        lyt = QFormLayout(prep)
        lyt.addRow(descl("Configure substrings that can be typeable\
 by any one of the set comma-separated list of replacements. This is useful\
 for unicode characters that you don’t have an easy way to input. Each\
 replacement should be of equal length to the original substring."))
        self.selectors['rdict'] = RDictWidget(
            deepcopy(self.config_edited['rdict']))
        self.selectors['rdict'].changed.connect(
            lambda rdict: self.update("rdict", rdict))
        lyt.addRow(self.selectors['rdict'])

        return prep

    def _windowSettings(self):
        self.selectors['window'] = WindowGeometrySelector(
            self.window, self.config_edited['window'])
        self.selectors['window'].changed.connect(
            lambda dims: self.update("window", dims))
        self.window.closing.connect(self.maybeSaveCertainThings)

        return self.selectors['window']

    def _bookviewSettings(self):
        self.selectors['bookview'] = BookViewSettingsWidget(
            self.config_edited['bookview'])
        self.selectors['bookview'].changed.connect(
            lambda x: self.update("bookview", x))

        return self.selectors['bookview']

    def update(self, name, new_value):
        self.config_edited[name] = new_value
        logger.debug("config_edited updated to: {}".format(
            self.config_edited.raw))

        self.revert_btn.setEnabled(self.config_edited.raw != self.config.raw)
        self.restore_btn.setEnabled(self.config_edited.raw != DEFAULTS)

    def accept(self):
        # User dir validation
        if not os.path.exists(self.config_edited['user_dir']):
            ret = QMessageBox.warning(
                self, "retype",
                "Cannot find specified user_dir path.\n"
                "Reset it to former value?",
                QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.config_edited['user_dir'] = self.config['user_dir']
                self.selectors['user_dir'].set_(self.config['user_dir'])
            return

        # Library paths validation
        for path in self.config_edited['library_paths']:
            if not os.path.exists(path):
                ret = QMessageBox.warning(
                    self, "retype",
                    "At least one library search path is invalid.")
                return

        # Replacements validation
        if '' in self.config_edited['rdict'] or \
           [] in self.config_edited['rdict'].values():
            ret = QMessageBox.warning(
                self, "retype", "At least one replacement is invalid.")
            return

        # Save
        self.saveConfig.emit(self.config_edited.raw)
        # Update base config
        self.config = self.config_edited.deepcopy()

        self.revert_btn.setEnabled(False)

    def setSelectors(self, config):
        for key, selector in self.selectors.items():
            selector.set_(config[key])

    def restoreDefaults(self):
        self.config_edited = SafeDict(
            deepcopy(DEFAULTS), {}, NESTED_RAW_DICT_KEYS)
        self.setSelectors(self.config_edited)

        self.restore_btn.setEnabled(False)

    def revert(self):
        self.config_edited = self.config.deepcopy()
        self.setSelectors(self.config_edited)

        self.revert_btn.setEnabled(False)

    def maybeSaveCertainThings(self):
        shouldSave = False

        if self.config['window']['save_on_quit']:
            logger.debug("Saving window geometry")
            values = self.selectors['window'].valuesByWindow()
            self.config['window'].update(values)
            shouldSave = True

        if self.config['window'].get('save_splitters_on_quit', True):
            logger.debug("Saving splitters states")
            for name, splitter in self.window.splitters.items():
                self.config['window'][f'{name}_splitter_state'] =\
                    b64encode(splitter.saveState()).decode('ascii')
            shouldSave = True

        if self.config['bookview']['save_font_size_on_quit']:
            logger.debug("Saving BookView’s font size")
            self.config['bookview']['font_size'] = self.getBookViewFontSize()
            shouldSave = True

        if shouldSave:
            self.saveConfig.emit(self.config.raw)


class CheckBox(QCheckBox):
    changed = pyqtSignal(bool)

    def __init__(self, desc, parent=None):
        QCheckBox.__init__(self, desc, parent)
        self.default_value = False

    def value(self):
        return self.isChecked()

    def set_(self, value):
        self.setChecked(value or self.default_value)


class PathSelector(QWidget):
    changed = pyqtSignal(str)

    def __init__(self, path, parent=None, window_title="Select path"):
        QWidget.__init__(self, parent)
        self.window_title = window_title

        lyt = QHBoxLayout(self)
        lyt.setContentsMargins(0, 0, 0, 0)

        self.path_edit = QLineEdit(path)
        self.path_edit.textChanged.connect(lambda t: self.changed.emit(t))
        lyt.addWidget(self.path_edit)

        self.browse_button = QToolButton(self)
        # TODO: add browse icon
        self.browse_button.setText("...")
        self.browse_button.clicked.connect(self.browse)
        lyt.addWidget(self.browse_button)

        self.setFocusProxy(self.path_edit)

    def browse(self):
        # The set focus lines are a workaround to a qt bug which causes the
        #  application to crash after the QFileDialog is invoked from a
        #  delegate editor
        self.browse_button.setFocus()
        path = QFileDialog.getExistingDirectory(self, self.window_title)
        self.browse_button.setFocus()

        if path:
            self.path_edit.setText(path)

    def value(self):
        return self.path_edit.text()

    def set_(self, value):
        self.path_edit.setText(value)


class Delegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self, parent)
        self.spacing = 5

    def toDoc(self, index):
        doc = QTextDocument()
        doc.setHtml(index.data())
        return doc

    def paint(self, painter, option, index):
        painter.save()
        painter.setClipRect(QRectF(option.rect))

        if hasattr(QStyle, 'CE_ItemViewItem'):
            QApplication.style().drawControl(
                QStyle.ControlElement.CE_ItemViewItem, option, painter)
        elif option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        start = option.rect.topLeft()
        start.setY(start.y() + self.spacing)
        painter.translate(start)

        self.toDoc(index).drawContents(painter)
        painter.restore()

    def sizeHint(self, option, index):
        size = self.toDoc(index).size().toSize()
        size.setHeight(size.height() + self.spacing*2)
        return size


class PathDelegate(Delegate):
    def __init__(self, parent=None):
        Delegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        return PathSelector(index.data(Qt.ItemDataRole.EditRole), parent)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.value(), Qt.EditRole)


class LibraryPathsModel(QAbstractListModel):
    changed = pyqtSignal(list)
    INVALID_TEMPLATE = '''<span style="color:red">{}</span>'''

    def __init__(self, paths, parent=None):
        QAbstractListModel.__init__(self, parent)
        self.paths = paths

    def rowCount(self, parent):
        return len(self.paths)

    def data(self, index, role):
        row = index.row()
        if row < 0 or row >= len(self.paths):
            return None

        path = self.paths[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if os.path.exists(path):
                return path
            else:
                return self.INVALID_TEMPLATE.format(path)
        elif role == Qt.ItemDataRole.EditRole:
            return path

        return None

    def setData(self, index, data, role):
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            self.paths[index.row()] = str(data)
            self.dataChanged.emit(index, index, [role])
            self.changed.emit(self.paths)
            return True
        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        return (QAbstractListModel.flags(self, index) |
                Qt.ItemFlag.ItemIsEditable)

    def insertRows(self, position=None, rows=1, parent=QModelIndex()):
        if position is None:
            position = len(self.paths)
        self.beginInsertRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            self.paths.insert(position + row, "")
            self.changed.emit(self.paths)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent):
        self.beginRemoveRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            del self.paths[position + row]
            self.changed.emit(self.paths)
        self.endRemoveRows()
        return True


class LibraryPathsWidget(QWidget):
    changed = pyqtSignal(list)

    def __init__(self, library_paths, parent=None):
        QWidget.__init__(self, parent)

        lyt = QFormLayout(self)
        lyt.setContentsMargins(0, 0, 0, 0)
        self.view = QListView()
        self.view.setItemDelegate(PathDelegate())
        self.setModel(library_paths)
        lyt.addRow(self.view)
        pbuttons = QWidget()
        pbl = QHBoxLayout(pbuttons)
        add_btn = QPushButton("Add path")
        add_btn.clicked.connect(self.addPath)
        pbl.addWidget(add_btn)
        remove_btn = QPushButton("Remove path")
        remove_btn.clicked.connect(self.removePath)
        pbl.addWidget(remove_btn)
        modify_btn = QPushButton("Modify path")
        modify_btn.clicked.connect(self.modifyPath)
        pbl.addWidget(modify_btn)
        pbl.setContentsMargins(0, 0, 0, 0)
        lyt.addRow(pbuttons)

    def setModel(self, library_paths):
        self.model = LibraryPathsModel(library_paths)
        self.view.setModel(self.model)
        self.model.changed.connect(lambda paths: self.changed.emit(paths))

    def addPath(self):
        self.model.insertRows()
        row = self.model.rowCount(QModelIndex())-1
        index = self.model.index(row, 0)
        self.view.selectionModel().setCurrentIndex(
            index, QItemSelectionModel.ClearAndSelect)
        self.view.edit(index)

    def selectedRowIndex(self):
        selectionModel = self.view.selectionModel()
        if selectionModel.hasSelection():
            index = selectionModel.selectedRows()[0]
            return index
        return False

    def removePath(self):
        index = self.selectedRowIndex()
        if index:
            self.model.removeRows(index.row(), 1, QModelIndex())

    def modifyPath(self):
        index = self.selectedRowIndex()
        if index:
            self.view.edit(index)

    def set_(self, library_paths):
        self.setModel(library_paths)


class PromptEdit(QLineEdit):
    def __init__(self, prompt, parent=None):
        QLineEdit.__init__(self, parent)
        self.set_(prompt)

    def set_(self, prompt):
        self.setText(prompt)


class ConsoleFontSelector(QFontComboBox):
    def __init__(self, font, parent=None):
        QLineEdit.__init__(self, parent)
        self.set_(font)

    def set_(self, font):
        self.setCurrentFont(QFont(font))


class ListView(QListView):
    def __init__(self, *args):
        QListView.__init__(self, *args)

    def sizeHint(self):
        size = QListView.sizeHint(self)
        size.setHeight(10)
        return size


class SDictModel(QAbstractListModel):
    TEMPLATE = '''<p><b>Substring:</b> <code>'<u style="color:blue">{0}</u>' ({1})</code><br>
Keep: <code><b>{2}</b></code></p>'''
    INVALID_TEMPLATE = '<div style="color:red">' + TEMPLATE + '</div>'
    changed = pyqtSignal(dict)

    def __init__(self, sdict, parent=None):
        QAbstractListModel.__init__(self, parent)
        self.sdict = sdict
        self.order = list(sdict)

    def rowCount(self, parent):
        return len(self.sdict)

    def data(self, index, role):
        row = index.row()
        if row < 0 or row >= len(self.order):
            return None

        substring = self.order[row]
        escaped_unicode = str(substring.encode("unicode_escape")
                              .decode("latin1"))

        if role == Qt.ItemDataRole.DisplayRole:
            if substring == '' or not self.sdict[substring]:
                return self.INVALID_TEMPLATE.format(
                    substring, escaped_unicode, self.sdict[substring]['keep'])
            return self.TEMPLATE.format(
                substring, escaped_unicode, self.sdict[substring]['keep'])
        elif role == Qt.ItemDataRole.EditRole:
            return (substring, self.sdict[substring]['keep'])

        return None

    def insertRows(self, position=None, rows=1, parent=QModelIndex()):
        if position is None:
            position = len(self.order)
        self.beginInsertRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            if '' in self.sdict:
                break
            self.order.insert(position + row, "")
            self.sdict[''] = {'keep': True}
            self.changed.emit(self.sdict)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent):
        self.beginRemoveRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            del self.sdict[self.order[position + row]]
            del self.order[position + row]
            self.changed.emit(self.sdict)
        self.endRemoveRows()
        return True

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        return (QAbstractListModel.flags(self, index) |
                Qt.ItemFlag.ItemIsEditable)

    def setData(self, index, data, role):
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            del self.sdict[self.order[index.row()]]
            self.order[index.row()] = data[0]
            self.sdict[data[0]] = data[1]
            self.dataChanged.emit(index, index, [role])
            self.changed.emit(self.sdict)
            return True
        return False


class SDictEntryEditor(QWidget):
    def __init__(self, substr, keep, parent=None):
        QWidget.__init__(self, parent)

        lyt = QFormLayout(self)
        self.substr_e = QLineEdit(substr)
        self.keep_e = QCheckBox()
        self.keep_e.setChecked(keep)
        lyt.addRow("Substring:", self.substr_e)
        lyt.addRow("Keep:", self.keep_e)

        # Background
        self.setStyleSheet("background-color:#CDE8FF")
        self.setAttribute(Qt.WA_StyledBackground, True)

        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.setSpacing(1)

    def substr(self):
        return self.substr_e.text()

    def keep(self):
        return {'keep': self.keep_e.isChecked()}


class SDictDelegate(Delegate):
    def __init__(self, parent=None):
        Delegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        data = index.data(Qt.ItemDataRole.EditRole)
        return SDictEntryEditor(*data, parent)

    def setModelData(self, editor, model, index):
        substr = editor.substr()
        keep = editor.keep()

        model.setData(index, [substr, keep], Qt.ItemDataRole.EditRole)


class SDictWidget(QWidget):
    changed = pyqtSignal(dict)

    def __init__(self, sdict, parent=None):
        QWidget.__init__(self, parent)

        lyt = QFormLayout(self)
        lyt.setContentsMargins(0, 0, 0, 0)
        self.view = ListView()
        self.view.setItemDelegate(SDictDelegate())
        self.setModel(sdict)
        lyt.addRow(self.view)

        pbuttons = QWidget()
        pbl = QHBoxLayout(pbuttons)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.addEntry)
        pbl.addWidget(add_btn)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.removeEntry)
        pbl.addWidget(remove_btn)
        modify_btn = QPushButton("Modify")
        modify_btn.clicked.connect(self.modifyEntry)
        pbl.addWidget(modify_btn)
        pbl.setContentsMargins(0, 0, 0, 0)
        lyt.addRow(pbuttons)

    def setModel(self, sdict):
        self.model = SDictModel(sdict)
        self.model.changed.connect(lambda sdict: self.changed.emit(sdict))
        self.view.setModel(self.model)

    def addEntry(self):
        self.model.insertRows()
        row = self.model.rowCount(QModelIndex())-1
        index = self.model.index(row, 0)
        self.view.selectionModel().setCurrentIndex(
            index, QItemSelectionModel.ClearAndSelect)
        self.view.edit(index)

    def selectedRowIndex(self):
        selectionModel = self.view.selectionModel()
        if selectionModel.hasSelection():
            index = selectionModel.selectedRows()[0]
            return index
        return False

    def removeEntry(self):
        index = self.selectedRowIndex()
        if index:
            self.model.removeRows(index.row(), 1, QModelIndex())

    def modifyEntry(self):
        index = self.selectedRowIndex()
        if index:
            self.view.edit(index)

    def set_(self, sdict):
        self.setModel(sdict)


class RDictModel(QAbstractListModel):
    TEMPLATE = '''<p><b>Substring:</b> <code>'<u style="color:blue">{0}</u>' ({1})</code><br>
Replacements list: <code><b>{2}</b></code></p>'''
    INVALID_TEMPLATE = '<div style="color:red">' + TEMPLATE + '</div>'
    changed = pyqtSignal(dict)

    def __init__(self, rdict, parent=None):
        QAbstractListModel.__init__(self, parent)
        self.rdict = rdict
        self.order = list(rdict)

    def rowCount(self, parent):
        return len(self.rdict)

    def data(self, index, role):
        row = index.row()
        if row < 0 or row >= len(self.order):
            return None

        substring = self.order[row]
        escaped_unicode = str(substring.encode("unicode_escape")
                              .decode("latin1"))

        if role == Qt.ItemDataRole.DisplayRole:
            if substring == '' or not self.rdict[substring]:
                return self.INVALID_TEMPLATE.format(substring, escaped_unicode,
                                                    self.rdict[substring])
            return self.TEMPLATE.format(substring, escaped_unicode,
                                        self.rdict[substring])
        elif role == Qt.ItemDataRole.EditRole:
            return (substring, self.rdict[substring])

        return None

    def insertRows(self, position=None, rows=1, parent=QModelIndex()):
        if position is None:
            position = len(self.order)
        self.beginInsertRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            if '' in self.rdict:
                break
            self.order.insert(position + row, "")
            self.rdict[''] = ""
            self.changed.emit(self.rdict)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent):
        self.beginRemoveRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            del self.rdict[self.order[position + row]]
            del self.order[position + row]
            self.changed.emit(self.rdict)
        self.endRemoveRows()
        return True

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        return (QAbstractListModel.flags(self, index) |
                Qt.ItemFlag.ItemIsEditable)

    def setData(self, index, data, role):
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            del self.rdict[self.order[index.row()]]
            self.order[index.row()] = data[0]
            self.rdict[data[0]] = data[1]
            self.dataChanged.emit(index, index, [role])
            self.changed.emit(self.rdict)
            return True
        return False


class RDictEntryEditor(QWidget):
    def __init__(self, substr, reps, parent=None):
        QWidget.__init__(self, parent)

        lyt = QFormLayout(self)
        self.substr_e = QLineEdit(substr)
        self.reps_e = QLineEdit(','.join(reps))
        lyt.addRow("Substring:", self.substr_e)
        lyt.addRow("Replacements (separated by ,):", self.reps_e)

        # Background
        self.setStyleSheet("background-color:#CDE8FF")
        self.setAttribute(Qt.WA_StyledBackground, True)

        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.setSpacing(1)

    def substr(self):
        return self.substr_e.text()

    def reps(self):
        return self.reps_e.text().split(',')


class RDictDelegate(Delegate):
    def __init__(self, parent=None):
        Delegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        data = index.data(Qt.ItemDataRole.EditRole)
        return RDictEntryEditor(*data, parent)

    def setModelData(self, editor, model, index):
        substr = editor.substr()
        reps = editor.reps()

        # remove duplicates
        reps = list(dict.fromkeys(reps))

        # remove reps that are of incorrect length
        for i, rep in enumerate(reps):
            if len(rep) != len(substr):
                del reps[i]

        model.setData(index, [substr, reps], Qt.ItemDataRole.EditRole)


class RDictWidget(QWidget):
    changed = pyqtSignal(dict)

    def __init__(self, rdict, parent=None):
        QWidget.__init__(self, parent)

        lyt = QFormLayout(self)
        lyt.setContentsMargins(0, 0, 0, 0)
        self.view = ListView()
        self.view.setItemDelegate(RDictDelegate())
        self.setModel(rdict)
        lyt.addRow(self.view)

        pbuttons = QWidget()
        pbl = QHBoxLayout(pbuttons)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.addEntry)
        pbl.addWidget(add_btn)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.removeEntry)
        pbl.addWidget(remove_btn)
        modify_btn = QPushButton("Modify")
        modify_btn.clicked.connect(self.modifyEntry)
        pbl.addWidget(modify_btn)
        pbl.setContentsMargins(0, 0, 0, 0)
        lyt.addRow(pbuttons)

    def setModel(self, rdict):
        self.model = RDictModel(rdict)
        self.model.changed.connect(lambda rdict: self.changed.emit(rdict))
        self.view.setModel(self.model)

    def addEntry(self):
        self.model.insertRows()
        row = self.model.rowCount(QModelIndex())-1
        index = self.model.index(row, 0)
        self.view.selectionModel().setCurrentIndex(
            index, QItemSelectionModel.ClearAndSelect)
        self.view.edit(index)

    def selectedRowIndex(self):
        selectionModel = self.view.selectionModel()
        if selectionModel.hasSelection():
            index = selectionModel.selectedRows()[0]
            return index
        return False

    def removeEntry(self):
        index = self.selectedRowIndex()
        if index:
            self.model.removeRows(index.row(), 1, QModelIndex())

    def modifyEntry(self):
        index = self.selectedRowIndex()
        if index:
            self.view.edit(index)

    def set_(self, rdict):
        self.setModel(rdict)


class WindowGeometrySelector(QWidget):
    changed = pyqtSignal(dict)

    def __init__(self, window, dims, parent=None):
        QWidget.__init__(self, parent)

        self.window = window
        self.dims = dims

        lyt = QFormLayout(self)

        self.selectors = {}

        self.selectors['save_splitters_on_quit'] = QCheckBox(
            "Save state of splitters on quit")
        self.selectors['save_splitters_on_quit'].stateChanged.connect(
            lambda state: self.updateDim('save_splitters_on_quit', state))

        self.selectors['save_on_quit'] = QCheckBox(
            "Save window size and position on quit")
        self.selectors['save_on_quit'].stateChanged.connect(self.setSaveOnQuit)

        lyt.addRow(self.selectors['save_splitters_on_quit'])
        lyt.addRow(self.selectors['save_on_quit'])
        lyt.addRow(hline())

        # when save on quit is checked, the following is greyed out
        self.selectors['x'] = npxspinbox(dims['x'] or 0)
        self.selectors['y'] = npxspinbox(dims['y'] or 0)
        self.selectors['w'] = pxspinbox(dims['w'])
        self.selectors['h'] = pxspinbox(dims['h'])
        self.cur_btn = QPushButton("Set values according to current window")
        self.cur_btn.clicked.connect(self.setSelectorsValuesByWindow)

        self.dim_selectors = {k: v for k, v in self.selectors.items()
                              if k in 'xywh'}

        for name, selector in self.dim_selectors.items():
            label = name.title() + ':'
            lyt.addRow(label, selector)
            self.connectSelector(name, selector.valueChanged)

        lyt.addRow(self.cur_btn)

        self.selectors['save_splitters_on_quit'].setChecked(
            dims['save_splitters_on_quit'])
        self.selectors['save_on_quit'].setChecked(dims['save_on_quit'])

    def setSaveOnQuit(self, state):
        controls_to_toggle = [*list(self.dim_selectors.values()), self.cur_btn]
        for control in controls_to_toggle:
            disabled_bool = True if state else False
            control.setDisabled(disabled_bool)

        self.updateDim('save_on_quit', state)

    def valuesByWindow(self):
        pos = self.window.pos()
        size = self.window.size()

        values = {}
        values['x'] = pos.x()
        values['y'] = pos.y()
        values['w'] = size.width()
        values['h'] = size.height()

        return values

    def setSelectorsValuesByWindow(self):
        values = self.valuesByWindow()
        self.dims.update(values)
        self.set_(self.dims)
        self.changed.emit(self.dims.raw)

    def connectSelector(self, name, signal):
        signal.connect(lambda val: self.updateDim(name, val))

    def updateDim(self, name, val):
        self.dims[name] = val
        self.changed.emit(self.dims.raw)

    def set_(self, dims):
        for key, selector in self.selectors.items():
            if key in ['save_splitters_on_quit', 'save_on_quit']:
                selector.setChecked(dims[key])
                continue
            value = dims[key] if dims[key] is not None else 0
            selector.setValue(value)


class BookViewSettingsWidget(QWidget):
    changed = pyqtSignal(dict)

    def __init__(self, bookview_settings, parent=None):
        QWidget.__init__(self, parent)

        self.settings = bookview_settings
        self.selectors = {}

        save_font_size_checkbox = QCheckBox("Save font size on quit")
        save_font_size_checkbox.stateChanged.connect(
            self.setSaveFontSizeOnQuit)
        self.selectors['save_font_size_on_quit'] = save_font_size_checkbox

        self.font_size_selector = pxspinbox(self.settings['font_size'], " pt")
        self.font_size_selector.valueChanged.connect(
            lambda val: self.updateSetting('font_size', val))
        self.selectors['font_size'] = self.font_size_selector

        self.font_selector = QFontComboBox()
        self.font_selector.currentFontChanged.connect(
            lambda val: self.updateSetting('font', val.family()))
        self.selectors['font'] = self.font_selector

        lyt = QFormLayout(self)
        lyt.addRow(save_font_size_checkbox)
        lyt.addRow(hline())
        lyt.addRow("Default font size:", self.font_size_selector)
        lyt.addRow("Font family:", self.font_selector)

        self.set_(bookview_settings)

    def updateSetting(self, name, val):
        self.settings[name] = val
        self.changed.emit(self.settings.raw)

    def setSaveFontSizeOnQuit(self, state):
        self.font_size_selector.setDisabled(True if state else False)
        self.updateSetting('save_font_size_on_quit', state)

    def set_(self, settings):
        for key, selector in self.selectors.items():
            if key == 'save_font_size_on_quit':
                state = settings[key]
                selector.setChecked(state)
                continue
            elif key == 'font':
                selector.setCurrentFont(QFont(settings[key]))
                continue
            value = settings[key]
            selector.setValue(value)
