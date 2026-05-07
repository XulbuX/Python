from typing import Optional
import re


_TIME_RE = re.compile(r"^\s*(?:(\d+):)?(?:(\d{1,2}):)?(\d+(?:\.\d+)?)\s*$")


def parse_time(val: str) -> Optional[float]:
    """Parse `HH:MM:SS(.ms)`, `MM:SS(.ms)`, or `SS(.ms)` into seconds.<br>
    Returns `None` if the input cannot be parsed."""
    if not val.strip():
        return None
    if not (m := _TIME_RE.match(val)):
        return None

    parts: list[str] = [p for p in (m.group(1), m.group(2), m.group(3)) if p is not None]
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        return None

    seconds: float = 0.0
    for n in nums:
        seconds = seconds * 60.0 + n

    return seconds


def format_time(seconds: float) -> str:
    """Format `seconds` as `HH:MM:SS.mmm` (or `MM:SS.mmm` when under one hour)."""
    if seconds < 0:
        seconds = 0.0

    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds - h * 3600 - m * 60

    if h > 0:
        return f"{h:02d}:{m:02d}:{s:06.3f}"
    else:
        return f"{m:02d}:{s:06.3f}"
