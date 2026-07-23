#!/usr/bin/env python3
# [x-cmds]: UPDATE

"""A really advanced directory tree generator
with a lot of options and customization."""

from __future__ import annotations

import fnmatch
import os
import re
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import ClassVar, NamedTuple, TypedDict
import xulbux as xx
from xulbux.ansi import AnyStyle, S, StyledText
from xulbux.base.consts import COLOR

ARGS = xx.console.get_args(
    {
        "base_dir": "before",
        "ignore_dirs": {"-i", "--ignore", "--ignore-dirs"},
        "no_progress": {"-n", "-np", "--no-progress"},
        "use_all_defaults": {"-d", "--default"},
        "help": {"-h", "--help"},
    }
)

DEFAULT: ScriptDefaults = {
    "ignore_dirs": [],
    "auto_ignore": True,
    "include_file_contents": False,
    "tree_style": 2,
    "indent": 2,
    "into_file": False,
}

COLORS: TreeColors = {
    "line": S.BR.BLACK,
    "error": S.RED,
    "dir": S.BR.WHITE,
    "file": S.WHITE,
    "symlink": S.BR.BLUE,
    "executable": S.BR.GREEN,
    "archive": S.BR.RED,
    "image": S.BR.MAGENTA,
    "video": S.MAGENTA,
    "audio": S.BR.CYAN,
    "code": S.BR.YELLOW,
    "content": S.BR.BLACK,
}

# fmt: off
IMAGE_EXTS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff", ".ai"})
ARCHIVE_EXTS = frozenset({".zip", ".tar", ".gz", ".rar", ".7z", ".bz2", ".xz", ".tgz"})
VIDEO_EXTS = frozenset({".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"})
AUDIO_EXTS = frozenset({".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"})
EXEC_EXTS = frozenset({".exe", ".bat", ".cmd", ".com", ".appimage"})
CODE_EXTS = frozenset({
    ".bash", ".bat", ".c", ".cpp", ".css", ".go", ".h", ".hpp", ".html", ".java", ".js", ".json", ".md", ".php", ".ps1", ".py",
    ".pyi", ".pyw", ".rb", ".rs", ".sh", ".ts", ".xml", ".yaml", ".yml", ".zsh"
})
BINARY_EXTENSIONS = frozenset({
    ".7z", ".avi", ".bin", ".cur", ".dat", ".db", ".dll", ".doc", ".docx", ".dylib", ".exe", ".gif", ".gz", ".ico", ".jpeg",
    ".jpg", ".mov", ".mp3", ".mp4", ".pdf", ".png", ".rar", ".so", ".sqlite", ".tar", ".xls", ".xlsx", ".zip"
})


def print_help() -> None:
    title = ["  Tree Generator", " — Quickly generate advanced and good looking directory trees  "]
    StyledText(
        "",
        ("▄" * len("".join(title))),
        (S.INVERSE | S.BG.BLACK)(S.BOLD(title[0]), title[1]),
        ("▀" * len("".join(title))),
        "",
        (S.BOLD("Usage: "), S.BR.GREEN("x-tree "), S.BR.CYAN("<base_dir> "), S.BR.BLUE("[options]")),
        "",
        S.BOLD("Arguments:"),
        ("  ", S.BR.CYAN("base_dir"), "               Base directory to generate tree from ", S.DIM("(default: CWD)")),
        "",
        S.BOLD("Options:"),
        ("  ", S.BR.BLUE("-i"), ", ", S.BR.BLUE("--ignore-dirs", S.DIM("="), "S"), "    Directories to ignore ", S.DIM("(directory paths/names, separated by ", S.BR.CYAN("|"), ")")),  # noqa: E501
        ("  ", S.BR.BLUE("-n"), ", ", S.BR.BLUE("--no-progress"), "      Disable progress display during tree generation"),
        ("  ", S.BR.BLUE("-d"), ", ", S.BR.BLUE("--default"), "          Use all default settings without prompts"),
        "",
        S.BOLD("Examples:"),
        ("  ", S.BR.GREEN("x-tree "), S.BR.BLUE("-i", S.DIM("="), '"/abs/to/dir1 | rel/to/dir2 | dir3"'), "    ", S.DIM("# ", S.ITALIC("Ignore specified directories"))),  # noqa: E501
        ("  ", S.BR.GREEN("x-tree "), S.BR.BLUE("--no-progress"), "                             ", S.DIM("# ", S.ITALIC("Disable progress display"))),  # noqa: E501
        ("  ", S.BR.GREEN("x-tree "), S.BR.BLUE("-d"), "                                        ", S.DIM("# ", S.ITALIC("Use all default settings without prompts"))),  # noqa: E501
        "",
        (S.BOLD("Prompts: "), S.DIM("(interactive — press Enter for defaults, or use ", S.BR.BLUE("-d"), " to skip all)")),
        ("  ", (S.ITALIC | S.DIM)("1"), "  Directories to ignore"),
        ("  ", (S.ITALIC | S.DIM)("2"), "  Include file contents in tree"),
        ("  ", (S.ITALIC | S.DIM)("3"), "  Tree style"),
        ("  ", (S.ITALIC | S.DIM)("4"), "  Indentation size"),
        ("  ", (S.ITALIC | S.DIM)("5"), "  Output tree to file"),
        "",
        sep="\n",
    ).print()
# fmt: on


class TreeColors(TypedDict):
    line: AnyStyle
    error: AnyStyle
    dir: AnyStyle
    file: AnyStyle
    symlink: AnyStyle
    executable: AnyStyle
    archive: AnyStyle
    image: AnyStyle
    video: AnyStyle
    audio: AnyStyle
    code: AnyStyle
    content: AnyStyle


class ScriptDefaults(TypedDict):
    ignore_dirs: list[str]
    auto_ignore: bool
    include_file_contents: bool
    tree_style: int
    indent: int
    into_file: bool


class TreeStylePreset(TypedDict):
    line_ver: str
    line_hor: str
    branch_new: str
    corners: tuple[str, str, str]
    error: str
    ignored: str
    dirname_end: str


class DirScanResult(NamedTuple):
    should_ignore: bool
    total_count: int
    hash_count: int
    show_partial: bool
    entries: tuple[os.DirEntry[str], ...]


@dataclass
class GenerationStats:
    """Tracks statistics for displaying during tree generation."""

    processed_dirs: int = 0
    processed_files: int = 0
    current_depth: int = 0
    max_depth: int = 0


class IGNORE:
    """Contains patterns and logic for determining which
    directories/files to auto-ignore during tree generation."""

    paths: ClassVar[set[str]] = {
        "__pycache__",
        "__tests__",
        "_locales",
        "_site",
        ".adobe",
        ".angular",
        ".archive-unpack",
        ".codeium",
        ".coverage",
        ".docker",
        ".ds_store",
        ".env",
        ".git",
        ".gitlab",
        ".gradle",
        ".hg",
        ".idea",
        ".ipynb_checkpoints",
        ".kube",
        ".minecraft/assets/objects",
        ".minecraft/assets/skins",
        ".mvn",
        ".next",
        ".npm",
        ".nuxt",
        ".nvm",
        ".nx",
        ".output",
        ".scannerwork",
        ".sonar",
        ".svn",
        ".terraform",
        ".tox",
        ".venv",
        ".vs",
        ".webpack",
        ".yarn",
        "*.noindex",
        "*[-_.@]cache",
        "*[-_.@]indexed",
        "*[-_.@]temp",
        "$recycle.bin",
        "addons-l10n",
        "adobe/typeQuest",
        "aggregatedCache",
        "artifacts",
        "autofillStates",
        "backstageInAppNavCache",
        "bin",
        "blob_storage",
        "bower_components",
        "build",
        "cache",
        "cache[-_.@]*",
        "cache[0-9]*",
        "cacheStorage",
        "celeryBeat-schedule",
        "code cache",
        "code_tracker",
        "composer/files",
        "coreSync/cloudNative",
        "coreSync/plugins",
        "coverage-reports",
        "coverage",
        "crlCache",
        "cvs",
        "D3DSCache",
        "data/emojis",
        "dawnCache",
        "dawnGraphiteCache",
        "dawnWebGPUCache",
        "debug",
        "debugbar",
        "dist-newstyle",
        "dist",
        "docker",
        "docs/_build",
        "env",
        "GPUCache",
        "graphicsCache",
        "graphiteDawnCache",
        "grShaderCache",
        "htmlCache",
        "htmlCov",
        "hyphen-data",
        "identityCache",
        "indexed[-_.@]*",
        "indexedDB",
        "indexes",
        "jspm_packages",
        "junit",
        "lib/encodings",
        "local storage",
        "locales",
        "log",
        "logs",
        "media cache files",
        "meta/assets/indexes",
        "meta/assets/objects",
        "metadataIndexer",
        "migrations",
        "node_modules",
        "node",
        "npm",
        "null",
        "nvm",
        "obj",
        "office/*/aggMru",
        "office/*/dts",
        "office/*/usageMetricsStore",
        "office/*/wef",
        "officeFileCache",
        "out",
        "packages",
        "patch64",
        "pods",
        "program64",
        "pythonLocator",
        "recent/automaticDestinations",
        "recent/customDestinations",
        "release",
        "reports",
        "rsa",
        "scriptCache",
        "session storage",
        "shaderCache",
        "site-packages",
        "slCache",
        "spotify/data",
        "spotify/users",
        "ssr/assets",
        "steamLink/avatars",
        "storage/framework",
        "tapCache",
        "target",
        "temp",
        "temp[-_.@]*",
        "test-results",
        "tmp",
        "user/history",
        "user/webStorage",
        "uxp/plugins/external",
        "vendor",
        "venv",
        "virtualBkgnd_*",
        "vscode.git/askPass",
        "webCache2",
        "wheels",
        "x64",
        "x86",
        "xcuserdata",
    }

    sep: str = r"[-_~x@\s]+"
    ext: str = r"(?:\.[-_a-zA-Z0-9]+)*?$"
    pre: str = rf"^(?![a-zA-Z]+\.[a-zA-Z])(?:[a-zA-Z0-9]+{sep})*?"
    date = r"[12][0-9]{3}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])"

    reoccurring: ClassVar[dict[str, str]] = {
        "delimited_number": r"_[0-9]{1,2}",
        "num5-rand12": r"[0-9]{5}-[a-zA-Z0-9]{12}",
        "min_hex32": r"\.min_[a-fA-F0-9]{32}",
        "lower32_num1,2.hex64": r"[a-z]{32}_[0-9]{1,2}\.[a-fA-F0-9]{64}",
        "id3hex4": rf"\w{{3}}[a-fA-F0-9]{{4}}(?:{sep}|{ext})",
        "e_rand32": rf"e_[a-zA-Z0-9]{{32}}(?:{sep}|{ext})",
        "date": date,
        "version.date": r"(?:[0-9]\.){3}" + date,
        "delimited_date": r"(?:[0-9]{2}|[0-9]{4})[-.](?:[0-9]{2}|[0-9]{4})[-.](?:[0-9]{2}|[0-9]{4})",
        "number": r"-?[a-fA-F0-9]{4,}",
        "base64": r"[+/0-9A-Za-z]{8,}={1,2}",
        "hex": r"(?:[a-fA-F0-9]{16}[a-fA-F0-9]{20}|[a-fA-F0-9]{32}|[a-fA-F0-9]{38}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64})",
        "uuid": rf"\{{?[a-zA-Z0-9]{{8}}-[a-zA-Z0-9]{{4}}-[a-zA-Z0-9]{{4}}-[a-zA-Z0-9]{{4}}-[a-zA-Z0-9]{{12}}\}}?(?:[-_a-zA-Z0-9]+(?:{sep}|{ext}))?",  # noqa: E501
        "sid": r"S-[0-9]+-[0-9]+(?:-[0-9]+){2,}",
        "domain": r"[-a-z]+(?:\.[-a-z]+){2,}",
        "rand4": rf"(?![A-Z][a-z]{{3}})(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9]))[a-zA-Z0-9]{{4}}{ext}",
        "rand5": rf"(?![A-Z][a-z]{{4}})(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9]))[a-zA-Z0-9]{{5}}{ext}",
        "rand11": rf"(?![A-Z][a-zA-Z]{{10}})(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9]))[a-zA-Z0-9]{{11}}(?:{sep}|{ext})",
        "rand25": rf"(?![A-Z][a-zA-Z]{{24}})(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9]))[a-zA-Z0-9]{{25}}(?:{sep}|{ext})",
        "rand32": rf"(?![A-Z][a-zA-Z]{{31}})(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9]))[a-zA-Z0-9]{{32}}(?:{sep}|{ext})",
        "rand59": rf"(?![A-Z][a-zA-Z]{{58}})(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9]))[a-zA-Z0-9]{{59}}(?:{sep}|{ext})",
    }
    standalones: ClassVar[dict[str, str]] = {
        "hex2": r"[a-fA-F0-9]{2}",
        "upper2": r"[A-Z]{2}" + ext,
        "alt-lower2": r"alt-[a-z]{2}" + ext,
        "rand_num": r"[A-Z0-9]{2,6}_[a-z][0-9]" + ext,
        "id_num": r"(?:[a-zA-Z0-9]{6}-){2}[a-zA-Z0-9]{6}\s(?:[0-9]{2}|[a-z][0-9]{2})",
        "domain_hex": rf"{reoccurring['domain']}_{reoccurring['hex']}",
        "camelCase_version-hex64": r"[a-z]+(?:[A-Z][a-z]+)*?_[0-9]{1,2}(?:\.[0-9]{1,2})+-[a-fA-F0-9]{64}",
    }

    pattern: re.Pattern[str] = re.compile(
        rf"(?:^(?:{'|'.join(standalones.values())})$|{pre}(?:(?:{sep})?(?:{'|'.join(reoccurring.values())}))+{ext})"
    )


class TreeStyle:
    """Manages the visual styling and ANSI codes for the tree."""

    PRESETS: ClassVar[dict[int, TreeStylePreset]] = {
        1: {
            "line_ver": "│",
            "line_hor": "─",
            "branch_new": "├",
            "corners": ("└", "┘", "┐"),
            "error": "⚠",
            "ignored": "…",
            "dirname_end": "/",
        },
        2: {
            "line_ver": "│",
            "line_hor": "─",
            "branch_new": "├",
            "corners": ("╰", "╯", "╮"),
            "error": "⚠",
            "ignored": "…",
            "dirname_end": "/",
        },
        3: {
            "line_ver": "┃",
            "line_hor": "━",
            "branch_new": "┣",
            "corners": ("┗", "┛", "┓"),
            "error": "⚠",
            "ignored": "…",
            "dirname_end": "/",
        },
        4: {
            "line_ver": "║",
            "line_hor": "═",
            "branch_new": "╠",
            "corners": ("╚", "╝", "╗"),
            "error": "⚠",
            "ignored": "…",
            "dirname_end": "/",
        },
    }

    def __init__(self, style_id: int, indent_size: int):
        preset = self.PRESETS.get(style_id, self.PRESETS[1])
        self.line_ver = preset["line_ver"]
        self.line_hor = preset["line_hor"]
        self.branch_new = preset["branch_new"]
        self.corners = preset["corners"]
        self.error = preset["error"]
        self.ignored = preset["ignored"]
        self.dirname_end = preset["dirname_end"]

        self.indent_size = indent_size
        self.tab = " " * indent_size
        self.line_hor_str = self.line_hor * max(0, indent_size - (2 if indent_size > 2 else 1)) + " "

        # Colors as ANSI strings:
        self.c_reset = StyledText(S.RESET).ansi
        self.c_dim = StyledText(S.DIM).ansi
        self.c_b_in = StyledText(S.BOLD, S.INVERSE).ansi

        self.c_line = StyledText(COLORS["line"]).ansi
        self.c_error = StyledText(COLORS["error"]).ansi
        self.c_dir = StyledText(S.BOLD, COLORS["dir"]).ansi
        self.c_file = StyledText(COLORS["file"]).ansi
        self.c_symlink = StyledText(COLORS["symlink"]).ansi
        self.c_executable = StyledText(COLORS["executable"]).ansi
        self.c_archive = StyledText(COLORS["archive"]).ansi
        self.c_image = StyledText(COLORS["image"]).ansi
        self.c_video = StyledText(COLORS["video"]).ansi
        self.c_audio = StyledText(COLORS["audio"]).ansi
        self.c_code = StyledText(COLORS["code"]).ansi
        self.c_content = StyledText(COLORS["content"]).ansi

        self.c_dir_dim = StyledText(S.DIM, self.c_dir).ansi
        self.c_line_dim = StyledText(S.DIM, self.c_line).ansi

    @classmethod
    def show_styles(cls) -> None:
        """Display available tree styles with their corresponding visual representation."""
        StyledText(
            *(
                (
                    (S.BOLD | S.ITALIC)(f" {style}"),
                    f"  {details['corners'][0]}{details['line_hor']} {details['ignored']}{details['dirname_end']}",
                )
                for style, details in cls.PRESETS.items()
            ),
            sep="\n",
        ).print()


class DirectoryScanner:
    """Handles scanning directories and applying ignore rules."""

    _HASH_NAME_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_~@. \t{}+/=")
    _HEX_SEGMENT = re.compile(r"^[a-fA-F0-9]{8,}$")
    _UUID_ANYWHERE = re.compile(r"[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}")
    _SEP_SPLITTER = re.compile(r"[-_~@\s]+")

    def __init__(self, ignore_dirs: list[str], auto_ignore: bool):
        self.auto_ignore = auto_ignore

        all_ignores = ignore_dirs.copy()
        if auto_ignore:
            all_ignores.extend(d.lower() for d in IGNORE.paths)

        self.ignore_set = frozenset(
            (d.lower().replace("\\", "/") if not Path(d).is_absolute() else "/" + d.lower().replace("\\", "/").lstrip("/"))
            for d in all_ignores
        )

    def should_ignore_path(self, path: str) -> bool:  # noqa: C901
        """Check if a relative path matches any user-specified or default ignore pattern."""
        if not path or not self.ignore_set:
            return False

        path_lower = path.lower().replace("\\", "/")
        path_parts = None

        for pattern in self.ignore_set:
            has_wildcard = "*" in pattern or "[" in pattern

            if not has_wildcard:
                if "/" in pattern:
                    if (pattern.startswith("/") and path_lower == pattern[1:]) or pattern in path_lower:
                        return True
                else:
                    if path_parts is None:
                        path_parts = path_lower.split("/")
                    if pattern in path_parts:
                        return True
            else:
                if "/" in pattern:
                    if pattern.startswith("/"):
                        if fnmatch.fnmatch(path_lower, pattern[1:]):
                            return True
                    else:
                        if path_parts is None:
                            path_parts = path_lower.split("/")
                        pattern_parts = pattern.split("/")
                        plen = len(pattern_parts)
                        for i in range(len(path_parts) - plen + 1):
                            if all(fnmatch.fnmatch(path_parts[i + j], pattern_parts[j]) for j in range(plen)):
                                return True
                else:
                    if path_parts is None:
                        path_parts = path_lower.split("/")
                    if any(fnmatch.fnmatch(part, pattern) for part in path_parts):
                        return True
        return False

    @staticmethod
    @lru_cache(maxsize=4096)
    def is_likely_hash_name(name: str) -> bool:
        """Determine if a filename or directory name is likely a hash or unique identifier."""
        if not DirectoryScanner._HASH_NAME_CHARS.issuperset(name):
            return False
        if len(name) < 2:
            return bool(IGNORE.pattern.match(name))
        if DirectoryScanner._UUID_ANYWHERE.search(name):
            return True

        base = name.rsplit(".", 1)[0] if "." in name else name
        return any(
            len(seg) >= 8 and DirectoryScanner._HEX_SEGMENT.match(seg) for seg in DirectoryScanner._SEP_SPLITTER.split(base)
        )

    @staticmethod
    def _find_filename_patterns(names: list[str], min_pattern_length: int = 4) -> tuple[bool, float]:
        """Analyze filenames to detect patterns indicating localization, versioning etc."""
        if len(names) < 5:
            return False, 0.0

        prefixes: dict[str, int] = {}
        suffixes: dict[str, int] = {}

        for name in names:
            base = Path(name).stem
            for i in range(1, len(base) + 1):
                if len(prefix := base[:i]) >= min_pattern_length:
                    prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if len(suffix := base[-i:]) >= min_pattern_length:
                    suffixes[suffix] = suffixes.get(suffix, 0) + 1

        best_prefix_count = max(prefixes.values()) if prefixes else 0
        best_suffix_count = max(suffixes.values()) if suffixes else 0
        pattern_ratio = max(best_prefix_count, best_suffix_count) / len(names)

        return (max(best_prefix_count, best_suffix_count) >= 5 and pattern_ratio >= 0.7), pattern_ratio

    @lru_cache(maxsize=1024)  # noqa: B019
    def scan_directory(self, dir_path: str) -> DirScanResult:  # noqa: C901
        """Scan a directory and decide if it should be auto-ignored or partially ignored."""
        if not self.auto_ignore:
            try:
                with os.scandir(dir_path) as it:
                    return DirScanResult(False, 0, 0, False, tuple(it))
            except Exception:
                return DirScanResult(False, 0, 0, False, ())

        try:
            with os.scandir(dir_path) as it:
                entries = tuple(it)

            if not entries:
                return DirScanResult(False, 0, 0, False, entries)

            dir_name = Path(dir_path).name
            total_count = len(entries)

            if total_count < 3:
                return DirScanResult(False, total_count, 0, False, entries)

            hash_count = normal_count = 0
            filenames: list[str] = []

            for entry in entries:
                name = entry.name
                if name.startswith("."):
                    total_count -= 1
                    continue
                filenames.append(name)
                if self.is_likely_hash_name(name):
                    hash_count += 1
                else:
                    normal_count += 1

            has_pattern, _ = self._find_filename_patterns(filenames)

            if normal_count >= 3 and hash_count >= 5:
                return DirScanResult(False, total_count, hash_count, True, entries)
            if has_pattern and total_count > 5:
                return DirScanResult(True, total_count, hash_count, False, entries)
            if total_count > 5 and (hash_count / total_count) > 0.8:
                return DirScanResult(True, total_count, hash_count, False, entries)
            if self.is_likely_hash_name(dir_name):
                return DirScanResult((hash_count / total_count > 0.7), total_count, hash_count, False, entries)

            return DirScanResult(False, total_count, hash_count, False, entries)
        except Exception:
            return DirScanResult(False, 0, 0, False, ())


@dataclass
class TreeConfig:
    base_dir: Path
    ignore_dirs: list[str] = field(default_factory=lambda: [])
    auto_ignore: bool = True
    include_file_contents: bool = False
    style_id: int = 2
    indent: int = 2
    display_progress: bool = True

    def __post_init__(self):
        self.base_dir = self.base_dir.resolve()
        self.indent_size = self.indent + 1


class TreeRenderer:
    """Orchestrates directory traversal and formats the tree output."""

    def __init__(self, config: TreeConfig):
        self.config = config
        self.style = TreeStyle(config.style_id, config.indent_size)
        self.scanner = DirectoryScanner(config.ignore_dirs, config.auto_ignore)
        self.stats = GenerationStats()
        self._progress_update_interval = 0.05
        self._last_progress_update = 0

    def generate(self) -> StyledText:
        """Generate the entire directory tree."""
        if self.config.display_progress:
            xx.console.info("starting tree generation...", start="\n")
        else:
            xx.console.info("generating tree...", start="\n")

        if not self.config.base_dir.is_dir():
            raise ValueError(f"Invalid base directory: {self.config.base_dir}")

        lines: list[str] = []
        self._render_tree(self.config.base_dir, "", 0, "", lines)
        result_str = "".join(lines)

        xx.console.log(
            "Photosynthesis Complete",
            StyledText(
                ("max depth ", S.BR.CYAN(str(self.stats.max_depth))),
                (S.DIM(" | "), S.BR.CYAN(f"{self.stats.processed_dirs:,}"), " dirs"),
                (S.DIM(" | "), S.BR.CYAN(f"{self.stats.processed_files:,}"), " files"),
            ),
            title_bg_color=S.BG.BR.GREEN,
            start="\033[F\033[K",
        )

        return StyledText(COLORS["line"], result_str)

    def _update_progress(self, current_dir: Path, is_dir: bool = True) -> None:
        """Update the generation progress display in terminal."""
        if is_dir:
            self.stats.processed_dirs += 1
        else:
            self.stats.processed_files += 1

        self.stats.current_depth = len(Path(current_dir).parts) - len(Path(self.config.base_dir).parts)
        self.stats.max_depth = max(self.stats.max_depth, self.stats.current_depth)

        if not self.config.display_progress:
            return

        current_time = time.time()
        if current_time - self._last_progress_update < self._progress_update_interval:
            return

        self._last_progress_update = current_time

        try:
            rel_path = str(Path(current_dir).relative_to(self.config.base_dir)).replace("\\", "/")
        except ValueError:
            rel_path = Path(current_dir).name

        formatted_dirs = f"{self.stats.processed_dirs:,}"
        formatted_files = f"{self.stats.processed_files:,}"

        status_len = len(
            f"depth {self.stats.current_depth}/{self.stats.max_depth} | {formatted_dirs} dirs | {formatted_files} files | "
        )
        max_rel_path_len = xx.console.get_width() - (18 + status_len)

        if len(rel_path) > max_rel_path_len:
            rel_path = "…" + rel_path[-max_rel_path_len:]

        xx.console.log(
            "Sprouting",
            StyledText(
                ("depth ", S.BR.CYAN(f"{self.stats.current_depth}/{self.stats.max_depth}")),
                (S.DIM(" | "), S.BR.CYAN(formatted_dirs), " dirs"),
                (S.DIM(" | "), S.BR.CYAN(formatted_files), " files"),
                (S.DIM(" | "), S.WHITE(rel_path)),
            ),
            title_bg_color=COLOR.BLUE,
            start="\033[F\033[K",
        )

    def _render_tree(self, dir_path: Path, prefix: str, level: int, parent_rel_path: str, lines: list[str]) -> None:
        """Recursively traverse and render the directory tree."""
        self._update_progress(dir_path)

        try:
            if level == 0:
                self._render_root(dir_path, lines)
                parent_rel_path = ""

            scan_result = self.scanner.scan_directory(str(dir_path))
            entries = tuple(sorted(scan_result.entries, key=lambda e: (not e.is_dir(), e.name.lower())))

            if not entries:
                return

            if scan_result.should_ignore:
                self._render_ignored_branch(prefix, is_last=True, lines=lines)
                return

            if scan_result.show_partial:
                self._render_partial_entries(entries, prefix, level, parent_rel_path, lines)
            else:
                self._render_all_entries(entries, prefix, level, parent_rel_path, lines)

        except Exception as exc:
            self._render_error(exc, prefix, lines)

    def _render_root(self, dir_path: Path, lines: list[str]) -> None:
        """Render the root directory at the top of the tree."""
        base_name = dir_path.name or dir_path.drive.rstrip(":\\")
        lines.append(f"{self.style.c_dir}{base_name}{self.style.c_reset}")
        lines.append(f"{self.style.c_line}{self.style.c_dir_dim}{self.style.dirname_end}{self.style.c_reset}")
        lines.append(f"{self.style.c_line}\n")

    def _render_all_entries(
        self, entries: tuple[os.DirEntry[str], ...], prefix: str, level: int, parent_rel_path: str, lines: list[str]
    ) -> None:
        """Render standard directory entries."""
        for idx, entry in enumerate(entries):
            is_dir = entry.is_dir()
            is_last = idx == len(entries) - 1
            branch = self.style.corners[0] if is_last else self.style.branch_new
            current_prefix = f"{prefix}{branch}{self.style.line_hor_str}"
            current_rel_path = str(Path(parent_rel_path) / entry.name)

            should_ignore_entry = self.scanner.should_ignore_path(current_rel_path)
            if is_dir and not should_ignore_entry:
                should_ignore_entry = self.scanner.scan_directory(entry.path).should_ignore

            if should_ignore_entry:
                self._render_ignored_entry(entry, prefix, is_last, is_dir, lines)
                continue

            if is_dir:
                self._render_directory(entry, prefix, current_prefix, level, is_last, current_rel_path, lines)
            else:
                self._render_file(entry, prefix, current_prefix, is_last, lines)

    def _render_partial_entries(
        self, entries: tuple[os.DirEntry[str], ...], prefix: str, level: int, parent_rel_path: str, lines: list[str]
    ) -> None:
        """Render entries with some hash names collapsed into an ignored marker."""
        visible_entries: list[os.DirEntry[str] | None] = []
        last_was_ignored = False

        for entry in entries:
            if not self.scanner.is_likely_hash_name(entry.name):
                if last_was_ignored:
                    visible_entries.append(None)
                visible_entries.append(entry)
                last_was_ignored = False
            else:
                last_was_ignored = True

        if visible_entries and visible_entries[-1] is None:
            visible_entries.pop()

        for idx, entry in enumerate(visible_entries):
            is_last = idx == len(visible_entries) - 1

            if entry is None:
                self._render_ignored_branch(prefix, is_last, lines)
                continue

            branch = self.style.corners[0] if is_last else self.style.branch_new
            current_prefix = f"{prefix}{branch}{self.style.line_hor_str}"

            if entry.is_dir():
                self._render_directory(
                    entry, prefix, current_prefix, level, is_last, str(Path(parent_rel_path) / entry.name), lines
                )
            else:
                self._render_file(entry, prefix, current_prefix, is_last, lines)

    def _render_directory(
        self,
        entry: os.DirEntry[str],
        prefix: str,
        current_prefix: str,
        level: int,
        is_last: bool,
        current_rel_path: str,
        lines: list[str],
    ) -> None:
        lines.append(f"{current_prefix}{self.style.c_dir}{entry.name}{self.style.c_reset}")
        lines.append(f"{self.style.c_line}{self.style.c_dir_dim}{self.style.dirname_end}{self.style.c_reset}")
        lines.append(f"{self.style.c_line}\n")

        new_prefix = prefix + (
            " " * self.style.indent_size if is_last else f"{self.style.line_ver}" + " " * (self.style.indent_size - 1)
        )
        self._render_tree(Path(entry.path), new_prefix, level + 1, current_rel_path, lines)

    def _render_file(self, entry: os.DirEntry[str], prefix: str, current_prefix: str, is_last: bool, lines: list[str]) -> None:
        self._update_progress(Path(entry.path), is_dir=False)
        color = self._get_file_color(entry)
        lines.append(f"{current_prefix}{color}{entry.name}{self.style.c_reset}{self.style.c_line}\n")

        if self.config.include_file_contents and self._is_text_file(entry.path):
            self._render_file_contents(entry.path, prefix, is_last, lines)

    def _render_ignored_entry(
        self, entry: os.DirEntry[str], prefix: str, is_last: bool, is_dir: bool, lines: list[str]
    ) -> None:
        branch = self.style.corners[0] if is_last else self.style.branch_new

        if is_last:
            lines.append(f"{prefix}{self.style.c_line_dim}{branch}")
        else:
            lines.append(f"{prefix}{branch}{self.style.c_line_dim}")

        lines.append(f"{self.style.line_hor_str}{entry.name}")

        if is_dir:
            lines.append(self.style.dirname_end)

        lines.append(f"{self.style.c_reset}{self.style.c_line}\n")

        if is_dir:
            ignored_prefix = f"{prefix}{self.style.tab}" if is_last else f"{prefix}{self.style.line_ver}{self.style.tab[:-1]}"
            self._render_ignored_branch(ignored_prefix, is_last=True, lines=lines)

    def _render_ignored_branch(self, prefix: str, is_last: bool, lines: list[str]) -> None:
        branch = self.style.corners[0] if is_last else self.style.branch_new
        lines.append(
            f"{prefix}{self.style.c_line_dim}{branch}{self.style.line_hor_str}{self.style.ignored}{self.style.c_reset}{self.style.c_line}\n"
        )

    def _render_file_contents(self, filepath: str, prefix: str, is_last: bool, lines: list[str]) -> None:
        content_prefix = prefix + (
            " " * self.style.indent_size if is_last else f"{self.style.line_ver}" + " " * (self.style.indent_size - 1)
        )
        try:
            with open(filepath, encoding="utf-8", errors="replace") as f:
                file_lines = f.readlines()

            if not file_lines:
                return

            file_lines = [
                line.replace("\t", "    ").translate(
                    {
                        0x2000: " ",
                        0x2001: " ",
                        0x2002: " ",
                        0x2003: " ",
                        0x2004: " ",
                        0x2005: " ",
                        0x2006: " ",
                        0x2007: " ",
                        0x2008: " ",
                        0x2009: " ",
                        0x200A: " ",
                    }
                )
                for line in file_lines
            ]
            content_width = max(len(line.rstrip()) for line in file_lines)
            hor_border = self.style.line_hor * (content_width + 2)

            lines.append(f"{content_prefix}{self.style.branch_new}{hor_border}{self.style.corners[2]}\n")

            for line in file_lines:
                stripped = line.rstrip()
                padding = " " * (content_width - len(stripped))
                lines.append(
                    f"{content_prefix}{self.style.line_ver} {self.style.c_content}{stripped}"
                    f"{self.style.c_reset}{self.style.c_line}{padding} {self.style.line_ver}\n"
                )

            lines.append(f"{content_prefix}{self.style.corners[0]}{hor_border}{self.style.corners[1]}\n")

        except Exception:
            lines.append(
                f"{content_prefix}{self.style.corners[0]}{self.style.line_hor}"
                f"{self.style.c_b_in}{self.style.c_error} {self.style.error} "
                f"Error reading file contents. {self.style.c_reset}\n{self.style.c_line}"
            )

    def _render_error(self, exc: Exception, prefix: str, lines: list[str]) -> None:
        error_prefix = prefix + self.style.corners[0] + (self.style.line_hor * (self.style.indent_size - 1))
        lines.append(
            f"{error_prefix}{self.style.c_b_in}{self.style.c_error} {self.style.error} "
            f"{exc!s} {self.style.c_reset}\n{self.style.c_line}"
        )

    def _get_file_color(self, entry: os.DirEntry[str]) -> str:  # noqa: C901
        """Determine the color string for a file based on its type and extension."""
        if entry.is_symlink():
            return self.style.c_symlink

        try:
            if os.access(entry.path, os.X_OK):
                return self.style.c_executable
        except Exception:
            pass

        ext = Path(entry.name).suffix.lower()
        if ext in EXEC_EXTS:
            return self.style.c_executable
        elif ext in IMAGE_EXTS:
            return self.style.c_image
        elif ext in ARCHIVE_EXTS:
            return self.style.c_archive
        elif ext in CODE_EXTS:
            return self.style.c_code
        elif ext in VIDEO_EXTS:
            return self.style.c_video
        elif ext in AUDIO_EXTS:
            return self.style.c_audio

        if entry.is_file():
            try:
                if entry.stat().st_size > 2:
                    with open(entry.path, "rb") as f:
                        if f.read(2) == b"#!":
                            return self.style.c_executable
            except Exception:
                pass

        return self.style.c_file

    @staticmethod
    @lru_cache(maxsize=1024)
    def _is_text_file(filepath: str) -> bool:
        if Path(filepath).suffix.lower() in BINARY_EXTENSIONS:
            return False

        try:
            with open(filepath, "rb") as f:
                chunk = f.read(1024)
                text_characters = bytes(range(32, 127)) + b"\n\r\t\f\b"
                return bool(chunk) and all(byte in text_characters for byte in chunk)
        except Exception:
            return False


def get_user_inputs(config: TreeConfig) -> None:
    """Prompt user for missing configuration if not using defaults."""
    if ARGS.ignore_dirs.exists:
        config.ignore_dirs = ARGS.ignore_dirs.values[0].split("|") if ARGS.ignore_dirs.values else []
    else:
        ignore_input = xx.console.input(
            StyledText(
                S.BOLD("Enter directory names/paths which's content should be ignored "),
                ("(", S.CYAN("|"), " separated)"),
                S.BOLD(" > "),
            ),
        )
        config.ignore_dirs = [d.strip() for d in ignore_input.split("|")]

    config.auto_ignore = (
        xx.console.input(
            StyledText(
                S.BOLD("Enable auto-ignore unimportant directories "),
                ("(Y)" if config.auto_ignore else "(N)"),
                S.BOLD(" > "),
            ),
            max_len=1,
            allowed_chars="yYnN",
            default_val="Y" if config.auto_ignore else "N",
        ).upper()
        == "Y"
    )

    config.include_file_contents = (
        xx.console.input(
            StyledText(
                S.BOLD("Display the file contents in the tree "),
                ("(Y)" if config.include_file_contents else "(N)"),
                S.BOLD(" > "),
            ),
            max_len=1,
            allowed_chars="yYnN",
            default_val="Y" if config.include_file_contents else "N",
        ).upper()
        == "Y"
    )

    StyledText(S.BOLD("Enter the tree style "), "(1-4)").print()
    TreeStyle.show_styles()
    config.style_id = xx.console.input(
        StyledText(f"({config.style_id})", S.BOLD(" > ")),
        max_len=1,
        allowed_chars="1234",
        default_val=config.style_id,
        output_type=int,
    )

    config.indent = xx.console.input(
        StyledText(S.BOLD("Enter the indent "), f"({config.indent})", S.BOLD(" > ")),
        max_len=2,
        allowed_chars="0123456789",
        default_val=config.indent,
        output_type=int,
    )


def main() -> None:
    if ARGS.help.exists:
        print_help()
        return

    base_dir = Path(v) if (v := ARGS.base_dir.get(0)) else Path.cwd()

    config = TreeConfig(
        base_dir=base_dir,
        ignore_dirs=DEFAULT["ignore_dirs"].copy(),
        auto_ignore=DEFAULT["auto_ignore"],
        include_file_contents=DEFAULT["include_file_contents"],
        style_id=DEFAULT["tree_style"],
        indent=DEFAULT["indent"],
        display_progress=(not ARGS.no_progress.exists),
    )

    into_file = DEFAULT["into_file"]

    if not ARGS.use_all_defaults.exists:
        get_user_inputs(config)

        into_file = (
            xx.console.input(
                StyledText(S.BOLD("Output tree into file "), ("(Y)" if into_file else "(N)"), S.BOLD(" > ")),
                max_len=1,
                allowed_chars="yYnN",
                default_val="Y" if into_file else "N",
            ).upper()
            == "Y"
        )

    # Re-initialize config in case user changed indent/style properties:
    config = TreeConfig(
        base_dir=config.base_dir,
        ignore_dirs=config.ignore_dirs,
        auto_ignore=config.auto_ignore,
        include_file_contents=config.include_file_contents,
        style_id=config.style_id,
        indent=config.indent,
        display_progress=config.display_progress,
    )

    renderer = TreeRenderer(config)
    result = renderer.generate()

    if into_file:
        file, cls_line = None, ""
        try:
            file = xx.file.create("tree.txt", result.raw)
        except FileExistsError:
            cls_line = "\033[F\033[K"
            if xx.console.confirm(StyledText("                 ", S.WHITE("tree.txt"), "already exists. Overwrite?"), end=""):
                file = xx.file.create("tree.txt", result.raw, force=True)
            else:
                xx.console.exit()

        if file:
            xx.console.done(
                StyledText((S.WHITE | S.link(file))(file.name), " successfully created."), start=cls_line, end="\n\n"
            )
        else:
            xx.console.fail(StyledText((S.BR.RED)("File is empty or failed to create file.")), start=cls_line, end="\n\n")
    else:
        print()
        result.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except PermissionError:
        xx.console.fail("Permission to create file was denied.", start="\n", end="\n\n")
    except Exception as exc:
        xx.console.fail(exc, start="\n", end="\n\n")
