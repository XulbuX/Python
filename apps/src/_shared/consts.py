from pathlib import Path
from typing import Any
import subprocess
import sys

# PREVENT A CONSOLE WINDOW FROM FLASHING WHEN CALLING EXTERNAL PROCESSES
POPEN_FLAGS: dict[str, Any] = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}

_ICON_DIR: Path = Path(__file__).resolve().parent / "assets" / "icons"

ICONS: dict[str, Path] = {
    "chevron-left": _ICON_DIR / "chevron-left.svg",
    "chevron-right": _ICON_DIR / "chevron-right.svg",
    "loader": _ICON_DIR / "loader.svg",
    "refresh-ccw": _ICON_DIR / "refresh-ccw.svg",
    "x": _ICON_DIR / "x.svg",
}

COLORS: dict[str, dict[str, str]] = {
    "dark": {
        "background": "#09090B",
        "foreground": "#FAFAFA",
        "muted_foreground": "#A1A1AA",
        "placeholder_foreground": "#52525B",
        "border": "#27272A",
        "primary": "#6366F1",
        "primary_hover": "#5950EB",
        "primary_foreground": "#FFFFFF",
        "secondary": "#09090B",
        "secondary_hover": "#27272A",
        "secondary_border": "#3F3F46",
        "secondary_foreground": "#FAFAFA",
        "card": "#FAFAFA",
        "card_hover": "#E4E4E7",
        "card_foreground": "#09090B",
        "destructive": "#290D0D",
        "destructive_border": "#7F1D1D",
        "destructive_foreground": "#FFDEDE",
        "destructive_muted": "#FCA5A5",
        "destructive_label": "#F87171",
        "link": "#818CF8",
    },
    "light": {
        "background": "#FFFFFF",
        "foreground": "#09090B",
        "muted_foreground": "#71717A",
        "placeholder_foreground": "#A1A1AA",
        "border": "#F0F0F2",
        "primary": "#4F46E5",
        "primary_hover": "#4338CA",
        "primary_foreground": "#FFFFFF",
        "secondary": "#FFFFFF",
        "secondary_hover": "#F4F4F5",
        "secondary_border": "#E0E0E3",
        "secondary_foreground": "#18181B",
        "card": "#18181B",
        "card_hover": "#3F3F46",
        "card_foreground": "#FAFAFA",
        "destructive": "#FFEBEB",
        "destructive_border": "#FCA5A5",
        "destructive_foreground": "#7F1D1D",
        "destructive_muted": "#B91C1C",
        "destructive_label": "#C0392B",
        "link": "#4F46E5",
    },
}
