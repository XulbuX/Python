import re

_TIME_RE = re.compile(r"^\s*(?:(\d+):)?(?:(\d{1,2}):)?(\d+(?:\.\d+)?)\s*$")


def parse_time(val: str) -> float | None:
    """Parse `HH:MM:SS(.ms)`, `MM:SS(.ms)`, or `SS(.ms)` into seconds.<br>
    Returns `None` if the input cannot be parsed."""

    if not val.strip():
        return None
    if not (match := _TIME_RE.match(val)):
        return None

    parts: list[str] = [part for part in (match.group(1), match.group(2), match.group(3)) if part is not None]
    try:
        nums = [float(part) for part in parts]
    except ValueError:
        return None

    seconds: float = 0.0
    for num in nums:
        seconds = seconds * 60.0 + num

    return seconds


def format_time(seconds: float) -> str:
    """Format `seconds` as `HH:MM:SS.mmm` (or `MM:SS.mmm` when under one hour)."""

    if seconds < 0:
        seconds = 0.0

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds - hours * 3600 - minutes * 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    else:
        return f"{minutes:02d}:{secs:06.3f}"


def frame_to_time(frame: int, fps: float) -> float:
    """Convert a frame number to seconds."""

    return frame / fps


def time_to_frame(seconds: float, fps: float) -> int:
    """Convert seconds to the nearest frame number."""

    return round(seconds * fps)
