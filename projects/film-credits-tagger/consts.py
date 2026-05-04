# pyright: basic
from pathlib import Path
from typing import TypedDict
from enum import IntEnum
import customtkinter as ctk


class FieldType(IntEnum):
    SINGLE = 1  # SINGLE-LINE CTkEntry
    EXPANDING = 2  # SINGLE-LINE THAT EXPANDS TO MULTI-LINE (NO HARD NEWLINES)
    MULTILINE = 3  # FREE MULTI-LINE WITH NEWLINES ALLOWED


class ValType(IntEnum):
    Date = 1  # DD/MM/YYYY → YYYY:MM:DD 00:00:00 (ExifTool format)
    Lang = 2  # ISO 639-2 three-letter code, e.g. eng, fra, deu


class _FieldDefRequired(TypedDict):
    tags: tuple[str, ...]  # PRIMARY (CROSS-PLATFORM) TAG FIRST; ALL ARE WRITTEN, PRIMARY USED FOR READING BACK
    type: FieldType


class FieldDef(_FieldDefRequired, total=False):
    placeholder: str
    val_type: ValType


class FieldEntry(TypedDict):
    tags: tuple[str, ...]  # PRIMARY (CROSS-PLATFORM) TAG FIRST; ALL ARE WRITTEN, PRIMARY USED FOR READING BACK
    widget: ctk.CTkEntry  # ctk.CTkEntry OR MultilineEntry


_ASSET_DIR: Path = Path(__file__).resolve().parent / "assets"
_ICON_DIR: Path = _ASSET_DIR / "icons"

APP_ICON_PNG: Path = _ASSET_DIR / "img" / "FilmCreditsTagger.png"

VIDEO_FILE_TYPES: list[tuple[str, str]] = [
    ("Video Files", "*.mp4 *.mov *.m4v *.m4a *.3gp *.3g2"),
    ("All Files", "*.*"),
]

COVER_ART_FILE_TYPES: list[tuple[str, str]] = [
    ("Images", "*.jpg *.jpeg *.png *.webp *.tiff *.tif"),
]

ICONS: dict[str, Path] = {
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
        "primary": "#2563EB",
        "primary_hover": "#1D4ED8",
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
        "link": "#60A5FA",
    },
    "light": {
        "background": "#FFFFFF",
        "foreground": "#09090B",
        "muted_foreground": "#71717A",
        "placeholder_foreground": "#A1A1AA",
        "border": "#F0F0F2",
        "primary": "#2563EB",
        "primary_hover": "#1D4ED8",
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
        "link": "#2563EB",
    },
}
