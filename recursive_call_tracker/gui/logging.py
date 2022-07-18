# This file is part of recursive-call-tracker. See __init__.py for more details.
# Copyright (C) 2022  Numerlor

"""Logging utilities used alongside Qt."""

import logging
import types
from collections import abc
from contextlib import contextmanager
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from __feature__ import snake_case, true_property  # noqa: F401

QT_LOG_LEVELS = {
    0: logging.DEBUG,
    4: logging.INFO,
    1: logging.WARNING,
    2: logging.ERROR,
    3: logging.CRITICAL,
}

log = logging.getLogger(__name__)


@contextmanager
def patch_log_module(logger: logging.Logger, module_name: str) -> abc.Iterator[None]:
    """Patch logs using `logger` within this context manager to use `module_name` as the module name."""
    original_find_caller = logger.findCaller

    def patched_caller(
        self: logging.Logger, stack_info: bool, stack_level: int
    ) -> tuple[str, int, str, str] | None:
        """Patch filename on logs after this was applied to be `module_name`."""
        _, lno, func, sinfo = original_find_caller(stack_info, stack_level)
        return module_name, lno, func, sinfo

    logger.findCaller = types.MethodType(patched_caller, logger)
    try:
        yield
    finally:
        logger.findCaller = original_find_caller


def init_qt_logging() -> None:
    """Redirect QDebug calls to `logger`."""

    def handler(level: int, _context: QtCore.QMessageLogContext, message: str) -> None:
        with patch_log_module(log, "<Qt>"):
            log.log(QT_LOG_LEVELS[level], message)

    QtCore.qInstallMessageHandler(handler)


def log_exceptions(
    exctype: type[BaseException],
    value: BaseException,
    tb: types.TracebackType | None,
) -> None:
    """
    Log exception, mocking the module to the traceback's module and emit `traceback_sig`` with formatted exception.

    If the traceback is not provided, use "UNKNOWN" as the module name.
    """
    if exctype is KeyboardInterrupt:
        QtWidgets.QApplication.instance().exit()
        return

    if tb is None:
        module_to_patch = "UNKNOWN"
    else:
        module_to_patch = Path(tb.tb_frame.f_code.co_filename).stem
    with patch_log_module(log, module_to_patch):
        log.critical("Uncaught exception:", exc_info=(exctype, value, tb))
