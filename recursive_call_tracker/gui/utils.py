# This file is part of recursive-call-tracker. See __init__.py for more details.
# Copyright (C) 2022  Numerlor

"""Utils needed to work with the Qt GUI."""

from __future__ import annotations

from PySide6 import QtCore

from __feature__ import snake_case, true_property  # noqa: F401


def create_interrupt_timer(parent: QtCore.QObject) -> QtCore.QTimer:
    """Create a timer that interrupts the Qt event loop regularly to let python process signals."""
    timer = QtCore.QTimer(parent)
    timer.interval = 50
    timer.timeout.connect(lambda: None)
    timer.start()
    return timer
