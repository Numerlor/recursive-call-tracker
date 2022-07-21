import threading
import time

from .call_tracker import CallTracker
from .gui.window import run

tracker = CallTracker()


@tracker
def depth(l):
    if len(l) == 0:
        return 1

    return max([depth(e) for e in l]) + 1


depth([[], [[]], [[[]]]])
run(tracker.start_calls[0])
