from __future__ import annotations

import enum
import typing as t
from collections import abc
from functools import wraps

P = t.ParamSpec("P")
R = t.TypeVar("R")


class Uninitialized(enum.Enum):  # noqa: D101
    UNINITIALIZED = enum.auto()

    def __str__(self):
        return self._name_
    __repr__ = __str__


UNINITIALIZED = Uninitialized.UNINITIALIZED


class RecursiveCall:
    """
    A single recursive call.

    Recursive calls from within this call should be registered with the `add_callee` method.
    """
    def __init__(self, args: tuple[object, ...], kwargs: dict[str, object], caller: None | RecursiveCall = None):
        self.caller = caller
        self.callees = list[RecursiveCall]()
        self.args = args
        self.kwargs = kwargs
        self.result: object | t.Literal[UNINITIALIZED] = UNINITIALIZED

    def add_callee(self, callee: RecursiveCall):
        """Add a callee to the `callees` attribute, and register self as its caller."""
        self.callees.append(callee)
        callee.caller = self

    def __repr__(self):
        return f"<RecursiveCall callees={self.callees} args={self.args} kwargs={self.kwargs} result={self.result})"


class CallTracker:
    """
    Track all recursive calls of the wrapped function.

    The initial call for each recursive chain is stored in the `start_calls` attribute.
    """
    def __init__(self):
        self._active_calls = list[RecursiveCall]()
        self.start_calls = list[RecursiveCall]()

    def __call__(self, func: abc.Callable[P, R]) -> abc.Callable[P, R]:

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            call = RecursiveCall(args, kwargs)

            if self._active_calls:
                self._active_calls[-1].add_callee(call)
            else:
                self.start_calls.append(call)

            self._active_calls.append(call)

            result = func(*args, **kwargs)

            self._active_calls.pop().result = result

            return result

        return wrapper
