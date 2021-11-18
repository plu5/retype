import os
import logging
from copy import deepcopy
from PyQt5.Qt import (QWidget, QFormLayout, QVBoxLayout, QLabel, QLineEdit,
                      QHBoxLayout, QFrame, QPushButton, QToolBox, QCheckBox,
                      QSpinBox, QListView, QToolButton, QDialogButtonBox,
                      QAbstractListModel, Qt, QStyledItemDelegate, QStyle,
                      QApplication, QRectF, QTextDocument, QFileDialog,
                      pyqtSignal, QModelIndex, QItemSelectionModel,
                      QMessageBox)

from retype.extras.utils import update
from retype.constants import default_config

logger = logging.getLogger(__name__)

DEFAULTS = default_config


def hline():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line


def pxspinbox(value=0):
    sb = QSpinBox()
    sb.setSuffix(" px")
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


class ConfigurationView(QWidget):
    def __init__(self, config, window, saveConfig, prevView, parent=None):
        QWidget.__init__(self, parent)
        # The base config (no uncommitted modifications)
        self.config = deepcopy(DEFAULTS)
        update(self.config, config)
        # The config with uncommitted modifications (any modifications will be
        #  applied to this one)
        self.config_edited = deepcopy(self.config)

        self.saveConfig = saveConfig
        self.prevView = prevView
        self.window = window

        self._initUI()

    def _initUI(self):
        plib = QWidget()
        lyt = QFormLayout(plib)

        self.selectors = {}

        # 1. user_dir
        lyt.addRow(QLabel("Location for the save and config files."))
        self.selectors['user_dir'] = PathSelector(
            self.config_edited['user_dir'])
        self.selectors['user_dir'].changed.connect(
            lambda t: self.update("user_dir", t))
        lyt.addRow("User dir:", self.selectors['user_dir'])
        lyt.addRow(hline())
        # 2. library_paths
        lyt.addRow(QLabel("Library search paths:"))
        self.selectors['library_paths'] = LibraryPathsWidget(
            self.config_edited['library_paths'])
        self.selectors['library_paths'].changed.connect(
            lambda paths: self.update("library_paths", paths))
        lyt.addRow(self.selectors['library_paths'])

        pcon = QWidget()
        lyt = QFormLayout(pcon)
        # 3. prompt
        lyt.addRow(descl("Prompt console commands must be prefixed by. Can be\
 any length, including empty if you do not want to prefix them with anything."
                         ))
        self.selectors['prompt'] = PromptEdit(self.config_edited['prompt'])
        self.selectors['prompt'].textChanged.connect(
            lambda t: self.update("prompt", t))
        lyt.addRow("Prompt:", self.selectors['prompt'])

        prep = QWidget()
        lyt = QFormLayout(prep)
        # 4. rdict
        lyt.addRow(descl("Configure substrings that can be typeable\
 by any one of the set comma-separated list of replacements. This is useful\
 for unicode characters that you don’t have an easy way to input. Each\
 replacement should be of equal length to the original substring."))
        self.selectors['rdict'] = RDictWidget(
            deepcopy(self.config_edited['rdict']))
        self.selectors['rdict'].changed.connect(
            lambda rdict: self.update("rdict", rdict))
        lyt.addRow(self.selectors['rdict'])

        # 5. window
        self.selectors['window'] = WindowGeometrySelector(
            self.window, self.config_edited['window'])
        self.selectors['window'].changed.connect(
            lambda dims: self.update("window", dims))
        self.window.closing.connect(self.maybeSaveGeometry)

        tbox = QToolBox()
        tbox.addItem(plib, "Paths")
        tbox.addItem(pcon, "Console")
        tbox.addItem(prep, "Replacements")
        tbox.addItem(self.selectors['window'], "Window geometry")

        back_btn = QPushButton(" ←")
        back_btn.setStyleSheet("text-align: left")
        back_btn.clicked.connect(self.reject)

        lyt = QVBoxLayout(self)
        lyt.addWidget(back_btn)
        lyt.addWidget(hline())
        lyt.addWidget(tbox)
        lyt.addWidget(hline())
        self.revert_btn = QPushButton("Revert")
        self.revert_btn.setToolTip("Revert changes")
        self.revert_btn.setEnabled(False)
        btnbox = QDialogButtonBox(QDialogButtonBox.Close |
                                  QDialogButtonBox.Save |
                                  QDialogButtonBox.RestoreDefaults)
        btnbox.addButton(self.revert_btn, QDialogButtonBox.DestructiveRole)
        lyt.addWidget(btnbox)
        btnbox.accepted.connect(self.accept)
        btnbox.rejected.connect(self.reject)
        self.revert_btn.clicked.connect(self.revert)
        btnbox.button(QDialogButtonBox.RestoreDefaults)\
              .clicked.connect(self.restoreDefaults)

    def update(self, name, new_value):
        self.config_edited[name] = new_value
        logger.debug("config_edited updated to: {}".format(self.config_edited))

        self.revert_btn.setEnabled(self.config_edited != self.config)

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
        self.saveConfig.emit(self.config_edited)
        # Update base config
        self.config = deepcopy(self.config_edited)

        self.revert_btn.setEnabled(False)

    def reject(self):
        self.prevView.emit()

    def setSelectors(self, config):
        for key, selector in self.selectors.items():
            selector.set_(config[key])

    def restoreDefaults(self):
        self.config_edited = deepcopy(default_config)
        self.setSelectors(self.config_edited)

    def revert(self):
        self.config_edited = deepcopy(self.config)
        self.setSelectors(self.config_edited)

        self.revert_btn.setEnabled(False)

    def maybeSaveGeometry(self):
        if self.config['window']['save_on_quit']:
            logger.debug("Saving window geometry")
            values = self.selectors['window'].valuesByWindow()
            self.config['window'].update(values)
            self.saveConfig.emit(self.config)


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
        if index.isValid() and role == Qt.EditRole:
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

    def set_(self, prompt):
        self.setText(prompt)


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
        if index.isValid() and role == Qt.EditRole:
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

        model.setData(index, [substr, reps], Qt.EditRole)


class RDictWidget(QWidget):
    changed = pyqtSignal(dict)

    def __init__(self, rdict, parent=None):
        QWidget.__init__(self, parent)

        lyt = QFormLayout(self)
        lyt.setContentsMargins(0, 0, 0, 0)
        self.view = QListView()
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
        # row = self.model.rowCount(QModelIndex())-1
        # index = self.model.index(row, 0)
        # self.view.selectionModel().setCurrentIndex(
        #     index, QItemSelectionModel.ClearAndSelect)
        # self.view.edit(index)

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
        save_checkbox = QCheckBox("Save window size and position on quit")
        save_checkbox.stateChanged.connect(self.setSaveOnQuit)
        lyt.addRow(save_checkbox)
        lyt.addRow(hline())

        self.selectors = {}
        # when save on quit is checked, the following is greyed out
        self.selectors['x'] = npxspinbox(dims['x'] or 0)
        self.selectors['y'] = npxspinbox(dims['y'] or 0)
        self.selectors['w'] = pxspinbox(dims['w'])
        self.selectors['h'] = pxspinbox(dims['h'])
        self.cur_btn = QPushButton("Set values according to current window")
        self.cur_btn.clicked.connect(self.setSelectorsValuesByWindow)

        for name, selector in self.selectors.items():
            label = name.title() + ':'
            lyt.addRow(label, selector)
            self.connectSelector(name, selector.valueChanged)

        lyt.addRow(self.cur_btn)

        save_checkbox.setChecked(dims['save_on_quit'])

    def setSaveOnQuit(self, state):
        controls_to_toggle = [*list(self.selectors.values()), self.cur_btn]
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
        self.set_(values)

    def connectSelector(self, name, signal):
        signal.connect(lambda val: self.updateDim(name, val))

    def updateDim(self, name, val):
        self.dims[name] = val
        self.changed.emit(self.dims)

    def set_(self, dims):
        for key, selector in self.selectors.items():
            if key == 'save_on_quit':
                self.setSaveOnQuit(self, dims[key])
                continue
            value = dims[key] if dims[key] is not None else 0
            selector.setValue(value)
