# This module is only used for typechecking. Do not import it in runtime.
from typing import (TypedDict, Callable, Dict, Mapping, Union, overload,
                    Literal, Protocol)
from ebooklib import epub
from retype.controllers.safe_config import _SafeConfig
from retype.ui import ShelfView, BookView
from retype.games.typespeed import TypespeedView as TypespeedV
from retype.games.steno import StenoView
from retype.controllers.main_controller import View
from retype.extras.dict import _NestedSafeDictGroup
from qt import QWidget, pyqtBoundSignal

NestedDict = Dict[object, Union[object, 'NestedDict']]
NestedMapping = Mapping[object, Union[object, 'NestedMapping']]

# CommandInfo = dict[str, str | list[str] | None]
CommandInfo = TypedDict(
    'CommandInfo',
    {'desc': str, 'aliases': list[str], 'args': str | None,
     'func': Callable[[], None]},
    total=False)
CommandsInfo = dict[str, CommandInfo]

SaveData = TypedDict(
    'SaveData',
    {'persistent_pos': int, 'chapter_pos': int, 'progress': float,
     'friendly_name': str},
    total=False)
Save = dict[str, SaveData]
ImageData = TypedDict(
    'ImageData',
    {'item': epub.EpubImage, 'link': str, 'raw': bytes})
Chapter = TypedDict(
    'Chapter',
    {'html': str, 'plain': str, 'len': int, 'links': list[str],
     'images': list[ImageData]},
    total=False)

BookViewSettings = TypedDict(
    'BookViewSettings',
    {'save_font_size_on_quit': bool, 'font_size': int, 'font': str},
    total=False)
Geometry = TypedDict(
    'Geometry',
    {'x': int | None, 'y': int | None, 'w': int, 'h': int,
     'save_on_quit': bool, 'save_splitters_on_quit': bool,
     'main_splitter_state': str, 'bookview_splitter_state': str},
    total=False)
SDictEntry = TypedDict(
    'SDictEntry',
    {'keep': bool})
SDict = dict[str, SDictEntry]
PosedSDictEntry = TypedDict(
    'PosedSDictEntry',
    {'keep': bool, 'pos': int})
PosedSDict = dict[str, PosedSDictEntry]
RDict = dict[str, list[str]]
KDict = dict[str, list[str]]
StenoSettings = TypedDict(
    'StenoSettings',
    {'kdict': KDict},
    total=False)

Config = TypedDict(
    'Config',
    {'user_dir': str, 'library_paths': list[str], 'icon_set': str,
     'prompt': str, 'console_font': str, 'sdict': SDict, 'rdict': RDict,
     'bookview': BookViewSettings, 'window': Geometry, 'auto_newline': bool,
     'steno': StenoSettings, 'hide_sysconsole': bool},
    total=False)


class ConfigKeyTypes:
    str = Literal['user_dir', 'icon_set', 'prompt', 'console_font']
    bool = Literal['auto_newline', 'hide_sysconsole']
    liststr = Literal['library_paths']
    SDict = Literal['sdict']
    RDict = Literal['rdict']
    BVS = Literal['bookview']
    Geometry = Literal['window']
    StenoSet = Literal['steno']


# Madness. But I can't find another way to have a TypedDict-like
# behaviour for a class with methods (SafeConfig)
class SConfig(_SafeConfig):
    @overload  # type: ignore[override,no-overload-impl]
    def __getitem__(self, key: ConfigKeyTypes.str) -> str: ...
    @overload
    def __getitem__(self, key: ConfigKeyTypes.liststr) -> list[str]: ...
    @overload
    def __getitem__(self, key: ConfigKeyTypes.bool) -> bool: ...
    @overload
    def __getitem__(self, key: ConfigKeyTypes.SDict) -> SDict: ...
    @overload
    def __getitem__(self, key: ConfigKeyTypes.RDict) -> RDict: ...
    @overload
    def __getitem__(self, key: ConfigKeyTypes.BVS) -> BookViewSettings: ...
    @overload
    def __getitem__(self, key: ConfigKeyTypes.Geometry) -> Geometry: ...
    @overload
    def __getitem__(self, key: ConfigKeyTypes.StenoSet) -> StenoSettings: ...


class SafeGeometry(_NestedSafeDictGroup):
    @overload  # type: ignore[override,no-overload-impl]
    def __getitem__(self, key: Literal['x']) -> int | None: ...
    @overload
    def __getitem__(self, key: Literal['y']) -> int | None: ...
    @overload
    def __getitem__(self, key: Literal['w']) -> int: ...
    @overload
    def __getitem__(self, key: Literal['h']) -> int: ...
    @overload
    def __getitem__(self, key: Literal['save_on_quit']) -> bool: ...
    @overload
    def __getitem__(self, key: Literal['save_splitters_on_quit']) -> bool: ...
    @overload
    def __getitem__(self, key: str) -> object: ...


class SafeBookViewSettings(_NestedSafeDictGroup):
    @overload  # type: ignore[override,no-overload-impl]
    def __getitem__(self, key: Literal['save_font_size_on_quit']) -> bool: ...
    @overload
    def __getitem__(self, key: Literal['font_size']) -> int: ...
    @overload
    def __getitem__(self, key: Literal['font']) -> str: ...
    @overload
    def __getitem__(self, key: str) -> object: ...


class SafeStenoSettings(_NestedSafeDictGroup):
    @overload  # type: ignore[override,no-overload-impl]
    def __getitem__(self, key: Literal['kdict']) -> KDict: ...
    @overload
    def __getitem__(self, key: str) -> object: ...


class ViewsDict(dict[object, object]):
    @overload  # type: ignore[override,no-overload-impl]
    def __getitem__(self, key: Literal[View.shelf_view]) -> ShelfView: ...
    @overload
    def __getitem__(self, key: Literal[View.book_view]) -> BookView: ...
    @overload
    def __getitem__(self, key: Literal[View.typespeed_view]) -> TypespeedV: ...
    @overload
    def __getitem__(self, key: Literal[View.steno_view]) -> StenoView: ...
    @overload
    def __getitem__(self, key: View) -> QWidget: ...


class Book(Protocol):
    title: str
    path: str
    chapter_lookup: dict[str, int]
    progress: float
    dirty: bool

    @property
    def chapters(self) -> list[Chapter]: ...

    def updateProgress(self, progress: float) -> None: ...


class Selector(Protocol, QWidget):  # type: ignore[misc]
    changed: pyqtBoundSignal

    def set_(self, value: object) -> None: ...
