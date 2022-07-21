from __future__ import annotations

import logging
import sys
import typing as t
from collections import abc
from itertools import cycle

from PySide6 import QtCore, QtGui, QtWidgets

from __feature__ import snake_case, true_property  # noqa: F401
from recursive_call_tracker.gui.logging import log_exceptions
from recursive_call_tracker.gui.utils import create_interrupt_timer
from recursive_call_tracker.utils import prettify_kwargs_repr

if t.TYPE_CHECKING:
    import typing_extensions as te

    from recursive_call_tracker.call_tracker import RecursiveCall

log = logging.getLogger(__name__)


DEPTH_COLORS = (
    QtGui.QColor(206, 240, 206),
    QtGui.QColor(208, 225, 242),
    QtGui.QColor(255, 213, 168),
    QtGui.QColor(255, 191, 191),
)


# todo navigate with wheel?
class CallWidget(QtWidgets.QFrame):
    """Widget to represent a `RecursiveCall`. TODO MORE."""

    def __init__(
        self,
        call: RecursiveCall,
        *,
        frame: bool,
        parent: QtWidgets.QWidget | None = None,
    ):
        super().__init__(parent)
        self._callee_widgets = []
        self._callees_shown = True
        self.auto_fill_background = True

        # region GUI setup
        if frame:
            self.set_frame_style(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Sunken)
        self.focus_policy = QtCore.Qt.FocusPolicy.StrongFocus

        self.layout_ = layout = QtWidgets.QVBoxLayout(self)
        layout.contents_margins = QtCore.QMargins(6, 6, 1, 1)
        layout.set_spacing(3)
        # todo limit labels
        layout.add_widget(QtWidgets.QLabel(f"Args: {call.args}", self))
        layout.add_widget(
            QtWidgets.QLabel(f"Kwargs: {prettify_kwargs_repr(call.kwargs)}", self)
        )
        layout.add_widget(QtWidgets.QLabel(f"Result: {call.result!r}", self))
        self.callee_label = QtWidgets.QLabel("Base case", self)
        layout.add_widget(self.callee_label)

        # Without forcing the palette to not inherit from the parent,
        # we get the parent's color until the widget is colored once.
        # Setting the color twice somehow forces the desired behaviour.
        palette = self.palette
        palette.set_color(QtGui.QPalette.Window, QtGui.QColor(240, 239, 240))
        palette.set_color(QtGui.QPalette.Window, QtGui.QPalette().window().color())
        self.palette = palette
        # endregion

    def add_callee_widget(self, callee_widget: CallWidget) -> None:
        """Add a callee `CallWidget` to the end of this widget's layout."""
        if not self._callee_widgets:
            self.callee_label.text = "Callees:"

        self.layout_.add_widget(callee_widget)
        self._callee_widgets.append(callee_widget)
        callee_widget.set_parent(self)

    @classmethod
    def recursive_from_top_call(
        cls,
        call: RecursiveCall,
        *,
        parent: QtWidgets.QWidget | None = None,
    ) -> te.Self:
        """Create a CallWidget for `call`, and all of its recursive callees as child widgets of the created widget."""
        top_widget = cls(call, frame=False, parent=parent)
        stack = [(call, top_widget)]

        while stack:
            call, widget = stack.pop()

            for child_call in call.callees:
                child_widget = cls(child_call, frame=True, parent=widget)
                widget.add_callee_widget(child_widget)
                stack.append((child_call, child_widget))

        return top_widget

    def mouse_double_click_event(self, event: QtGui.QMouseEvent) -> None:
        """Show/hide callees when double clicked. TODO also hide everything other then result with multiple collapse levels."""
        if self._callees_shown:
            method = QtWidgets.QWidget.hide
        else:
            method = QtWidgets.QWidget.show

        self._callees_shown = not self._callees_shown
        for callee in self._callee_widgets:
            method(callee)

    def focus_in_event(self, event: QtGui.QFocusEvent) -> None:
        """Set color for self and all parents on focus in."""
        self._color_selected_path(colors=cycle(DEPTH_COLORS))

    def focus_out_event(self, event: QtGui.QFocusEvent) -> None:
        """Reset colors on focus out."""
        self._color_selected_path(colors=cycle([QtGui.QPalette().window().color()]))

    def _color_selected_path(self, *, colors: abc.Iterable[QtGui.QColor]) -> None:
        """Color all the widgets up to self with colors from `colors`, starting at the top widget."""
        widget = self
        active_widgets = [self]

        while True:
            parent = widget.parent()
            if not isinstance(parent, self.__class__):
                break
            widget = parent
            active_widgets.append(parent)

        for widget, color in zip(reversed(active_widgets), colors):
            palette = widget.palette
            palette.set_color(QtGui.QPalette.Window, color)
            widget.palette = palette


class Window(QtWidgets.QMainWindow):
    """todo."""

    def __init__(self, call: RecursiveCall):
        super().__init__()
        widget = QtWidgets.QWidget()
        self.set_central_widget(widget)

        layout = QtWidgets.QHBoxLayout(widget)

        call_widget = CallWidget.recursive_from_top_call(call, parent=widget)
        call_widget.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Maximum,
            QtWidgets.QSizePolicy.Maximum,
        )
        layout.add_widget(call_widget, alignment=QtCore.Qt.AlignmentFlag.AlignTop)

        placeholder_label = QtWidgets.QTextEdit("placeholder", widget)
        layout.add_widget(placeholder_label)


# todo multiple calls sohuld be possible
def run(call: RecursiveCall) -> None:
    """Todo, name too."""
    app = QtWidgets.QApplication()
    app.set_style("Fusion")
    window = Window(call)
    interrupt = create_interrupt_timer(app)  # noqa: F841
    sys.excepthook = log_exceptions
    window.show()
    app.exec()
