from typing import Optional
import re

from consts import ValueType


def normalize_multi(val: str) -> str:
    """Normalize user-entered separators to `; ` for multi-value tags."""
    return "; ".join(part for part in (raw_part.strip() for raw_part in re.split(r"\s*[/;,]\s*", val)) if part)


def parse_date(val: str) -> str:
    """Parse a user-entered date (`DD/MM/YYYY`, flexible separators) into ExifTool format `YYYY:MM:DD 00:00:00`.<br>
    Raises `ValueError` with a human-readable message if the input cannot be parsed."""
    _fmt = "Expected format: DD/MM/YYYY (e.g. 25/12/2026)"

    if not (match := re.fullmatch(r"(\d{1,2})[./\- ](\d{1,2})[./\- ](\d{4})", val.strip())):
        raise ValueError(f'Cannot parse "{val}" as a date.\n{_fmt}')

    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))

    if not (1 <= month <= 12):
        raise ValueError(f'Invalid month ({month}) in "{val}".\n{_fmt}')
    if not (1 <= day <= 31):
        raise ValueError(f'Invalid day ({day}) in "{val}".\n{_fmt}')

    return f"{year}:{month:02d}:{day:02d} 00:00:00"


def exiftool_date_to_display(exiftool_date: str) -> Optional[str]:
    """Convert an ExifTool date string (`YYYY:MM:DD …`) to display format `DD/MM/YYYY`.<br>
    Returns `None` if `exiftool_date` does not start with a recognizable `YYYY:MM:DD` pattern."""
    if match := re.match(r"(\d{4}):(\d{2}):(\d{2})", exiftool_date):
        return f"{match.group(3)}/{match.group(2)}/{match.group(1)}"
    return None


def validate_field(val: str, value_type: ValueType) -> Optional[str]:
    """Return a human-readable error string if `val` fails validation for `value_type`, else `None`."""
    match value_type:
        case ValueType.Date:
            try:
                parse_date(val)
            except ValueError as err:
                return str(err)

        case ValueType.Lang:
            if not re.fullmatch(r"[a-z]{3}", val.strip()):
                return (
                    f'"{val}" is not a valid ISO 639-2 language code.\n'
                    "Expected exactly 3 lowercase letters (e.g. eng, fra, deu)."
                )

        case _:
            return None
