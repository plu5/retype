from qt import QAction

from typing import TYPE_CHECKING

from retype.resource_handler import getIcon


def makeAction(name,  # type: str
               func,  # type: Callable[[], None]
               tooltip=None,  # type: str | None
               shortcuts=None,  # type: list[str] | None
               icon=None,  # type: str | None
               menu=None,  # type: QWidget
               widget=None,  # type: QWidget
               **_
               ):
    # type: (...) -> QAction
    action = QAction(name)
    action.triggered.connect(func)
    if tooltip:
        action.setToolTip(tooltip)
    if shortcuts:
        action.setShortcuts(shortcuts)
    if icon:
        action.setIcon(getIcon(icon))
    if menu:
        menu.addAction(action)
    if widget:
        widget.addAction(action)
    return action


if TYPE_CHECKING:
    from qt import QWidget  # noqa: F401
    from typing import Callable  # noqa: F401
