from enum import IntEnum
from pathlib import Path
from typing import NotRequired, TypedDict
import customtkinter as ctk  # pyright:ignore[reportMissingTypeStubs]

ASSET_DIR: Path = Path(__file__).resolve().parent / "assets"
"""Absolute path to the assets directory."""


class ValueType(IntEnum):
    """Validation format types for metadata fields."""

    Date = 1  # DD/MM/YYYY → YYYY:MM:DD 00:00:00 (ExifTool format).
    Lang = 2  # ISO 639-2 code: eng, fra, deu…


class FieldType(IntEnum):
    """UI input widget behavior type for metadata fields."""

    SINGLE = 1  # Single-line `CTkEntry`.
    EXPANDING = 2  # Single-line that expands to multi-line (no hard newlines).
    MULTILINE = 3  # Free multi-line with newlines allowed.


class FieldDef(TypedDict):
    """Complete definition specifying metadata field properties."""

    tags: tuple[str, ...]  # Primary (cross-platform) tag first; all are written, primary used for reading back.
    field_type: FieldType
    placeholder: NotRequired[str]
    value_type: NotRequired[ValueType]


class FieldEntry(TypedDict):
    """Runtime field entry mapping tags to UI entry widgets."""

    tags: tuple[str, ...]  # Primary (cross-platform) tag first; all are written, primary used for reading back.
    widget: ctk.CTkEntry  # `ctk.CTkEntry` or `MultilineEntry`.


APP_ICON_PNG: Path = ASSET_DIR / "img" / "film-credits-tagger.png"
"""Absolute path to the app icon image file."""

VIDEO_FILE_TYPES: list[tuple[str, str]] = [("Video Files", "*.mp4 *.mov *.m4v *.m4a *.3gp *.3g2"), ("All Files", "*.*")]
"""File type filters for video file selection dialogs."""

COVER_ART_FILE_TYPES: list[tuple[str, str]] = [("Images", "*.jpg *.jpeg *.png *.webp *.tiff *.tif")]
"""File type filters for cover art file selection dialogs."""

# Each field lists tags in priority order: cross-platform first, OS-specific appended.
# `ItemList` tags write standard iTunes/QuickTime atoms; Microsoft tags cover Windows Explorer/WMP:
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
"""Flat mapping of field labels to definitions for easy lookup."""
