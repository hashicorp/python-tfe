from __future__ import annotations

import re
import time
from collections.abc import Callable

_STRING_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{2,}$")


def poll_until(
    fn: Callable[[], bool],
    *,
    interval_s: float = 5.0,
    timeout_s: float | None = 600,
) -> bool:
    start = time.time()
    while True:
        value = fn()
        if value:
            return True
        if timeout_s is not None and (time.time() - start) > timeout_s:
            raise TimeoutError("Timed out")
        time.sleep(interval_s)


def valid_string(v: str | None) -> bool:
    return v is not None and str(v).strip() != ""


def valid_string_id(v: str | None) -> bool:
    return v is not None and _STRING_ID_PATTERN.match(str(v)) is not None
