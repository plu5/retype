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

from typing import TYPE_CHECKING

from retype.extras.dict import merge_dicts, update
from retype.constants import default_config, iswindows, default_steno_kdict
from retype.services.theme import (Theme, populateThemes, valuesFromQss, theme,
                                   C)
from retype.extras.qss import serialiseValuesDict
from retype.resource_handler import getStylePath
from retype.extras.widgets import (ScrollTabWidget, AdjustedStackedWidget,
                                   WrappedLabel, MinWidget)
from retype.extras.camel import spacecamel
from retype.services.icon_set import Icons
from retype.games.steno import VisualStenoKeyboard

logger = logging.getLogger(__name__)

DEFAULTS = default_config
THEME_MODIFICATIONS_FILENAME = '__current__.qss'


def hline():
    # type: () -> QFrame
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


class SelectorValueTypeMismatch(TypeError):
    """Wrong value type passed to a configuration selector."""


class SpinBox(QSpinBox):
    changed = pyqtSignal(int)

    def __init__(self, parent=None):
        # type: (SpinBox, QWidget | None) -> None
        QSpinBox.__init__(self, parent)
        self.valueChanged.connect(lambda t: self.changed.emit(t))

    def set_(self, value):
        # type: (SpinBox, object) -> None
        # Taking a wide type in order to be able to call it dynamically from
        # data structure of selectors with set_ method
        if not isinstance(value, int):
            raise SelectorValueTypeMismatch(f'expects int, got: {type(value)}')
        self.setValue(value)


def pxspinbox(value=0, suffix=" px"):
    # type: (int, str) -> SpinBox
    sb = SpinBox()
    sb.setSuffix(suffix)
    sb.setMaximum(10000)
    sb.setValue(value)
    return sb


def npxspinbox(value):
    # type: (int) -> SpinBox
    sb = pxspinbox()
    sb.setMinimum(-10000)
    sb.setValue(value)
    return sb


def descl(text):
    # type: (str) -> WrappedLabel
    return WrappedLabel(text)


class CustomisationDialog(QDialog):
    def __init__(self,  # type: CustomisationDialog
                 config,  # type: Config
                 window,  # type: MainWin
                 saveConfig,  # type: pyqtBoundSignal
                 prevView,  # type: pyqtBoundSignal
                 getBookViewFontSize,  # type: Callable[[], int]
                 parent=None  # type: QWidget | None
                 ):
        # type: (...) -> None
        QDialog.__init__(self, parent, Qt.WindowType.WindowCloseButtonHint)
        # The base config (no uncommitted modifications)
        self.config = merge_dicts(DEFAULTS, config)  # type: Config
        # The config with uncommitted modifications (any modifications will be
        #  applied to this one)
        self.config_edited = deepcopy(self.config)

        self.saveConfig = saveConfig
        self.prevView = prevView
        self._window = window
        self.getBookViewFontSize = getBookViewFontSize

        self._initUI()
        self.setModal(True)
        self.setWindowTitle("Customise retype")

    def sizeHint(self):
        # type: (CustomisationDialog) -> QSize
        return QSize(500, 500)

    def getUserDir(self):
        # type: (CustomisationDialog) -> str
        return self.config['user_dir']

    def _initUI(self):
        # type: (CustomisationDialog) -> None
        self.selectors = {}  # type: dict[str, Selector]

        catw = CategorisedWidget()
        catw.add("Filesystem", "Paths", self._pathSettings())
        catw.add("User interface", "Icons", self._iconsSettings())
        catw.add("User interface", "Theme", self._themeSettings())
        catw.add("User interface", "Console", self._consoleSettings())
        catw.add("User interface", "Book View", self._bookviewSettings())
        catw.add("User interface", "Window geometry", self._windowSettings())
        catw.add("Behaviour", "Line splits", self._sdictSettings())
        catw.add("Behaviour", "Replacements", self._rdictSettings())
        catw.add("Games", "Learn Stenography", self._stenoSettings())
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
        self.restore_btn.setEnabled(self.config != DEFAULTS)

    def _pathSettings(self):
        # type: (CustomisationDialog) -> QWidget
        plib = QWidget()
        lyt = QFormLayout(plib)

        # user_dir
        lyt.addRow(QLabel("Location for the save and config files."))
        self.selectors['user_dir'] = PathSelector(
            self.config_edited['user_dir'])
        self.selectors['user_dir'].changed.connect(
            lambda t: self.update_("user_dir", t))
        lyt.addRow("User dir:", self.selectors['user_dir'])
        lyt.addRow(hline())
        # library_paths
        lyt.addRow(QLabel("Library search paths:"))
        self.selectors['library_paths'] = LibraryPathsWidget(
            self.config_edited['library_paths'])
        self.selectors['library_paths'].changed.connect(
            lambda paths: self.update_("library_paths", paths))
        lyt.addRow(self.selectors['library_paths'])

        return plib

    def _iconsSettings(self):
        # type: (CustomisationDialog) -> QWidget
        pic = QWidget()
        lyt = QFormLayout(pic)
        icon_sets = QComboBox()
        lyt.addRow("Icon set:", icon_sets)
        lyt.addRow(descl("To import an icon set, place the folder in the\
 'style/icons' subfolder in either the user dir or application folder, and\
 restart retype. Missing icons will fall back to the default set."))
        lyt.addRow(descl("Changing icon set requires restarting retype for the\
 change to take effect."))
        for s in Icons.icon_sets:
            icon_sets.addItem(s)
        icon_sets.model().sort(0)
        icon_sets.setCurrentText(self.config_edited['icon_set'])
        icon_sets.currentTextChanged.connect(
            lambda t: self.update_('icon_set', t))
        return pic

    def _themeSettings(self):
        # type: (CustomisationDialog) -> QWidget
        pth = QWidget()
        lyt = QFormLayout(pth)

        preset_lyt = QHBoxLayout()
        themes = QComboBox()
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
        populateThemes(getStylePath(), getStylePath(user_dir))
        prefix_to_exclude = THEME_MODIFICATIONS_FILENAME.rsplit('.', 1)[0]
        for t in Theme.themes:
            if not t.startswith(prefix_to_exclude):
                themes.addItem(t)
        themes.model().sort(0)
        themes.setCurrentIndex(0)

        self.theme = ThemeWidget(user_dir)
        self.theme.changed.connect(self.themeUpdate)
        lyt.addRow(self.theme)

        apply_btn.clicked.connect(
            lambda: self.theme.applyTheme(themes.currentText()))
        export_btn.clicked.connect(
            lambda: self.theme.exportCurrent(self.getUserDir()))

        return pth

    def _consoleSettings(self):
        # type: (CustomisationDialog) -> QWidget
        pcon = MinWidget(200, height=False)
        lyt = QFormLayout(pcon)

        # prompt
        lyt.addRow(descl("Prompt console commands must be prefixed by. Can be\
 any length, including empty if you do not want to prefix them with anything."
                         ))
        self.selectors['prompt'] = PromptEdit(self.config_edited['prompt'])
        self.selectors['prompt'].changed.connect(
            lambda t: self.update_("prompt", t))
        lyt.addRow("Prompt:", self.selectors['prompt'])

        # console font
        self.selectors['console_font'] = ConsoleFontSelector(
            self.config_edited['console_font'])
        self.selectors['console_font'].changed.connect(
            lambda f: self.update_("console_font", f))
        lyt.addRow("Console font:", self.selectors['console_font'])

        # Windows-only: system console
        if iswindows:
            lyt.addRow(hline())
            hide_sysconsole_checkbox = CheckBox(
                "Hide System Console window on UI load\n(Windows-only)")
            hide_sysconsole_checkbox.setChecked(
                self.config_edited.get('hide_sysconsole', True))
            hide_sysconsole_checkbox.changed.connect(
                lambda t: self.update_("hide_sysconsole", t))
            self.selectors['hide_sysconsole'] = hide_sysconsole_checkbox
            lyt.addRow(hide_sysconsole_checkbox)

        pcon.setMinimumWidth(50)
        return pcon

    def _sdictSettings(self):
        # type: (CustomisationDialog) -> QWidget
        psep = QWidget()
        lyt = QFormLayout(psep)
        lyt.addRow(descl("Configure substrings that split the text into lines.\
 The 'keep' argument determines whether the substring still needs to be typed\
 or gets skipped over."))
        self.selectors['sdict'] = SDictWidget(
            deepcopy(self.config_edited['sdict']))
        self.selectors['sdict'].changed.connect(
            lambda sdict: self.update_("sdict", sdict))
        lyt.addRow(self.selectors['sdict'])

        lyt.addRow(hline())
        auto_newline_checkbox = CheckBox(
            "Newline characters advance automatically\n\
(if off, requires pressing Enter at the end of a line)")
        auto_newline_checkbox.setChecked(self.config_edited['auto_newline'])
        auto_newline_checkbox.changed.connect(
            lambda t: self.update_("auto_newline", t))
        self.selectors['auto_newline'] = auto_newline_checkbox
        lyt.addRow(auto_newline_checkbox)

        return psep

    def _rdictSettings(self):
        # type: (CustomisationDialog) -> QWidget
        prep = QWidget()
        lyt = QFormLayout(prep)
        lyt.addRow(descl("Configure substrings that can be typeable\
 by any one of the set comma-separated list of replacements. This is useful\
 for unicode characters that you don’t have an easy way to input. Each\
 replacement should be of equal length to the original substring."))
        self.selectors['rdict'] = RDictWidget(
            deepcopy(self.config_edited['rdict']))
        self.selectors['rdict'].changed.connect(
            lambda rdict: self.update_("rdict", rdict))
        lyt.addRow(self.selectors['rdict'])

        return prep

    def _windowSettings(self):
        # type: (CustomisationDialog) -> QWidget
        self.selectors['window'] = WindowGeometrySelector(
            self._window, self.config_edited['window'])
        self.selectors['window'].changed.connect(
            lambda dims: self.update_("window", dims))
        self._window.closing.connect(self.maybeSaveCertainThings)

        return self.selectors['window']

    def _bookviewSettings(self):
        # type: (CustomisationDialog) -> QWidget
        self.selectors['bookview'] = BookViewSettingsWidget(
            self.config_edited['bookview'])
        self.selectors['bookview'].changed.connect(
            lambda x: self.update_("bookview", x))

        return self.selectors['bookview']

    def _stenoSettings(self):
        # type: (CustomisationDialog) -> QWidget
        w = self.selectors['steno'] = StenoSettingsWidget(
            self.config_edited['steno'])
        w.changed.connect(lambda x: self.update_("steno", x))
        return w

    def update_(self, name, new_value):
        # type: (CustomisationDialog, str, object) -> None
        self.config_edited[name] = new_value  # type: ignore[literal-required]
        logger.debug("config_edited updated to: {}".format(
            self.config_edited))

        self.revert_btn.setEnabled(self.config_edited != self.config)
        self.restore_btn.setEnabled(self.config_edited != DEFAULTS)

    def themeUpdate(self):
        # type: (CustomisationDialog) -> None
        revert = restore = False

        if self.theme.committed is False:
            revert = True
        else:
            revert = self.config_edited != self.config

        if self.theme.isDefault() is False:
            restore = True
        else:
            restore = self.config_edited != DEFAULTS

        self.revert_btn.setEnabled(revert)
        self.restore_btn.setEnabled(restore)

    def accept(self):
        # type: (CustomisationDialog) -> None
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
        self.saveConfig.emit(self.config_edited)
        # Update base config
        self.config = deepcopy(self.config_edited)

        # Save theme
        self.theme.saveCurrent(getStylePath(self.getUserDir()))

        self.revert_btn.setEnabled(False)

    def setSelectors(self, config):
        # type: (CustomisationDialog, Config) -> None
        for key, selector in self.selectors.items():
            selector.set_(config[key])  # type: ignore[literal-required, misc]

    def restoreDefaults(self):
        # type: (CustomisationDialog) -> None
        self.config_edited = deepcopy(DEFAULTS)
        self.setSelectors(self.config_edited)

        self.theme.restoreDefaults()

        self.restore_btn.setEnabled(False)

    def revert(self):
        # type: (CustomisationDialog) -> None
        self.config_edited = deepcopy(self.config)
        self.setSelectors(self.config_edited)

        self.theme.revert()

        self.revert_btn.setEnabled(False)

    def maybeSaveCertainThings(self):
        # type: (CustomisationDialog) -> None
        shouldSave = False

        geom = self.config['window']  # type: Geometry

        if geom['save_on_quit']:
            logger.debug("Saving window geometry")
            s = self.selectors[
                'window'
            ]  # type: WindowGeometrySelector  # type: ignore[assignment]
            values = s.valuesByWindow()
            update(geom, values)  # type: ignore[arg-type]
            shouldSave = True

        if geom['save_splitters_on_quit']:
            logger.debug("Saving splitters states")
            for name, splitter in self._window.splitters.items():
                state = splitter.saveState().data()
                encoded_state = b64encode(state).decode('ascii')
                geom[
                    f'{name}_splitter_state'  # type: ignore[literal-required]
                ] = encoded_state
            shouldSave = True

        if self.config['bookview']['save_font_size_on_quit']:
            logger.debug("Saving BookView’s font size")
            self.config['bookview']['font_size'] = self.getBookViewFontSize()
            shouldSave = True

        if shouldSave:
            self.saveConfig.emit(self.config)


class CheckBox(QCheckBox):
    changed = pyqtSignal(bool)

    def __init__(self, desc, parent=None):
        # type: (CheckBox, str, QWidget | None) -> None
        QCheckBox.__init__(self, desc, parent)
        self.default_value = False
        self.stateChanged.connect(lambda t: self.changed.emit(bool(t)))

    def value(self):
        # type: (CheckBox) -> bool
        return self.isChecked()

    def set_(self, value):
        # type: (CheckBox, object) -> None
        if not isinstance(value, bool):
            raise SelectorValueTypeMismatch(
                f'expects bool, got: {type(value)}')
        self.setChecked(value or self.default_value)
        self.changed.emit(value)


class PathSelector(QWidget):
    changed = pyqtSignal(str)

    def __init__(self, path, parent=None, window_title="Select path"):
        # type: (PathSelector, str, QWidget | None, str) -> None
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
        # type: (PathSelector) -> None
        # The set focus lines are a workaround to a qt bug which causes the
        #  application to crash after the QFileDialog is invoked from a
        #  delegate editor
        self.browse_button.setFocus()
        path = QFileDialog.getExistingDirectory(self, self.window_title)
        self.browse_button.setFocus()

        if path:
            self.path_edit.setText(path)

    def value(self):
        # type: (PathSelector) -> str
        return self.path_edit.text()

    def set_(self, value):
        # type: (PathSelector, object) -> None
        if not isinstance(value, str):
            raise SelectorValueTypeMismatch(
                f'expects str, got: {type(value)}')
        self.path_edit.setText(value)


class Delegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        # type: (Delegate, QWidget | None) -> None
        QStyledItemDelegate.__init__(self, parent)
        self.spacing = 5

    def toDoc(self, index):
        # type: (Delegate, QModelIndex) -> QTextDocument
        doc = QTextDocument()
        data = index.data()  # type: str | object
        if isinstance(data, str):
            doc.setHtml(data)
        else:
            logger.error(f'toDoc: data at index {index} is not str')
        return doc

    def paint(self, painter, option, index):
        # type: (Delegate, QPainter, QStyleOptionViewItem, QModelIndex) -> None
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
        # type: (Delegate, QStyleOptionViewItem, QModelIndex) -> QSize
        size = self.toDoc(index).size().toSize()
        size.setHeight(size.height() + self.spacing*2)
        return size


class PathDelegate(Delegate):
    def __init__(self, parent=None):
        # type: (PathDelegate, QWidget | None) -> None
        Delegate.__init__(self, parent)

    def createEditor(self,
                     parent,  # type: QWidget
                     option,  # type: QStyleOptionViewItem
                     index  # type: QModelIndex
                     ):
        # type: (...) -> QWidget
        data = index.data(Qt.ItemDataRole.EditRole)  # type: object
        if not isinstance(data, str):
            logger.error(f'createEditor: EditRole data at index {index} is not'
                         f' str. Received {data} ({type(data)}).')
            data = ''
        return PathSelector(data, parent)

    def setModelData(self,
                     editor,  # type: QWidget
                     model,  # type: QAbstractItemModel
                     index  # type: QModelIndex
                     ):
        # type: (...) -> None
        if isinstance(editor, PathSelector):
            model.setData(index, editor.value(), Qt.EditRole)
        else:
            logger.error('setModelData: Wrong editor type used with '
                         'PathDelegate. Expected PathSelector, got '
                         f'{type(editor)}')


class LibraryPathsModel(QAbstractListModel):
    changed = pyqtSignal(list)
    INVALID_TEMPLATE = '''<span style="color:red">{}</span>'''

    def __init__(self, paths, parent=None):
        # type: (LibraryPathsModel, list[str], QWidget | None) -> None
        QAbstractListModel.__init__(self, parent)
        self.paths = paths

    def rowCount(self, parent=QModelIndex()):
        # type: (LibraryPathsModel, QModelIndex) -> int
        return len(self.paths)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        # type: (LibraryPathsModel, QModelIndex, int) -> str | None
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

    def setData(self, index, data, role=Qt.ItemDataRole.EditRole):
        # type: (LibraryPathsModel, QModelIndex, str, int) -> bool
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            self.paths[index.row()] = str(data)
            roles = [role]  # type: list[int]
            self.dataChanged.emit(index, index, roles)
            self.changed.emit(self.paths)
            return True
        return False

    def flags(self, index):
        # type: (LibraryPathsModel, QModelIndex) -> Qt.ItemFlags
        if not index.isValid():
            return Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled)
        return (QAbstractListModel.flags(self, index) |
                Qt.ItemFlag.ItemIsEditable)

    def insertRows(self, position=-1, rows=1, parent=QModelIndex()):
        # type: (LibraryPathsModel, int, int, QModelIndex) -> bool
        if position == -1:
            position = len(self.paths)
        self.beginInsertRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            self.paths.insert(position + row, "")
            self.changed.emit(self.paths)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QModelIndex()):
        # type: (LibraryPathsModel, int, int, QModelIndex) -> bool
        self.beginRemoveRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            del self.paths[position + row]
            self.changed.emit(self.paths)
        self.endRemoveRows()
        return True


class LibraryPathsWidget(QWidget):
    changed = pyqtSignal(list)

    def __init__(self, library_paths, parent=None):
        # type: (LibraryPathsWidget, list[str], QWidget | None) -> None
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
        # type: (LibraryPathsWidget, list[str]) -> None
        self.model = LibraryPathsModel(library_paths)
        self.view.setModel(self.model)
        self.model.changed.connect(lambda paths: self.changed.emit(paths))

    def addPath(self):
        # type: (LibraryPathsWidget) -> None
        self.model.insertRows()
        row = self.model.rowCount(QModelIndex())-1
        index = self.model.index(row, 0)
        self.view.selectionModel().setCurrentIndex(
            index, QItemSelectionModel.ClearAndSelect)
        self.view.edit(index)

    def selectedRowIndex(self):
        # type: (LibraryPathsWidget) -> QModelIndex | None
        selectionModel = self.view.selectionModel()
        if selectionModel.hasSelection():
            index = selectionModel.selectedRows()[0]
            return index
        return None

    def removePath(self):
        # type: (LibraryPathsWidget) -> None
        index = self.selectedRowIndex()
        if isinstance(index, QModelIndex):
            self.model.removeRows(index.row(), 1, QModelIndex())

    def modifyPath(self):
        # type: (LibraryPathsWidget) -> None
        index = self.selectedRowIndex()
        if isinstance(index, QModelIndex):
            self.view.edit(index)

    def set_(self, value):
        # type: (LibraryPathsWidget, object) -> None
        if not isinstance(value, list):
            raise SelectorValueTypeMismatch(
                f'expects list[str], got: {type(value)}')
        self.setModel(value)


class PromptEdit(QLineEdit):
    changed = pyqtSignal(str)

    def __init__(self, prompt, parent=None):
        # type: (PromptEdit, str, QWidget | None) -> None
        QLineEdit.__init__(self, parent)
        self.set_(prompt)
        self.textChanged.connect(lambda t: self.changed.emit(t))

    def set_(self, value):
        # type: (PromptEdit, object) -> None
        if not isinstance(value, str):
            raise SelectorValueTypeMismatch(
                f'expects str, got: {type(value)}')
        self.setText(value)


class ConsoleFontSelector(QFontComboBox):
    changed = pyqtSignal(str)

    def __init__(self, font, parent=None):
        # type: (ConsoleFontSelector, str, QWidget | None) -> None
        QFontComboBox.__init__(self, parent)
        self.set_(font)
        self.currentFontChanged.connect(
            lambda f: self.changed.emit(f.family()))  # type: ignore[misc]

    def set_(self, value):
        # type: (ConsoleFontSelector, object) -> None
        if not isinstance(value, str):
            raise SelectorValueTypeMismatch(
                f'expects str, got: {type(value)}')
        self.setCurrentFont(QFont(value))


class ListView(QListView):
    def __init__(self, parent=None):
        # type: (ListView, QWidget | None) -> None
        QListView.__init__(self, parent)

    def sizeHint(self):
        # type: (ListView) -> QSize
        size = QListView.sizeHint(self)
        size.setHeight(10)
        return size


class SDictModel(QAbstractListModel):
    TEMPLATE = '''<p><b>Substring:</b> <code>'<u style="color:palette(link)">\
{0}</u>' ({1})</code><br>
Keep: <code><b>{2}</b></code></p>'''
    INVALID_TEMPLATE = '<div style="color:red">' + TEMPLATE + '</div>'
    changed = pyqtSignal(dict)

    def __init__(self, sdict, parent=None):
        # type: (SDictModel, SDict, QWidget | None) -> None
        QAbstractListModel.__init__(self, parent)
        self.sdict = sdict
        self.order = list(sdict)

    def rowCount(self, parent=QModelIndex()):
        # type: (SDictModel, QModelIndex) -> int
        return len(self.sdict)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        # type: (SDictModel, QModelIndex, int) -> str | tuple[str, bool] | None
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

    def insertRows(self, position=-1, rows=1, parent=QModelIndex()):
        # type: (SDictModel, int, int, QModelIndex) -> bool
        if position == -1:
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

    def removeRows(self, position, rows, parent=QModelIndex()):
        # type: (SDictModel, int, int, QModelIndex) -> bool
        self.beginRemoveRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            del self.sdict[self.order[position + row]]
            del self.order[position + row]
            self.changed.emit(self.sdict)
        self.endRemoveRows()
        return True

    def flags(self, index):
        # type: (SDictModel, QModelIndex) -> Qt.ItemFlags
        if not index.isValid():
            return Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled)
        return (QAbstractListModel.flags(self, index) |
                Qt.ItemFlag.ItemIsEditable)

    def setData(self, index, data, role=Qt.ItemDataRole.EditRole):
        # type: (SDictModel, QModelIndex, tuple[str, bool], int) -> bool
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            del self.sdict[self.order[index.row()]]
            self.order[index.row()] = data[0]
            self.sdict[data[0]] = {'keep': data[1]}
            roles = [role]  # type: list[int]
            self.dataChanged.emit(index, index, roles)
            self.changed.emit(self.sdict)
            return True
        return False


@theme('CustomisationDialog.SDict.EntryEditor', C(fg='black', bg='#CDE8FF'))
class SDictEntryEditor(QWidget):
    selector = 'CustomisationDialog.SDict.EntryEditor'

    def __init__(self, substr, keep, parent=None):
        # type: (SDictEntryEditor, str, bool, QWidget | None) -> None
        QWidget.__init__(self, parent)

        lyt = QFormLayout(self)
        self.substr_e = QLineEdit(substr)
        self.keep_e = CheckBox('')
        self.keep_e.setChecked(keep)
        lyt.addRow("Substring:", self.substr_e)
        lyt.addRow("Keep:", self.keep_e)

        # Note: No need to connect to selector change; this editor gets created
        #  and destroyed each time it opens/closes, it does not persist
        self.themeUpdate()

        self.setAttribute(Qt.WA_StyledBackground, True)

        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.setSpacing(1)

    def substr(self):
        # type: (SDictEntryEditor) -> str
        return self.substr_e.text()

    def keep(self):
        # type: (SDictEntryEditor) -> SDictEntry
        return {'keep': self.keep_e.isChecked()}

    def themeUpdate(self):
        # type: (SDictEntryEditor) -> None
        qss = Theme.getQss(self.selector).replace(self.selector, 'QWidget')
        self.setStyleSheet(qss)


class SDictDelegate(Delegate):
    def __init__(self, parent=None):
        # type: (SDictDelegate, QWidget | None) -> None
        Delegate.__init__(self, parent)

    def createEditor(self,
                     parent,  # type: QWidget
                     option,  # type: QStyleOptionViewItem
                     index  # type: QModelIndex
                     ):
        # type: (...) -> QWidget
        data = index.data(Qt.ItemDataRole.EditRole)  # type: object
        if not isinstance(data, tuple) or len(data) != 2:
            logger.error(f'createEditor: EditRole data at index {index} is not'
                         f' a len 2 tuple. Received {data} ({type(data)}).')
            data = ('', False)
        return SDictEntryEditor(*data, parent)

    def setModelData(self,
                     editor,  # type: QWidget
                     model,  # type: QAbstractItemModel
                     index  # type: QModelIndex
                     ):
        # type: (...) -> None
        if isinstance(editor, SDictEntryEditor):
            substr = editor.substr()
            keep = editor.keep()
            data = (substr, keep)
            model.setData(index, data, Qt.ItemDataRole.EditRole)
        else:
            logger.error('setModelData: Wrong editor type used with '
                         'SDictDelegate. Expected SDictEntryEditor, got '
                         f'{type(editor)}')


class SDictWidget(QWidget):
    changed = pyqtSignal(dict)

    def __init__(self, sdict, parent=None):
        # type: (SDictWidget, SDict, QWidget | None) -> None
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
        # type: (SDictWidget, SDict) -> None
        self.model = SDictModel(sdict)
        self.model.changed.connect(lambda sdict: self.changed.emit(sdict))
        self.view.setModel(self.model)

    def addEntry(self):
        # type: (SDictWidget) -> None
        self.model.insertRows()
        row = self.model.rowCount(QModelIndex())-1
        index = self.model.index(row, 0)
        self.view.selectionModel().setCurrentIndex(
            index, QItemSelectionModel.ClearAndSelect)
        self.view.edit(index)

    def selectedRowIndex(self):
        # type: (SDictWidget) -> QModelIndex | None
        selectionModel = self.view.selectionModel()
        if selectionModel.hasSelection():
            index = selectionModel.selectedRows()[0]
            return index
        return None

    def removeEntry(self):
        # type: (SDictWidget) -> None
        index = self.selectedRowIndex()
        if index:
            self.model.removeRows(index.row(), 1, QModelIndex())

    def modifyEntry(self):
        # type: (SDictWidget) -> None
        index = self.selectedRowIndex()
        if index:
            self.view.edit(index)

    def set_(self, value):
        # type: (SDictWidget, object) -> None
        if not isinstance(value, dict):
            raise SelectorValueTypeMismatch(
                f'expects SDict, got: {type(value)}')
        self.setModel(value)


class RDictModel(QAbstractListModel):
    TEMPLATE = '''<p><b>Substring:</b> <code>'<u style="color:palette(link)">\
{0}</u>' ({1})</code><br>
Replacements list: <code><b>{2}</b></code></p>'''
    INVALID_TEMPLATE = '<div style="color:red">' + TEMPLATE + '</div>'
    changed = pyqtSignal(dict)

    def __init__(self, rdict, parent=None):
        # type: (RDictModel, RDict, QWidget | None) -> None
        QAbstractListModel.__init__(self, parent)
        self.rdict = rdict
        self.order = list(rdict)

    def rowCount(self, parent=QModelIndex()):
        # type: (RDictModel, QModelIndex) -> int
        return len(self.rdict)

    def data(self,
             index,  # type: QModelIndex
             role=Qt.ItemDataRole.DisplayRole  # type: int
             ):
        # type: (...) -> str | tuple[str, list[str]] | None
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

    def insertRows(self, position=-1, rows=1, parent=QModelIndex()):
        # type: (RDictModel, int, int, QModelIndex) -> bool
        if position == -1:
            position = len(self.order)
        self.beginInsertRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            if '' in self.rdict:
                break
            self.order.insert(position + row, "")
            self.rdict[''] = ['']
            self.changed.emit(self.rdict)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QModelIndex()):
        # type: (RDictModel, int, int, QModelIndex) -> bool
        self.beginRemoveRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            del self.rdict[self.order[position + row]]
            del self.order[position + row]
            self.changed.emit(self.rdict)
        self.endRemoveRows()
        return True

    def flags(self, index):
        # type: (RDictModel, QModelIndex) -> Qt.ItemFlags
        if not index.isValid():
            return Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled)
        return (QAbstractListModel.flags(self, index) |
                Qt.ItemFlag.ItemIsEditable)

    def setData(self, index, data, role=Qt.ItemDataRole.EditRole):
        # type: (RDictModel, QModelIndex, tuple[str, list[str]], int) -> bool
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            del self.rdict[self.order[index.row()]]
            self.order[index.row()] = data[0]
            self.rdict[data[0]] = data[1]
            roles = [role]  # type: list[int]
            self.dataChanged.emit(index, index, roles)
            self.changed.emit(self.rdict)
            return True
        return False


@theme('CustomisationDialog.RDict.EntryEditor', C(fg='black', bg='#CDE8FF'))
class RDictEntryEditor(QWidget):
    selector = 'CustomisationDialog.RDict.EntryEditor'

    def __init__(self, substr, reps, parent=None):
        # type: (RDictEntryEditor, str, list[str], QWidget | None) -> None
        QWidget.__init__(self, parent)

        lyt = QFormLayout(self)
        self.substr_e = QLineEdit(substr)
        self.reps_e = QLineEdit(','.join(reps))
        lyt.addRow("Substring:", self.substr_e)
        lyt.addRow("Replacements (separated by ,):", self.reps_e)

        # Note: No need to connect to selector change; this editor gets created
        #  and destroyed each time it opens/closes, it does not persist
        self.themeUpdate()

        self.setAttribute(Qt.WA_StyledBackground, True)

        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.setSpacing(1)

    def substr(self):
        # type: (RDictEntryEditor) -> str
        return self.substr_e.text()

    def reps(self):
        # type: (RDictEntryEditor) -> list[str]
        return self.reps_e.text().split(',')

    def themeUpdate(self):
        # type: (RDictEntryEditor) -> None
        qss = Theme.getQss(self.selector).replace(self.selector, 'QWidget')
        self.setStyleSheet(qss)


class RDictDelegate(Delegate):
    def __init__(self, parent=None):
        # type: (RDictDelegate, QWidget | None) -> None
        Delegate.__init__(self, parent)

    def createEditor(self,
                     parent,  # type: QWidget
                     option,  # type: QStyleOptionViewItem
                     index  # type: QModelIndex
                     ):
        # type: (...) -> QWidget
        data = index.data(Qt.ItemDataRole.EditRole)  # type: object
        if not isinstance(data, tuple) or len(data) != 2:
            logger.error(f'createEditor: EditRole data at index {index} is not'
                         f' a len 2 tuple. Received {data} ({type(data)}).')
            data = ('', [''])
        return RDictEntryEditor(*data, parent)

    def setModelData(self,
                     editor,  # type: QWidget
                     model,  # type: QAbstractItemModel
                     index  # type: QModelIndex
                     ):
        # type: (...) -> None
        if not isinstance(editor, RDictEntryEditor):
            logger.error('setModelData: Wrong editor type used with '
                         'RDictDelegate. Expected RDictEntryEditor, got '
                         f'{type(editor)}')
            return
        substr = editor.substr()
        reps = editor.reps()

        # remove duplicates
        reps = list(dict.fromkeys(reps))  # type: ignore[misc]

        # remove reps that are of incorrect length
        for i, rep in enumerate(reps):
            if len(rep) != len(substr):
                del reps[i]

        data = (substr, reps)
        model.setData(index, data, Qt.ItemDataRole.EditRole)


class RDictWidget(QWidget):
    changed = pyqtSignal(dict)

    def __init__(self, rdict, parent=None):
        # type: (RDictWidget, RDict, QWidget | None) -> None
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
        # type: (RDictWidget, RDict) -> None
        self.model = RDictModel(rdict)
        self.model.changed.connect(lambda rdict: self.changed.emit(rdict))
        self.view.setModel(self.model)

    def addEntry(self):
        # type: (RDictWidget) -> None
        self.model.insertRows()
        row = self.model.rowCount(QModelIndex())-1
        index = self.model.index(row, 0)
        self.view.selectionModel().setCurrentIndex(
            index, QItemSelectionModel.ClearAndSelect)
        self.view.edit(index)

    def selectedRowIndex(self):
        # type: (RDictWidget) -> QModelIndex | None
        selectionModel = self.view.selectionModel()
        if selectionModel.hasSelection():
            index = selectionModel.selectedRows()[0]
            return index
        return None

    def removeEntry(self):
        # type: (RDictWidget) -> None
        index = self.selectedRowIndex()
        if index:
            self.model.removeRows(index.row(), 1, QModelIndex())

    def modifyEntry(self):
        # type: (RDictWidget) -> None
        index = self.selectedRowIndex()
        if index:
            self.view.edit(index)

    def set_(self, value):
        # type: (RDictWidget, object) -> None
        if not isinstance(value, dict):
            raise SelectorValueTypeMismatch(
                f'expects RDict, got: {type(value)}')
        self.setModel(value)


class KDictModel(QAbstractListModel):
    TEMPLATE = '''<p><b>Steno key: <code>{0}</code></b><br>
Bindings list: <code><b>{1}</b></code></p>'''
    INVALID_TEMPLATE = '<div style="color:red">' + TEMPLATE + '</div>'
    changed = pyqtSignal(dict)

    def __init__(self, kdict, parent=None):
        # type: (KDictModel, KDict, QWidget | None) -> None
        QAbstractListModel.__init__(self, parent)
        self.kdict = kdict
        self.order = list(kdict)

    def rowCount(self, parent=QModelIndex()):
        # type: (KDictModel, QModelIndex) -> int
        return len(self.kdict)

    def data(self,
             index,  # type: QModelIndex
             role=Qt.ItemDataRole.DisplayRole  # type: int
             ):
        # type: (...) -> str | tuple[str, list[str]] | None
        row = index.row()
        if row < 0 or row >= len(self.order):
            return None

        substring = self.order[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if substring == '' or not self.kdict[substring]:
                return self.INVALID_TEMPLATE.format(
                    substring, self.kdict[substring])
            return self.TEMPLATE.format(substring, self.kdict[substring])
        elif role == Qt.ItemDataRole.EditRole:
            return (substring, self.kdict[substring])

        return None

    def flags(self, index):
        # type: (KDictModel, QModelIndex) -> Qt.ItemFlags
        if not index.isValid():
            return Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled)
        return (QAbstractListModel.flags(self, index) |
                Qt.ItemFlag.ItemIsEditable)

    def setData(self, index, data, role=Qt.ItemDataRole.EditRole):
        # type: (KDictModel, QModelIndex, tuple[str, list[str]], int) -> bool
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            self.kdict[data[0]] = data[1]
            roles = [role]  # type: list[int]
            self.dataChanged.emit(index, index, roles)
            self.changed.emit(self.kdict)
            return True
        return False


@theme('CustomisationDialog.KDict.EntryEditor', C(fg='black', bg='#CDE8FF'))
class KDictEntryEditor(QWidget):
    selector = 'CustomisationDialog.KDict.EntryEditor'

    def __init__(self, substr, reps, parent=None):
        # type: (KDictEntryEditor, str, list[str], QWidget | None) -> None
        QWidget.__init__(self, parent)

        lyt = QFormLayout(self)
        self.substr_e = QLineEdit(substr)
        self.reps_e = QLineEdit(','.join(reps))
        lyt.addRow(QLabel(f"<b>Steno key: <code>{substr}</code></b>"))
        lyt.addRow("Bindings (separated by ,):", self.reps_e)

        # Note: No need to connect to selector change; this editor gets created
        #  and destroyed each time it opens/closes, it does not persist
        self.themeUpdate()

        self.setAttribute(Qt.WA_StyledBackground, True)

        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.setSpacing(1)

    def substr(self):
        # type: (KDictEntryEditor) -> str
        return self.substr_e.text()

    def reps(self):
        # type: (KDictEntryEditor) -> list[str]
        return self.reps_e.text().split(',')

    def themeUpdate(self):
        # type: (KDictEntryEditor) -> None
        qss = Theme.getQss(self.selector).replace(self.selector, 'QWidget')
        self.setStyleSheet(qss)


class KDictDelegate(Delegate):
    def __init__(self, parent=None):
        # type: (KDictDelegate, QWidget | None) -> None
        Delegate.__init__(self, parent)

    def createEditor(self,
                     parent,  # type: QWidget
                     option,  # type: QStyleOptionViewItem
                     index  # type: QModelIndex
                     ):
        # type: (...) -> QWidget
        data = index.data(Qt.ItemDataRole.EditRole)  # type: object
        if not isinstance(data, tuple) or len(data) != 2:
            logger.error(f'createEditor: EditRole data at index {index} is not'
                         f' a len 2 tuple. Received {data} ({type(data)}).')
            data = ('', [''])
        return KDictEntryEditor(*data, parent)

    def setModelData(self,
                     editor,  # type: QWidget
                     model,  # type: QAbstractItemModel
                     index  # type: QModelIndex
                     ):
        # type: (...) -> None
        if not isinstance(editor, KDictEntryEditor):
            logger.error('setModelData: Wrong editor type used with '
                         'KDictDelegate. Expected KDictEntryEditor, got '
                         f'{type(editor)}')
            return
        substr = editor.substr()
        reps = editor.reps()

        # remove duplicates
        reps = list(dict.fromkeys(reps))  # type: ignore[misc]

        # remove reps that are of incorrect length
        for i, rep in enumerate(reps):
            if len(rep) != 1:
                del reps[i]

        data = (substr, reps)
        model.setData(index, data, Qt.ItemDataRole.EditRole)


class KDictWidget(QWidget):
    changed = pyqtSignal(dict)
    currentChanged = pyqtSignal(int)

    def __init__(self, kdict, parent=None):
        # type: (KDictWidget, KDict, QWidget | None) -> None
        QWidget.__init__(self, parent)

        lyt = QFormLayout(self)
        lyt.setContentsMargins(0, 0, 0, 0)
        self.view = ListView()
        self.view.setItemDelegate(KDictDelegate())
        self.setModel(kdict)
        lyt.addRow(self.view)

        pbuttons = QWidget()
        pbl = QHBoxLayout(pbuttons)
        modify_btn = QPushButton("Modify")
        modify_btn.clicked.connect(self.modifyEntry)
        pbl.addWidget(modify_btn)
        pbl.setContentsMargins(0, 0, 0, 0)
        lyt.addRow(pbuttons)

    def setModel(self, kdict):
        # type: (KDictWidget, KDict) -> None
        self.model = KDictModel(kdict)
        self.model.changed.connect(lambda kdict: self.changed.emit(kdict))
        self.view.setModel(self.model)
        self.view.selectionModel().currentChanged.connect(
            lambda i: self.currentChanged.emit(i.row()))  # type: ignore[misc]

    def select(self, i):
        # type: (KDictWidget, int) -> None
        index = self.model.index(i, 0)
        self.view.selectionModel().setCurrentIndex(
            index, QItemSelectionModel.ClearAndSelect)

    def selectedRowIndex(self):
        # type: (KDictWidget) -> QModelIndex | None
        selectionModel = self.view.selectionModel()
        if selectionModel.hasSelection():
            index = selectionModel.selectedRows()[0]
            return index
        return None

    def modifyEntry(self):
        # type: (KDictWidget) -> None
        index = self.selectedRowIndex()
        if index:
            self.view.edit(index)

    def set_(self, value):
        # type: (KDictWidget, object) -> None
        if not isinstance(value, dict):
            raise SelectorValueTypeMismatch(
                f'expects KDict, got: {type(value)}')
        self.setModel(value)


class WindowGeometrySelector(QWidget):
    changed = pyqtSignal(dict)

    def __init__(self,
                 window,  # type: MainWin
                 dims,  # type: Geometry
                 parent=None  # type: QWidget | None
                 ):
        # type: (...) -> None
        QWidget.__init__(self, parent)

        self._window = window
        self.dims = dims

        lyt = QFormLayout(self)

        self.selectors = {}  # type: dict[str, Selector]

        cb = self.selectors['save_splitters_on_quit'] = CheckBox(
            "Save state of splitters on quit")
        cb.changed.connect(
            lambda state: self.updateDim(  # type: ignore[misc]
                'save_splitters_on_quit', state))

        cb = self.selectors['save_on_quit'] = CheckBox(
            "Save window size and position on quit")
        cb.changed.connect(self.setSaveOnQuit)

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

        self.dim_selectors = {
            k: v for k, v in self.selectors.items()  # type: ignore[misc]
            if k in 'xywh'
        }  # type: dict[str, SpinBox]

        for name, selector in self.dim_selectors.items():
            label = name.title() + ':'
            lyt.addRow(label, selector)
            self.connectSelector(name, selector.valueChanged)

        lyt.addRow(self.cur_btn)

        for k in ('save_splitters_on_quit', 'save_on_quit'):
            self.selectors[k].set_(self.dims[k])

    def setSaveOnQuit(self, state):
        # type: (WindowGeometrySelector, bool) -> None
        controls_to_toggle = [*list(self.dim_selectors.values()), self.cur_btn]
        for control in controls_to_toggle:
            disabled_bool = True if state else False
            control.setDisabled(disabled_bool)

        self.updateDim('save_on_quit', state)

    def valuesByWindow(self):
        # type: (WindowGeometrySelector) -> Geometry
        pos = self._window.pos()
        size = self._window.size()

        values = {}  # type: Geometry
        values['x'] = pos.x()
        values['y'] = pos.y()
        values['w'] = size.width()
        values['h'] = size.height()

        return values

    def setSelectorsValuesByWindow(self):
        # type: (WindowGeometrySelector) -> None
        values = self.valuesByWindow()
        update(self.dims, values)  # type: ignore[arg-type]
        self.set_(self.dims)
        self.changed.emit(self.dims)

    def connectSelector(self, name, signal):
        # type: (WindowGeometrySelector, str, pyqtBoundSignal) -> None
        signal.connect(
            lambda val: self.updateDim(name, val))  # type: ignore[misc]

    def updateDim(self, name, val):
        # type: (WindowGeometrySelector, str, object) -> None
        if name not in self.dims.keys():
            logger.error(f'updateDim: Nonexistent key {name}')
        self.dims[name] = val  # type: ignore[literal-required]
        self.changed.emit(self.dims)

    def set_(self, value):
        # type: (WindowGeometrySelector, object) -> None
        if not isinstance(value, dict):
            raise SelectorValueTypeMismatch(
                f'expects Geometry dict, got: {type(value)}')
        for key, selector in self.selectors.items():
            selector.set_(value[key])


class FontComboBox(QFontComboBox):
    changed = pyqtSignal(int)

    def __init__(self, parent=None):
        # type: (FontComboBox, QWidget | None) -> None
        QFontComboBox.__init__(self, parent)
        self.currentFontChanged.connect(lambda t: self.changed.emit(t))

    def set_(self, value):
        # type: (FontComboBox, object) -> None
        if not isinstance(value, str):
            raise SelectorValueTypeMismatch(f'expects str, got: {type(value)}')
        self.setCurrentFont(QFont(value))


class BookViewSettingsWidget(QWidget):
    changed = pyqtSignal(dict)

    def __init__(self,
                 bookview_settings,  # type: BookViewSettings
                 parent=None  # type: QWidget | None
                 ):
        # type: (...) -> None
        QWidget.__init__(self, parent)

        self.settings = bookview_settings
        self.selectors = {
        }  # type: dict[str, Selector]

        save_font_size_checkbox = CheckBox("Save font size on quit")
        save_font_size_checkbox.changed.connect(self.setSaveFontSizeOnQuit)
        self.selectors['save_font_size_on_quit'] = save_font_size_checkbox

        self.font_size_selector = pxspinbox(self.settings['font_size'], " pt")
        self.font_size_selector.valueChanged.connect(
            lambda val: self.updateSetting('font_size', val))
        self.selectors['font_size'] = self.font_size_selector

        self.font_selector = FontComboBox()
        self.font_selector.changed.connect(
            lambda f: self.updateSetting('font', f))
        self.selectors['font'] = self.font_selector

        lyt = QFormLayout(self)
        lyt.addRow(save_font_size_checkbox)
        lyt.addRow(hline())
        lyt.addRow("Default font size:", self.font_size_selector)
        lyt.addRow("Font family:", self.font_selector)

        self.set_(bookview_settings)

    def updateSetting(self, name, val):
        # type: (BookViewSettingsWidget, str, object) -> None
        if name in self.settings.keys():
            self.settings[name] = val  # type: ignore[literal-required]
            self.changed.emit(self.settings)
        else:
            logger.error(f'updateSetting: Nonexistent key {name}')

    def setSaveFontSizeOnQuit(self, state):
        # type: (BookViewSettingsWidget, bool) -> None
        self.font_size_selector.setDisabled(True if state else False)
        self.updateSetting('save_font_size_on_quit', state)

    def set_(self, value):
        # type: (BookViewSettingsWidget, object) -> None
        if not isinstance(value, dict):
            raise SelectorValueTypeMismatch(
                f'expects BookViewSettings dict, got: {type(value)}')
        for key, selector in self.selectors.items():
            selector.set_(value[key])

    def minimumSizeHint(self):
        # type: (BookViewSettingsWidget) -> QSize
        return QSize(100, 100)

    def sizeHint(self):
        # type: (BookViewSettingsWidget) -> QSize
        return self.minimumSizeHint()


class StenoSettingsWidget(QWidget):
    changed = pyqtSignal(dict)

    def __init__(self, steno_settings, parent=None):
        # type: (StenoSettingsWidget, StenoSettings, QWidget|None) -> None
        QWidget.__init__(self, parent)

        self.settings = steno_settings
        self.selectors = {}  # type: dict[str, Selector]

        lyt = QFormLayout(self)
        self.kbd = VisualStenoKeyboard()
        self.kbd.should_select_key_on_click = True
        kdictw = self.selectors['kdict'] = KDictWidget(self.settings['kdict'])
        kdictw.changed.connect(lambda v: self.updateSetting('kdict', v))
        self.kl = list(default_steno_kdict)

        def maybeSelect(k):
            # type: (str) -> None
            if k in self.kl:
                kdictw.select(self.kl.index(k))

        self.kbd.keySelected.connect(maybeSelect)
        kdictw.currentChanged.connect(lambda i: self.kbd.selectKey(self.kl[i]))

        lyt.addRow(self.kbd)
        lyt.addRow(kdictw)

    def updateSetting(self, name, val):
        # type: (StenoSettingsWidget, str, object) -> None
        if name in self.settings.keys():
            self.settings[name] = val  # type: ignore[literal-required]
            self.changed.emit(self.settings)
        else:
            logger.error(f'updateSetting: Nonexistent key {name}')

    def set_(self, value):
        # type: (StenoSettingsWidget, object) -> None
        if not isinstance(value, dict):
            raise SelectorValueTypeMismatch(
                f'expects StenoSettings dict, got: {type(value)}')
        for key, selector in self.selectors.items():
            selector.set_(value[key])

    def minimumSizeHint(self):
        # type: (StenoSettingsWidget) -> QSize
        return QSize(100, 100)

    def sizeHint(self):
        # type: (StenoSettingsWidget) -> QSize
        return self.minimumSizeHint()


class _CEdit(QWidget):
    changed = pyqtSignal()

    def __init__(self, c, parent=None):
        # type: (_CEdit, QColor, QWidget | None) -> None
        QWidget.__init__(self, parent)
        self.current_c = self.committed_c = c

    def set_(self, c):
        # type: (_CEdit, QColor) -> None
        self.current_c = c
        self.update()
        self.changed.emit()

    def revert(self):
        # type: (_CEdit) -> None
        self.set_(self.committed_c)

    def commitCurrent(self):
        # type: (_CEdit) -> None
        self.committed_c = self.current_c

    def paintEvent(self, event=None):
        # type: (_CEdit, QPaintEvent | None) -> None
        painter = QPainter(self)
        painter.setBrush(QBrush(self.current_c))
        painter.drawRect(self.rect())

    def mouseReleaseEvent(self, e):
        # type: (_CEdit, QMouseEvent) -> None
        res = QColorDialog.getColor(self.current_c)
        if res.isValid():
            self.set_(res)


class CEdit(QWidget):
    changed = pyqtSignal()

    def __init__(self, c, parent=None):
        # type: (CEdit, QColor, QWidget | None) -> None
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
        # type: (CEdit, QColor) -> None
        self.inner.set_(c)

    def revert(self):
        # type: (CEdit) -> None
        self.inner.revert()

    @property
    def current_c(self):
        # type: (CEdit) -> QColor
        return self.inner.current_c

    def commitCurrent(self):
        # type: (CEdit) -> None
        self.inner.commitCurrent()
        self.committed = True
        self.btn.hide()

    def handleChange(self):
        # type: (CEdit) -> None
        if self.inner.current_c == self.inner.committed_c:
            self.committed = True
            self.btn.hide()
        else:
            self.committed = False
            self.btn.show()
        self.changed.emit()


class ThemeSelectorWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self,
                 selector_name,  # type: str
                 values,  # type: dict[str, str]
                 parent=None  # type: QWidget | None
                 ):
        # type: (...) -> None
        QWidget.__init__(self, parent)
        self.committed = True
        self.selector_name = selector_name
        self.values = values
        self.cedits = {}  # type: dict[str, CEdit]
        self._populateCedits()

    def _populateCedits(self):
        # type: (ThemeSelectorWidget) -> None
        for prop_name, value in self.values.items():
            cedit = CEdit(QColor(value))
            self.cedits[prop_name] = cedit
            cedit.changed.connect(self._ceditChanged)

    def _ceditChanged(self):
        # type: (ThemeSelectorWidget) -> None
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
        # type: (ThemeSelectorWidget) -> None
        for cedit in self.cedits.values():
            if cedit.committed is False:
                cedit.revert()

    def set_(self, values):
        # type: (ThemeSelectorWidget, dict[str, str]) -> None
        for prop_name, value in values.items():
            cedit = self.cedits.get(prop_name)
            if (cedit):
                cedit.set_(QColor(value))
            else:
                logger.error(f'Missing cedit for {prop_name} in'
                             f'{self.selector_name}')

    def get(self):
        # type: (ThemeSelectorWidget) -> dict[str, str]
        values = {}
        for prop_name, cedit in self.cedits.items():
            values[prop_name] = cedit.current_c.name()
        return values


class ThemeCategoryWidget(QWidget):
    def __init__(self, parent=None):
        # type: (ThemeCategoryWidget, QWidget | None) -> None
        QWidget.__init__(self, parent)
        self.lyt = QFormLayout(self)

    def addSelectorWidget(self, widget):
        # type: (ThemeCategoryWidget, ThemeSelectorWidget) -> None
        self.lyt.addRow(QLabel(f'<b>{widget.selector_name}</b>'))
        for prop_name, cedit in widget.cedits.items():
            self.lyt.addRow(prop_name, cedit)


class ThemeWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, user_dir, parent=None):
        # type: (ThemeWidget, str, QWidget | None) -> None
        QWidget.__init__(self, parent)
        self.committed = True
        self.selector_widgets = {}  # type: dict[str, ThemeSelectorWidget]
        self.cat_widgets = {}  # type: dict[str, ThemeCategoryWidget]
        self.default_values = Theme.getValuesDict()
        self.values = self._loadValues(getStylePath(user_dir))
        self.lyt = QVBoxLayout(self)
        self.lyt.setContentsMargins(0, 0, 0, 0)
        self.tabw = ScrollTabWidget()
        self.lyt.addWidget(self.tabw)
        self._populateWidgets()

    def _loadValues(self, path):
        # type: (ThemeWidget, str) -> dict[str, dict[str, str]]
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
        # type: (ThemeWidget) -> None
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
        # type: (ThemeWidget) -> None
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
        # type: (ThemeWidget, str) -> str
        return spacecamel(name.split('.')[0])

    def get(self):
        # type: (ThemeWidget) -> dict[str, dict[str, str]]
        values = {}
        for name, widget in self.selector_widgets.items():
            values[name] = widget.get()
        return values

    def applyTheme(self, name):
        # type: (ThemeWidget, str) -> None
        values = {}  # type: dict[str, dict[str, str]]
        t = Theme.themes.get(name)
        if t:
            values = t.get('values', {})
        else:
            logger.warning('applyTheme: Unable to find values for theme '
                           f'{name}')
        for name, widget in self.selector_widgets.items():
            v = values.get(name, {})
            widget.set_(v)

    def isDefault(self):
        # type: (ThemeWidget) -> bool
        res = True
        values = self.get()
        for selector_name, props in self.default_values.items():
            for prop_name, value in props.items():
                v = values.get(selector_name, {}).get(prop_name)
                if v:
                    res = QColor(v) == QColor(value)
                else:
                    logger.warning('isDefault: Theme values asymmetry in '
                                   f'{selector_name} / {prop_name}')
                    res = False
                if res is False:
                    return res
        return res

    def revert(self):
        # type: (ThemeWidget) -> None
        for s in self.selector_widgets.values():
            if s.committed is False:
                s.revert()

    def restoreDefaults(self):
        # type: (ThemeWidget) -> None
        for selector_name, props in self.default_values.items():
            for prop_name, value in props.items():
                s = self.selector_widgets.get(selector_name)
                if s:
                    cedit = s.cedits.get(prop_name)
                    if cedit:
                        cedit.set_(QColor(value))
                    else:
                        logger.error('restoreDefaults: Missing cedit for '
                                     f'{prop_name} in {selector_name}')
                else:
                    logger.error('restoreDefaults: Missing selector widget '
                                 f'for {selector_name}')

    def _save(self, file_path, qss):
        # type: (ThemeWidget, str, str) -> None
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                logger.debug(f'Saving theme: {file_path}')
                f.write(qss)
        except OSError as e:
            logger.error(f'Failed to save theme to file {file_path}')
            logger.error(f'{type(e)}: {e}')

    def saveCurrent(self, path):
        # type: (ThemeWidget, str) -> None
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
        # type: (ThemeWidget, str) -> None
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

    def minimumSizeHint(self):
        # type: (ThemeWidget) -> QSize
        return QSize(100, 100)

    def sizeHint(self):
        # type: (ThemeWidget) -> QSize
        return self.minimumSizeHint()


class CategoriesDelegate(QItemDelegate):
    def __init__(self, parent=None):
        # type: (CategoriesDelegate, QWidget | None) -> None
        QItemDelegate.__init__(self, parent)
        self.row_height = 24

    def drawDisplay(self,
                    painter,  # type: QPainter
                    option,  # type: QStyleOptionViewItem
                    rect,  # type: QRect
                    text  # type: str
                    ):
        # type: (...) -> None
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
            option.font.setWeight(QFont.Weight.Bold)

        QItemDelegate.drawDisplay(self, painter, newoption, rect, text)

    def sizeHint(self,
                 option,  # type: QStyleOptionViewItem
                 index  # type: QModelIndex
                 ):
        # type: (...) -> QSize
        size = QItemDelegate.sizeHint(self, option, index)
        size.setHeight(self.row_height)
        return size


class CategoriesTree(QTreeView):
    def __init__(self, parent=None):
        # type: (CategoriesTree, QWidget | None) -> None
        QWidget.__init__(self, parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setIndentation(0)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setItemsExpandable(False)
        self.header().setVisible(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setItemDelegate(CategoriesDelegate(self))

        self._model = QStandardItemModel(self)
        self.setModel(self._model)

        self.data_role = Qt.ItemDataRole.UserRole

        self.setSizePolicy(QSizePolicy.Policy.Fixed,
                           QSizePolicy.Policy.Preferred)

    def sizeHint(self):
        # type: (CategoriesTree) -> QSize
        size = QTreeView.sizeHint(self)
        size.setWidth(130)
        return size

    def addSection(self, name):
        # type: (CategoriesTree, str) -> QStandardItem
        section = QStandardItem(name)
        section.setFlags(Qt.ItemFlag.NoItemFlags)
        self._model.appendRow(section)
        return section

    def addCategory(self, section, name, data=None):
        # type: (CategoriesTree, QStandardItem, str, object | None) -> None
        category = QStandardItem(f'  {name}')
        if data is not None:
            category.setData(data, self.data_role)
        section.appendRow(category)
        category.setFlags(Qt.ItemFlag.ItemIsEnabled |
                          Qt.ItemFlag.ItemIsSelectable)

    def postAddingCategories(self):
        # type: (CategoriesTree) -> None
        self.expandAll()
        self.setCurrentIndex(self._model.index(0, 0, self._model.index(0, 0)))
        self.setFocus(Qt.FocusReason.NoFocusReason)

    def dataFromIndex(self, index):
        # type: (CategoriesTree, QModelIndex) -> object | None
        item = self._model.itemFromIndex(index)  # type: QStandardItem | None
        if item is not None:
            data = item.data(self.data_role)  # type: object
            return data
        else:
            return None


class CategorisedWidget(QWidget):
    def __init__(self, parent=None):
        # type: (CategorisedWidget, QWidget | None) -> None
        QWidget.__init__(self, parent)
        self.tree = CategoriesTree()
        self.stack = AdjustedStackedWidget()
        self.sections = {}  # type: dict[str, QStandardItem]
        self.tree.selectionModel().currentChanged.connect(self.switchCategory)
        lyt = QHBoxLayout(self)
        lyt.addWidget(self.tree)
        lyt.addWidget(self.stack)
        lyt.setContentsMargins(0, 0, 0, 0)

    def add(self, section_name, category_name, widget):
        # type: (CategorisedWidget, str, str, QWidget) -> None
        if section_name not in self.sections:
            self.sections[section_name] = self.tree.addSection(section_name)
        self.tree.addCategory(
            self.sections[section_name], category_name, widget)
        self.stack.addWidget(widget)

    def postAddingCategories(self):
        # type: (CategorisedWidget) -> None
        self.tree.postAddingCategories()

    def switchCategory(self, index):
        # type: (CategorisedWidget, QModelIndex) -> None
        widget = self.tree.dataFromIndex(index)
        if isinstance(widget, QWidget):
            self.stack.setCurrentWidget(widget)
        else:
            logger.error(f'switchCategory: Data at index {index} is not a '
                         'QWidget')


if TYPE_CHECKING:
    from qt import (  # noqa: F401
        QStyleOptionViewItem, QAbstractItemModel, QRect, pyqtBoundSignal,
        QPaintEvent, QMouseEvent)
    from typing import Callable  # noqa: F401
    from retype.extras.metatypes import (  # noqa: F401
        SDict, SDictEntry, RDict, KDict, Geometry, SafeGeometry,
        BookViewSettings, StenoSettings, Config, NestedDict, Selector)
    from retype.ui import MainWin  # noqa: F401
    from retype.controllers import SafeConfig  # noqa: F401
