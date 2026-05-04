# pyright: basic
from pathlib import Path
from typing import TypedDict
from enum import IntEnum
import customtkinter as ctk


class ValueType(IntEnum):
    Date = 1  # DD/MM/YYYY → YYYY:MM:DD 00:00:00 (EXIFTOOL FORMAT)
    Lang = 2  # ISO 639-2 CODE: eng, fra, deu…


class FieldType(IntEnum):
    SINGLE = 1  # SINGLE-LINE CTkEntry
    EXPANDING = 2  # SINGLE-LINE THAT EXPANDS TO MULTI-LINE (NO HARD NEWLINES)
    MULTILINE = 3  # FREE MULTI-LINE WITH NEWLINES ALLOWED


class _FieldDefRequired(TypedDict):
    tags: tuple[str, ...]  # PRIMARY (CROSS-PLATFORM) TAG FIRST; ALL ARE WRITTEN, PRIMARY USED FOR READING BACK
    field_type: FieldType


class FieldDef(_FieldDefRequired, total=False):
    placeholder: str
    value_type: ValueType


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

# EACH FIELD LISTS ITS TAGS IN PRIORITY ORDER: CROSS-PLATFORM FIRST, OS-SPECIFIC APPENDED.
# ItemList TAGS WRITE STANDARD iTunes/QuickTime ATOMS (©dir, ©wrt, ©prd, …) RECOGNIZED BY
# macOS, VLC, MPV AND LINUX MEDIA PLAYERS. MICROSOFT TAGS COVER WINDOWS EXPLORER / WMP.
FIELDS: dict[str, FieldDef] = {
    "Title": {"tags": ("-ItemList:Title", ), "field_type": FieldType.SINGLE},
    "Short Description": {"tags": ("-ItemList:Description", "-Microsoft:Subtitle"), "field_type": FieldType.SINGLE},
    "Release Date": {
        "tags": ("-ItemList:Year", ),
        "placeholder": "DD/MM/YYYY",
        "field_type": FieldType.SINGLE,
        "value_type": ValueType.Date,
    },
    "Creation Date": {
        "tags": ("-ItemList:ContentCreateDate", ),
        "placeholder": "DD/MM/YYYY",
        "field_type": FieldType.SINGLE,
        "value_type": ValueType.Date,
    },
    "Copyright": {"tags": ("-ItemList:Copyright", ), "field_type": FieldType.SINGLE},
    "Rating": {
        "tags": ("-ItemList:ContentRating", "-Microsoft:ParentalRating"),
        "placeholder": "G, PG, PG-13, R, NC-17\u2026",
        "field_type": FieldType.SINGLE,
    },
    "Media Type": {
        "tags": ("-ItemList:MediaType", ),
        "placeholder": "Movie, TV Show, Music Video\u2026",
        "field_type": FieldType.SINGLE,
    },
    "Language": {
        "tags": ("-ItemList:Language", ),
        "placeholder": "ISO 639-2 code: eng, fra, deu\u2026",
        "field_type": FieldType.SINGLE,
        "value_type": ValueType.Lang,
    },
    "Genre(s)": {"tags": ("-ItemList:Genre", ), "field_type": FieldType.EXPANDING},
    "Keywords": {
        "tags": ("-ItemList:Keywords", ),
        "placeholder": "action, adventure, thriller\u2026",
        "field_type": FieldType.SINGLE,
    },
    "Studio / Prod. Company": {"tags": ("-ItemList:Studio", ), "field_type": FieldType.SINGLE},
    "Director(s)": {"tags": ("-ItemList:Director", "-Microsoft:Director"), "field_type": FieldType.EXPANDING},
    "Writer(s)": {"tags": ("-ItemList:Composer", "-Microsoft:Writer"), "field_type": FieldType.EXPANDING},
    "Producer(s)": {"tags": ("-ItemList:Producer", "-Microsoft:Producer"), "field_type": FieldType.EXPANDING},
    "Publisher(s)": {"tags": ("-Microsoft:Publisher", ), "field_type": FieldType.EXPANDING},
    "Cast / Actor(s)": {"tags": ("-ItemList:Artist", ), "field_type": FieldType.EXPANDING},
    "Long Description": {"tags": ("-ItemList:LongDescription", ), "field_type": FieldType.MULTILINE},
    "Comment": {"tags": ("-ItemList:Comment", ), "field_type": FieldType.MULTILINE},
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
