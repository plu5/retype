import os
import logging
from copy import deepcopy
from base64 import b64encode
from qt import (QWidget, QFormLayout, QVBoxLayout, QLabel, QLineEdit,
                QHBoxLayout, QFrame, QPushButton, QCheckBox,
                QSpinBox, QListView, QToolButton, QDialogButtonBox,
                QAbstractListModel, Qt, QStyledItemDelegate, QStyle,
                QApplication, QRectF, QTextDocument, QFileDialog, pyqtSignal,
                QModelIndex, QItemSelectionModel, QMessageBox, QDialog, QSize,
                QFont, QFontComboBox, QComboBox, QPainter, QBrush,
                QColorDialog, QColor, QTreeView, QStandardItemModel,
                QAbstractItemView, QItemDelegate, QStandardItem, QSizePolicy)

from retype.extras.dict import SafeDict, update
from retype.constants import default_config, iswindows
from retype.services.theme import Theme, populateThemes, valuesFromQss
from retype.extras.qss import serialiseValuesDict
from retype.resource_handler import getStylePath
from retype.extras.widgets import (ScrollTabWidget, AdjustedStackedWidget,
                                   WrappedLabel)
from retype.extras.camel import spacecamel

logger = logging.getLogger(__name__)

DEFAULTS = default_config
NESTED_RAW_DICT_KEYS = ['rdict', 'sdict']
THEME_MODIFICATIONS_FILENAME = '__current__.qss'


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
    return WrappedLabel(text)


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
        return QSize(500, 500)

    def getUserDir(self):
        return self.config['user_dir']

    def _initUI(self):
        self.selectors = {}

        catw = CategorisedWidget()
        catw.add("Filesystem", "Paths", self._pathSettings())
        catw.add("User interface", "Theme", self._themeSettings())
        catw.add("User interface", "Console", self._consoleSettings())
        catw.add("User interface", "Book View", self._bookviewSettings())
        catw.add("User interface", "Window geometry", self._windowSettings())
        catw.add("Behaviour", "Line splits", self._sdictSettings())
        catw.add("Behaviour", "Replacements", self._rdictSettings())
        catw.postAddingCategories()

        lyt = QVBoxLayout(self)
        lyt.addWidget(catw)
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

    def _themeSettings(self):
        pth = QWidget()
        lyt = QFormLayout(pth)

        preset_lyt = QHBoxLayout()
        themes = QComboBox()
        themes.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        preset_lyt.addWidget(themes, 1)
        apply_btn = QPushButton("Apply")
        apply_btn.setToolTip("Apply selected preset")
        preset_lyt.addWidget(apply_btn)
        export_btn = QPushButton("Export")
        export_btn.setToolTip("Export saved modifications as new preset")
        preset_lyt.addWidget(export_btn)
        lyt.addRow(QLabel("Preset:"), preset_lyt)
        lyt.addRow(descl("To import a preset, place the qss file in the\
 'style' subfolder in either the user dir or application folder, and restart\
 retype."))
        lyt.addRow(hline())

        user_dir = self.getUserDir()
        populateThemes([getStylePath(), getStylePath(user_dir)])
        for t in Theme.themes:
            if t != THEME_MODIFICATIONS_FILENAME.rstrip('.qss'):
                themes.addItem(t)

        t = ThemeWidget(user_dir)
        self.theme = t
        self.theme.changed.connect(self.themeUpdate)
        lyt.addRow(self.theme)

        apply_btn.clicked.connect(lambda: t.applyTheme(themes.currentText()))
        export_btn.clicked.connect(lambda: t.exportCurrent(self.getUserDir()))

        return pth

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
            hide_sysconsole_checkbox.changed.connect(
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
        auto_newline_checkbox = CheckBox(
            "Newline characters advance automatically\n\
(if off, requires pressing Enter at the end of a line)")
        auto_newline_checkbox.setChecked(self.config_edited['auto_newline'])
        auto_newline_checkbox.changed.connect(
            lambda t: self.update("auto_newline", t))
        self.selectors['auto_newline'] = auto_newline_checkbox
        lyt.addRow(auto_newline_checkbox)

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

    def themeUpdate(self):
        revert = restore = False

        if self.theme.committed is False:
            revert = True
        else:
            revert = self.config_edited.raw != self.config.raw

        if self.theme.isDefault() is False:
            restore = True
        else:
            restore = self.config_edited.raw != DEFAULTS

        self.revert_btn.setEnabled(revert)
        self.restore_btn.setEnabled(restore)

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

        # Save theme
        self.theme.saveCurrent(getStylePath(self.getUserDir()))

        self.revert_btn.setEnabled(False)

    def setSelectors(self, config):
        for key, selector in self.selectors.items():
            selector.set_(config[key])

    def restoreDefaults(self):
        self.config_edited = SafeDict(
            deepcopy(DEFAULTS), {}, NESTED_RAW_DICT_KEYS)
        self.setSelectors(self.config_edited)

        self.theme.restoreDefaults()

        self.restore_btn.setEnabled(False)

    def revert(self):
        self.config_edited = self.config.deepcopy()
        self.setSelectors(self.config_edited)

        self.theme.revert()

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
        self.stateChanged.connect(lambda t: self.changed.emit(bool(t)))

    def value(self):
        return self.isChecked()

    def set_(self, value):
        self.setChecked(value or self.default_value)
        self.changed.emit(value)


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
        self.keep_e = CheckBox()
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

        self.selectors['save_splitters_on_quit'] = CheckBox(
            "Save state of splitters on quit")
        self.selectors['save_splitters_on_quit'].changed.connect(
            lambda state: self.updateDim('save_splitters_on_quit', state))

        self.selectors['save_on_quit'] = CheckBox(
            "Save window size and position on quit")
        self.selectors['save_on_quit'].changed.connect(self.setSaveOnQuit)

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

        save_font_size_checkbox = CheckBox("Save font size on quit")
        save_font_size_checkbox.changed.connect(self.setSaveFontSizeOnQuit)
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


class _CEdit(QWidget):
    changed = pyqtSignal()

    def __init__(self, c, parent=None):
        QWidget.__init__(self, parent)
        self.current_c = self.committed_c = c

    def set_(self, c):
        self.current_c = c
        self.update()
        self.changed.emit()

    def revert(self):
        self.set_(self.committed_c)

    def commitCurrent(self):
        self.committed_c = self.current_c

    def paintEvent(self, event=None):
        painter = QPainter(self)
        painter.setBrush(QBrush(self.current_c))
        painter.drawRect(self.rect())

    def mouseReleaseEvent(self, e):
        res = QColorDialog.getColor(self.current_c)
        if res.isValid():
            self.set_(res)


class CEdit(QWidget):
    changed = pyqtSignal()

    def __init__(self, c, parent=None):
        QWidget.__init__(self, parent)
        self.committed = True
        self.inner = _CEdit(c)
        self.lyt = QHBoxLayout(self)
        self.lyt.addWidget(self.inner)
        self.btn = QToolButton()
        self.lyt.addWidget(self.btn)
        self.btn.setArrowType(Qt.ArrowType.LeftArrow)
        self.lyt.setContentsMargins(0, 0, 0, 0)
        self.btn.setFixedSize(16, 13)
        self.btn.setToolTip("Revert")
        self.btn.hide()
        self.inner.changed.connect(self.handleChange)
        self.btn.clicked.connect(self.inner.revert)

    def set_(self, c):
        self.inner.set_(c)

    def revert(self):
        self.inner.revert()

    @property
    def current_c(self):
        return self.inner.current_c

    def commitCurrent(self):
        self.inner.commitCurrent()
        self.committed = True
        self.btn.hide()

    def handleChange(self):
        if self.inner.current_c == self.inner.committed_c:
            self.committed = True
            self.btn.hide()
        else:
            self.committed = False
            self.btn.show()
        self.changed.emit()


class ThemeSelectorWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, selector_name, values, parent=None):
        QWidget.__init__(self, parent)
        self.committed = True
        self.selector_name = selector_name
        self.values = values
        self.cedits = {}
        self._populateCedits()

    def _populateCedits(self):
        for prop_name, value in self.values.items():
            cedit = CEdit(QColor(value))
            self.cedits[prop_name] = cedit
            cedit.changed.connect(self._ceditChanged)

    def _ceditChanged(self):
        all_committed = True
        for cedit in self.cedits.values():
            if cedit.committed is False:
                self.committed = False
                all_committed = False
                break
        if all_committed is True:
            self.committed = True
        self.changed.emit()

    def revert(self):
        for cedit in self.cedits.values():
            if cedit.committed is False:
                cedit.revert()

    def set_(self, values):
        for prop_name, value in values.items():
            cedit = self.cedits.get(prop_name)
            if (cedit):
                cedit.set_(QColor(value))
            else:
                logger.error('Missing cedit for {prop_name} in\
 {self.selector_name}')

    def get(self):
        values = {}
        for prop_name, cedit in self.cedits.items():
            values[prop_name] = cedit.current_c.name()
        return values


class ThemeCategoryWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.lyt = QFormLayout(self)

    def addSelectorWidget(self, widget):
        self.lyt.addRow(QLabel(f'<b>{widget.selector_name}</b>'))
        for prop_name, cedit in widget.cedits.items():
            self.lyt.addRow(prop_name, cedit)


class ThemeWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, user_dir, parent=None):
        QWidget.__init__(self, parent)
        self.committed = True
        self.selector_widgets = {}
        self.cat_widgets = {}
        self.default_values = Theme.getValuesDict()
        self.values = self._loadValues(getStylePath(user_dir))
        self.lyt = QVBoxLayout(self)
        self.lyt.setContentsMargins(0, 0, 0, 0)
        self.tabw = ScrollTabWidget()
        self.lyt.addWidget(self.tabw)
        self._populateWidgets()

    def _loadValues(self, path):
        values = deepcopy(self.default_values)
        file_path = os.path.join(path, THEME_MODIFICATIONS_FILENAME)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    qss = f.read()
                    v = valuesFromQss(self.default_values, qss)
                    # Merge with default values (fallback for any missing)
                    update(values, v)
                    # Update colours in application
                    Theme.set_(values)
            except OSError as e:
                logger.error(f'Failed to open current theme file in {path}')
                logger.error(f'{type(e)}: {e}')
        else:
            logger.debug(f'Current theme {file_path} not found. This is normal\
 on first launch or if it has not been saved yet. Falling back to default\
 values.')
        return values

    def _populateWidgets(self):
        for name, v in self.values.items():
            selector_widget = ThemeSelectorWidget(name, v)
            selector_widget.changed.connect(self._selectorWidgetChanged)
            self.selector_widgets[name] = selector_widget
            cat_name = self.friendlyCatName(name)
            cat = self.cat_widgets.get(cat_name)
            if (cat):
                cat.addSelectorWidget(selector_widget)
            else:
                cat_widget = ThemeCategoryWidget()
                cat_widget.addSelectorWidget(selector_widget)
                self.cat_widgets[cat_name] = cat_widget
                self.tabw.addTab(cat_widget, cat_name)

    def _selectorWidgetChanged(self):
        all_committed = True
        for s in self.selector_widgets.values():
            if s.committed is False:
                self.committed = False
                all_committed = False
                break
        if all_committed is True:
            self.committed = True
        self.changed.emit()

    def friendlyCatName(self, name):
        return spacecamel(name.split('.')[0])

    def get(self):
        values = {}
        for name, widget in self.selector_widgets.items():
            values[name] = widget.get()
        return values

    def applyTheme(self, name):
        values = {}
        t = Theme.themes.get(name)
        if t:
            values = t.get('values', {})
        else:
            logger.warn('Unable to find values for theme {name}')
        for name, widget in self.selector_widgets.items():
            v = values.get(name, {})
            widget.set_(v)

    def isDefault(self):
        res = True
        values = self.get()
        for selector_name, props in self.default_values.items():
            for prop_name, value in props.items():
                v = values.get(selector_name, {}).get(prop_name)
                if v:
                    res = QColor(v) == QColor(value)
                else:
                    logger.warn(f'Theme values asymmetry in {selector_name}\
 / {prop_name}')
                    res = False
                if res is False:
                    return res
        return res

    def revert(self):
        for s in self.selector_widgets.values():
            if s.committed is False:
                s.revert()

    def restoreDefaults(self):
        for selector_name, props in self.default_values.items():
            for prop_name, value in props.items():
                s = self.selector_widgets.get(selector_name)
                if s:
                    cedit = s.cedits.get(prop_name)
                    if cedit:
                        cedit.set_(QColor(value))
                    else:
                        logger.error('restoreDefaults: Missing cedit for\
 {prop_name} in {selector_name}')
                else:
                    logger.error('restoreDefaults: Missing selector widget for\
 {selector_name}')

    def _save(self, file_path, qss):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                logger.debug(f'Saving theme: {file_path}')
                f.write(qss)
        except OSError as e:
            logger.error('Failed to save theme to file {file_path}')
            logger.error(f'{type(e)}: {e}')

    def saveCurrent(self, path):
        # Get values dict
        values = {}
        for name, widget in self.selector_widgets.items():
            values[name] = widget.get()
            # Commit all the cedits
            for cedit in widget.cedits.values():
                cedit.commitCurrent()
        # Serialise
        res = serialiseValuesDict(values)
        # Write to file in path
        file_path = os.path.join(path, THEME_MODIFICATIONS_FILENAME)
        self._save(file_path, res)
        # Update colours in application
        Theme.set_(values)

    def exportCurrent(self, user_dir):
        # Get values dict
        values = self.get()
        # Serialise
        res = serialiseValuesDict(values)
        # Save dialog
        path = getStylePath(user_dir)
        if not os.path.exists(path):
            path = getStylePath()
        file_path = QFileDialog.getSaveFileName(
            self, 'Export as new theme preset', path, 'Theme preset (*.qss)'
        )[0]
        if len(file_path) == 0:
            return
        # Write to file in path
        self._save(file_path, res)


class CategoriesDelegate(QItemDelegate):
    def __init__(self, parent=None):
        QItemDelegate.__init__(self, parent)
        self.row_height = 24

    def drawDisplay(self, painter, option, rect, text):
        newoption = option
        if not option.state & QStyle.StateFlag.State_Enabled:  # Sections
            painter.fillRect(rect, option.palette.window().color().darker(106))
            painter.setPen(option.palette.window().color().darker(130))
            if rect.top():
                painter.drawLine(rect.topRight(), rect.topLeft())
            painter.drawLine(rect.bottomRight(), rect.bottomLeft())

            newoption.displayAlignment = Qt.AlignmentFlag.AlignCenter

            # Fake enabled state
            newoption.state |= newoption.state | QStyle.StateFlag.State_Enabled
        else:
            option.font.setWeight(QFont.Bold)

        QItemDelegate.drawDisplay(self, painter, newoption, rect, text)

    def sizeHint(self, option, index):
        size = QItemDelegate.sizeHint(self, option, index)
        size.setHeight(self.row_height)
        return size


class CategoriesTree(QTreeView):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setIndentation(0)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setItemsExpandable(False)
        self.header().setVisible(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setItemDelegate(CategoriesDelegate(self))

        self.model = QStandardItemModel(self)
        self.setModel(self.model)

        self.data_role = Qt.ItemDataRole.UserRole

        self.setSizePolicy(QSizePolicy.Policy.Fixed,
                           QSizePolicy.Policy.Preferred)

    def sizeHint(self):
        size = QTreeView.sizeHint(self)
        size.setWidth(130)
        return size

    def addSection(self, name):
        section = QStandardItem(name)
        section.setFlags(Qt.ItemFlag.NoItemFlags)
        self.model.appendRow(section)
        return section

    def addCategory(self, section, name, data=None):
        category = QStandardItem(f'  {name}')
        if data is not None:
            category.setData(data, self.data_role)
        section.appendRow(category)
        category.setFlags(Qt.ItemFlag.ItemIsEnabled |
                          Qt.ItemFlag.ItemIsSelectable)

    def postAddingCategories(self):
        self.expandAll()
        self.setCurrentIndex(self.model.index(0, 0, self.model.index(0, 0)))
        self.setFocus(Qt.FocusReason.NoFocusReason)

    def dataFromIndex(self, index):
        return self.model.itemFromIndex(index).data(self.data_role)


class CategorisedWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.tree = CategoriesTree()
        self.stack = AdjustedStackedWidget()
        self.sections = {}
        self.tree.selectionModel().currentChanged.connect(self.switchCategory)
        lyt = QHBoxLayout(self)
        lyt.addWidget(self.tree)
        lyt.addWidget(self.stack)
        lyt.setContentsMargins(0, 0, 0, 0)

    def add(self, section_name, category_name, widget):
        if section_name not in self.sections:
            self.sections[section_name] = self.tree.addSection(section_name)
        self.tree.addCategory(
            self.sections[section_name], category_name, widget)
        self.stack.addWidget(widget)

    def postAddingCategories(self):
        self.tree.postAddingCategories()

    def switchCategory(self, index):
        self.stack.setCurrentWidget(self.tree.dataFromIndex(index))
