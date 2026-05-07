from pathlib import Path


_ASSET_DIR: Path = Path(__file__).resolve().parent / "assets"

APP_ICON_PNG: Path = _ASSET_DIR / "img" / "VideoTrimmer.png"

VIDEO_FILE_TYPES: list[tuple[str, str]] = [
    ("Video Files", "*.mp4 *.mov *.m4v *.mkv *.webm *.avi *.flv *.wmv *.ts *.m4a *.3gp *.3g2"),
    ("All Files", "*.*"),
]
