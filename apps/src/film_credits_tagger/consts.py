from enum import IntEnum
from pathlib import Path
from typing import TypedDict
import customtkinter as ctk  # type: ignore[no-stubs]


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

APP_ICON_PNG: Path = _ASSET_DIR / "img" / "FilmCreditsTagger.png"

VIDEO_FILE_TYPES: list[tuple[str, str]] = [("Video Files", "*.mp4 *.mov *.m4v *.m4a *.3gp *.3g2"), ("All Files", "*.*")]

COVER_ART_FILE_TYPES: list[tuple[str, str]] = [("Images", "*.jpg *.jpeg *.png *.webp *.tiff *.tif")]

# EACH FIELD LISTS ITS TAGS IN PRIORITY ORDER: CROSS-PLATFORM FIRST, OS-SPECIFIC APPENDED.
# ItemList TAGS WRITE STANDARD iTunes/QuickTime ATOMS (©dir, ©wrt, ©prd, …) RECOGNIZED BY
# macOS, VLC, MPV AND LINUX MEDIA PLAYERS. MICROSOFT TAGS COVER WINDOWS EXPLORER / WMP.
FIELDS: dict[str, dict[str, FieldDef]] = {
    "General": {
        "Title": {"tags": ("-ItemList:Title",), "field_type": FieldType.SINGLE},
        "Short Description": {"tags": ("-ItemList:Description", "-Microsoft:Subtitle"), "field_type": FieldType.SINGLE},
    },
    "Details": {
        "Release Date": {
            "tags": ("-ItemList:Year",),
            "placeholder": "DD/MM/YYYY",
            "field_type": FieldType.SINGLE,
            "value_type": ValueType.Date,
        },
        "Creation Date": {
            "tags": ("-ItemList:ContentCreateDate",),
            "placeholder": "DD/MM/YYYY",
            "field_type": FieldType.SINGLE,
            "value_type": ValueType.Date,
        },
        "Copyright": {"tags": ("-ItemList:Copyright",), "field_type": FieldType.SINGLE},
        "Rating": {
            "tags": ("-ItemList:ContentRating", "-Microsoft:ParentalRating"),
            "placeholder": "G, PG, PG-13, R, NC-17\u2026",
            "field_type": FieldType.SINGLE,
        },
        "Media Type": {
            "tags": ("-ItemList:MediaType",),
            "placeholder": "Movie, TV Show, Music Video\u2026",
            "field_type": FieldType.SINGLE,
        },
        "Language": {
            "tags": ("-ItemList:Language",),
            "placeholder": "ISO 639-2 code: eng, fra, deu\u2026",
            "field_type": FieldType.SINGLE,
            "value_type": ValueType.Lang,
        },
    },
    "Categories": {
        "Genre(s)": {
            "tags": ("-ItemList:Genre",),
            "placeholder": "action, comedy, horror\u2026",
            "field_type": FieldType.EXPANDING,
        },
        "Keywords": {
            "tags": ("-ItemList:Keywords",),
            "placeholder": "heist, female-lead, cult-classic\u2026",
            "field_type": FieldType.SINGLE,
        },
    },
    "Credits": {
        "Prod. Company": {"tags": ("-ItemList:Studio",), "field_type": FieldType.SINGLE},
        "Director(s)": {"tags": ("-ItemList:Director", "-Microsoft:Director"), "field_type": FieldType.EXPANDING},
        "Writer(s)": {"tags": ("-ItemList:Composer", "-Microsoft:Writer"), "field_type": FieldType.EXPANDING},
        "Producer(s)": {"tags": ("-ItemList:Producer", "-Microsoft:Producer"), "field_type": FieldType.EXPANDING},
        "Publisher(s)": {"tags": ("-Microsoft:Publisher",), "field_type": FieldType.EXPANDING},
        "Cast": {"tags": ("-ItemList:Artist",), "field_type": FieldType.EXPANDING},
    },
    "Descriptions": {
        "Long Description": {"tags": ("-ItemList:LongDescription",), "field_type": FieldType.MULTILINE},
        "Comment": {"tags": ("-ItemList:Comment",), "field_type": FieldType.MULTILINE},
    },
}

FIELDS_FLAT: dict[str, FieldDef] = {label: fd for section in FIELDS.values() for label, fd in section.items()}
