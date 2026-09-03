from pathlib import Path

ASSET_DIR: Path = Path(__file__).resolve().parent / "assets"
"""Absolute path to the assets directory."""

APP_ICON_PNG: Path = ASSET_DIR / "img" / "video-trimmer.png"
"""Absolute path to the app icon image file."""

VIDEO_FILE_TYPES: list[tuple[str, str]] = [
    ("Video Files", "*.mp4 *.mov *.m4v *.mkv *.webm *.avi *.flv *.wmv *.ts *.m4a *.3gp *.3g2"),
    ("All Files", "*.*"),
]
"""File type filters for video file selection dialogs."""
