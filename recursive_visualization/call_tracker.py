from __future__ import annotations

import enum
import typing as t
from collections import abc
from functools import wraps

P = t.ParamSpec("P")
R = t.TypeVar("R")

INDENT = 4


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

    def add_callee(self, callee: RecursiveCall) -> None:
        """Add a callee to the `callees` attribute, and register self as its caller."""
        self.callees.append(callee)
        callee.caller = self

    def __repr__(self) -> str:
        return f"<RecursiveCall callees={self.callees} args={self.args} kwargs={self.kwargs} result={self.result})"

    def pretty_print(self) -> None:
        """Pretty print this call."""
        current = self
        depth = 0
        callee_iterators = {}

        while current is not None:
            if current not in callee_iterators:
                callee_iterators[current] = iter(current.callees)
                joined_kwargs = ", ".join(f"{name}={value!r}" for name, value in current.kwargs.items())
                print(f"{self._indent_from_depth(depth,)}RecursiveCall")
                hanging_indent = self._indent_from_depth(depth, hanging=True)
                print(f"{hanging_indent}result={current.result!r}")
                print(f"{hanging_indent}args={current.args!r}")
                print(f"{hanging_indent}kwargs=dict({joined_kwargs})")
                if not current.callees:
                    print(f"{hanging_indent}callees=[]")
                else:
                    print(f"{hanging_indent}callees=[")

            try:
                current = next(callee_iterators[current])
            except StopIteration:
                if current.callees:
                    print(f"{self._indent_from_depth(depth, hanging=True)}],")
                depth -= 1
                current = current.caller
            else:
                depth += 1

    @staticmethod
    def _indent_from_depth(depth: int, *, hanging: bool = False) -> str:
        """Get the spaces to indent for `depth`. If `hanging` is True, an additional indentation level is added."""
        if not depth:
            indent_width = 0
        else:
            # Each depth has base indent + hanging from callees
            indent_width = INDENT * depth * 2
        if hanging:
            indent_width += INDENT
        return " " * indent_width


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
