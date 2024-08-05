import time
from typing import Callable

from . import Logger


def benchmark(func: Callable) -> Callable:
    def wrapper(*args, **kwargs) -> None:
        start = time.perf_counter()
        func(*args, **kwargs)
        stop = time.perf_counter()
        Logger.debug(f"executed {func.__qualname__} in {stop-start:.3f}s")

    return wrapper
