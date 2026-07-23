#!/usr/bin/env python3
# [x-cmds]: UPDATE

"""A really advanced directory tree generator
with a lost of options and customization."""

from __future__ import annotations

import fnmatch
import os
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import ClassVar, NamedTuple, TypedDict
import xulbux as xx
from xulbux import S, StyledText
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


# fmt: off
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


class IgnoreDirectory(Exception):
    """Raised when a directory should be ignored."""

    ...


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

    # Least resource intensive patterns first, more complex patterns later:
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


class Tree:
    _NEWLINE = b"\n"
    _SPACE = b" "

    # fmt: off
    BINARY_EXTENSIONS: frozenset[str] = frozenset(
        {
            ".7z", ".avi", ".bin", ".cur", ".dat", ".db", ".dll", ".doc", ".docx", ".dylib",
            ".exe", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".mov", ".mp3", ".mp4", ".pdf",
            ".png", ".rar", ".so", ".sqlite", ".tar", ".xls", ".xlsx", ".zip"
        }
    )
    # fmt: on

    IGNORE_DIRS: ClassVar[list[str]] = [d.lower() for d in IGNORE.paths]

    def __init__(
        self,
        base_dir: Path,
        ignore_dirs: list[str] | None = None,
        auto_ignore: bool | None = True,
        include_file_contents: bool | None = False,
        style: int = 1,
        indent: int = 2,
        display_progress: bool | None = True,
    ) -> None:
        if ignore_dirs is None:
            ignore_dirs = []

        self.base_dir: Path = base_dir.resolve()
        self.ignore_dirs: list[str] = (ignore_dirs or []) + (self.IGNORE_DIRS if auto_ignore else [])
        self.auto_ignore: bool | None = auto_ignore
        self.include_file_contents: bool | None = include_file_contents
        self.style: int = style
        self.indent: int = indent
        self.display_progress: bool | None = display_progress
        self.ignore_set: frozenset[str] = frozenset()
        self.style_presets: dict[int, TreeStylePreset] = {
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

        self._reset_style_attrs()

        self.gen_stats = GenerationStats()

        self._progress_update_interval = 0.05  # Seconds between updates.
        self._last_progress_update = 0

    def generate(
        self,
        ignore_dirs: list[str] | None = None,
        auto_ignore: bool | None = None,
        include_file_contents: bool | None = None,
        style: int | None = None,
        indent: int | None = None,
        display_progress: bool | None = None,
    ) -> str:
        """Generate the directory tree as a string."""

        if ignore_dirs is None:
            ignore_dirs = []
        self.display_progress = self.display_progress if display_progress is None else display_progress
        if self.display_progress:
            xx.console.info("starting tree generation...", start="\n")
        else:
            xx.console.info("generating tree...", start="\n")

        self.gen_stats = GenerationStats()

        self.ignore_dirs += ignore_dirs
        if not auto_ignore:
            self.ignore_dirs = []

        self.auto_ignore = self.auto_ignore if auto_ignore is None else auto_ignore
        self.include_file_contents = include_file_contents or self.include_file_contents
        self.style = style if style is not None and style >= 1 else self.style
        self.indent = (indent if indent is not None and indent >= 0 else self.indent) + 1

        if not self.base_dir.is_dir():
            raise ValueError(f"Invalid base directory: {self.base_dir}")

        self.ignore_set = (
            frozenset()
            if len(
                norm_ignore_dirs := {
                    # Normalize paths and convert absolute paths to start with `/`:
                    (
                        d.lower().replace("\\", "/")
                        if not Path(d).is_absolute()
                        else "/" + d.lower().replace("\\", "/").lstrip("/")
                    )
                    for d in self.ignore_dirs
                }
            )
            == 0
            else frozenset(norm_ignore_dirs)
        )

        self._reset_style_attrs()
        result = self._gen_tree(self.base_dir)

        xx.console.done(
            StyledText(
                S.BOLD("Generating tree: "),
                ("max depth ", S.BR.CYAN(str(self.gen_stats.max_depth))),
                (S.DIM(" | "), S.BR.CYAN(f"{self.gen_stats.processed_dirs:,}"), " dirs"),
                (S.DIM(" | "), S.BR.CYAN(f"{self.gen_stats.processed_files:,}"), " files"),
            ),
            start="\033[F\033[K",
        )

        return result

    def _reset_style_attrs(self) -> None:
        """Reset style attributes based on the current style preset."""

        styles = self.style_presets.get(self.style, self.style_presets[1])

        self.line_ver = styles["line_ver"]
        self.line_hor = styles["line_hor"]
        self.branch_new = styles["branch_new"]
        self.corners = styles["corners"]
        self.error = styles["error"]
        self.ignored = styles["ignored"]
        self.dirname_end = styles["dirname_end"]

        self._tab = self._SPACE * self.indent
        self._line_ver_b = self.line_ver.encode()
        self._line_hor_b = self.line_hor.encode() * max(0, self.indent - (2 if self.indent > 2 else 1))
        self._branch_new_b = self.branch_new.encode()
        self._corners_b = tuple(c.encode() for c in self.corners)
        self._dirname_end_b = self.dirname_end.encode()
        self._ignored_suffix_b = f"{self.line_hor}{self.ignored}\n".encode()

    def show_styles(self) -> None:
        """Display available tree styles with their corresponding visual representation."""

        StyledText(
            *(
                (
                    (S.BOLD | S.ITALIC)(f" {style}"),
                    f"  {details['corners'][0]}{details['line_hor']}{details['ignored']}{details['dirname_end']}",
                )
                for style, details in self.style_presets.items()
            ),
            sep="\n",
        ).print()

    @staticmethod
    @lru_cache(maxsize=4096)
    def _encode_str(string: str) -> bytes:
        """Encode a string to bytes."""

        return string.encode()

    _HASH_NAME_CHARS: frozenset[str] = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_~@. \t{}+/=")
    _HEX_SEGMENT: re.Pattern[str] = re.compile(r"^[a-fA-F0-9]{8,}$")
    _UUID_ANYWHERE: re.Pattern[str] = re.compile(
        r"[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}"
    )
    _SEP_SPLITTER: re.Pattern[str] = re.compile(r"[-_~@\s]+")

    @staticmethod
    @lru_cache(maxsize=4096)
    def _is_likely_hash_name(name: str) -> bool:
        """Determine if a filename or directory name is likely
        a hash or unique identifier based on patterns."""

        if not Tree._HASH_NAME_CHARS.issuperset(name):
            return False
        if len(name) < 2:
            return bool(IGNORE.pattern.match(name))
        if Tree._UUID_ANYWHERE.search(name):
            return True

        base = name.rsplit(".", 1)[0] if "." in name else name
        return any(len(seg) >= 8 and Tree._HEX_SEGMENT.match(seg) for seg in Tree._SEP_SPLITTER.split(base))

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
    def _scan_directory(self, dir_path: Path) -> DirScanResult:
        """Cached directory scanning with analysis."""

        if not self.auto_ignore:
            with os.scandir(dir_path) as it:
                return DirScanResult(False, 0, 0, False, tuple(it))

        try:
            entries: tuple[os.DirEntry[str], ...] = ()
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
                if self._is_likely_hash_name(name):
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
            if self._is_likely_hash_name(dir_name):
                return DirScanResult((hash_count / total_count > 0.7), total_count, hash_count, False, entries)

            return DirScanResult(False, total_count, hash_count, False, entries)

        except Exception:
            return DirScanResult(False, 0, 0, False, ())

    def _should_ignore_path(self, path: str) -> bool:  # noqa: C901
        """Check if a path matches any ignore pattern (supports `*` wildcards and `[…]` character classes)."""

        if not path:
            return False

        path_lower = path.lower().replace("\\", "/")
        path_parts = None

        for pattern in self.ignore_set:
            has_wildcard = "*" in pattern or "[" in pattern

            if not has_wildcard:
                # Exact matching:
                if "/" in pattern:
                    if (pattern.startswith("/") and path_lower == pattern[1:]) or pattern in path_lower:
                        return True
                else:
                    # Single component exact match:
                    if path_parts is None:
                        path_parts = path_lower.split("/")
                    if pattern in path_parts:
                        return True
            else:
                # Wildcard matching:
                if "/" in pattern:
                    if pattern.startswith("/"):
                        if fnmatch.fnmatch(path_lower, pattern[1:]):
                            return True
                    else:
                        # Multi-component wildcard pattern; match at any depth:
                        if path_parts is None:
                            path_parts = path_lower.split("/")
                        pattern_parts = pattern.split("/")
                        plen = len(pattern_parts)
                        for i in range(len(path_parts) - plen + 1):
                            if all(fnmatch.fnmatch(path_parts[i + j], pattern_parts[j]) for j in range(plen)):
                                return True
                else:
                    # Single component wildcard; check each path component:
                    if path_parts is None:
                        path_parts = path_lower.split("/")
                    if any(fnmatch.fnmatch(part, pattern) for part in path_parts):
                        return True

        return False

    @staticmethod
    @lru_cache(maxsize=1024)
    def _is_text_file(filepath: str) -> bool:
        """Check if a file is likely a text file based on its extension and content."""

        if Path(filepath).suffix.lower() in Tree.BINARY_EXTENSIONS:
            return False

        try:
            with open(filepath, "rb") as f:
                chunk = f.read(1024)
                text_characters = bytes(range(32, 127)) + b"\n\r\t\f\b"

                return bool(chunk) and all(byte in text_characters for byte in chunk)

        except Exception:
            return False

    def _update_progress(self, current_dir: Path, is_dir: bool = True) -> None:
        """Update the generation progress display."""

        if is_dir:
            self.gen_stats.processed_dirs += 1
        else:
            self.gen_stats.processed_files += 1

        self.gen_stats.current_depth = len(Path(current_dir).parts) - len(Path(self.base_dir).parts)
        self.gen_stats.max_depth = max(self.gen_stats.max_depth, self.gen_stats.current_depth)

        if (
            not self.display_progress
            or (current_time := time.time()) - self._last_progress_update < self._progress_update_interval
        ):
            return

        self._last_progress_update = current_time

        try:
            rel_path = str(Path(current_dir).relative_to(self.base_dir)).replace("\\", "/")
        except ValueError:
            rel_path = Path(current_dir).name

        formatted_dirs, formatted_files = (
            format(self.gen_stats.processed_dirs, ","),
            format(self.gen_stats.processed_files, ","),
        )
        max_rel_path_len = xx.console.get_width() - (
            28
            + len(
                f"depth {self.gen_stats.current_depth}/{self.gen_stats.max_depth}"
                f" | {formatted_dirs} dirs | {formatted_files} files | "
            )
        )

        if len(rel_path) > max_rel_path_len:
            rel_path = "…" + rel_path[-max_rel_path_len:]

        xx.console.log(
            "GENERATING TREE",
            StyledText(
                ("depth ", S.BR.CYAN(f"{self.gen_stats.current_depth}/{self.gen_stats.max_depth}")),
                (S.DIM(" | "), S.BR.CYAN(formatted_dirs), " dirs"),
                (S.DIM(" | "), S.BR.CYAN(formatted_files), " files"),
                (S.DIM(" | "), S.WHITE(rel_path)),
            ),
            title_bg_color=COLOR.BLUE,
            start="\033[F\033[K",
        )

    def _gen_tree(self, _dir: Path, _prefix: str = "", _level: int = 0, _parent_path: str = "") -> str:  # noqa: C901
        """Generate tree for directory.\n
        --------------------------------------------------------------------
        *   `_dir` – Current directory path.
        *   `_prefix` – Line prefix for visual tree structure.
        *   `_level` – Current recursion depth.
        *   `_parent_path` – Relative path from base_dir to current dir."""

        self._update_progress(_dir)
        result: bytearray = bytearray()

        try:
            if _level == 0:
                dir_path = Path(_dir)
                base_name = dir_path.name or dir_path.drive.rstrip(":\\")
                result.extend(base_name.encode())
                result.extend(self._dirname_end_b)
                result.extend(self._NEWLINE)
                _parent_path = ""

            scan_result = self._scan_directory(str(_dir))
            # Display directories first and everything else after, both groups sorted alphabetically:
            entries = tuple(sorted(scan_result.entries, key=lambda e: (not e.is_dir(), e.name.lower())))

            if not entries:
                return bytes(result).decode() if result else ""

            prefix_bytes = self._encode_str(_prefix)

            if scan_result.should_ignore:
                result.extend(prefix_bytes)
                result.extend(self._corners_b[0])
                result.extend(self._ignored_suffix_b)
                return bytes(result).decode() if result else ""

            entries_count = len(entries)
            prefix_ver = prefix_bytes + self._line_ver_b + self._tab[:-1]
            prefix_tab = prefix_bytes + self._tab

            if scan_result.show_partial:
                visible_entries: list[os.DirEntry[str] | None] = []
                last_was_ignored = False

                for entry in entries:
                    if not self._is_likely_hash_name(entry.name):
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
                        result.extend(prefix_bytes)
                        result.extend(self._corners_b[0] if is_last else self._branch_new_b)
                        result.extend(self._ignored_suffix_b)
                        continue

                    branch = self._corners_b[0] if is_last else self._branch_new_b
                    current_prefix = prefix_bytes + branch + self._line_hor_b

                    if entry.is_dir():
                        result.extend(current_prefix)
                        result.extend(entry.name.encode())
                        result.extend(self._dirname_end_b)
                        result.extend(self._NEWLINE)
                        new_prefix = _prefix + (" " * self.indent if is_last else self.line_ver + " " * (self.indent - 1))
                        result.extend(self._gen_tree(Path(entry.path), new_prefix, _level + 1).encode())

                    else:
                        self._update_progress(Path(entry.path), is_dir=False)
                        result.extend(current_prefix)
                        result.extend(entry.name.encode())
                        result.extend(self._NEWLINE)

                        if self.include_file_contents and self._is_text_file(entry.path):
                            content_prefix = _prefix + (
                                " " * self.indent if is_last else self.line_ver + " " * (self.indent - 1)
                            )

                            try:
                                with open(entry.path, encoding="utf-8", errors="replace") as f:
                                    if lines := f.readlines():
                                        lines = [
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
                                            for line in lines
                                        ]
                                        content_width = max(len(line.rstrip()) for line in lines)
                                        hor_border = self.line_hor * (content_width + 2)
                                        result.extend(
                                            f"{content_prefix}{self.branch_new}{hor_border}{self.corners[2]}\n".encode()
                                        )

                                        for line in lines:
                                            stripped = line.rstrip()
                                            padding = " " * (content_width - len(stripped))
                                            result.extend(
                                                (
                                                    f"{content_prefix}{self.line_ver} {stripped}{padding} {self.line_ver}\n"
                                                ).encode()
                                            )

                                        result.extend(
                                            f"{content_prefix}{self.corners[0]}{hor_border}{self.corners[1]}\n".encode()
                                        )

                            except Exception:
                                result.extend(
                                    StyledText(
                                        (content_prefix, self.corners[0], self.line_hor),
                                        (S.BOLD | S.INVERSE | S.RED)(f" {self.error} Error reading file contents. "),
                                        ("\n", S.WHITE),
                                    ).ansi.encode()
                                )

            else:
                for idx, entry in enumerate(entries):
                    is_dir, is_last = entry.is_dir(), idx == entries_count - 1
                    branch = self._corners_b[0] if is_last else self._branch_new_b
                    current_prefix = prefix_bytes + branch + self._line_hor_b
                    current_rel_path = str(Path(_parent_path) / entry.name)

                    if self._should_ignore_path(current_rel_path) or (
                        is_dir and self._scan_directory(entry.path).should_ignore
                    ):
                        result.extend(current_prefix)
                        result.extend(entry.name.encode())

                        if is_dir:
                            result.extend(self._dirname_end_b)
                            result.extend(self._NEWLINE)
                            result.extend(prefix_tab if is_last else prefix_ver)
                            result.extend(self._corners_b[0])
                            result.extend(self._ignored_suffix_b)
                        else:
                            result.extend(self._NEWLINE)

                        continue

                    if is_dir:
                        result.extend(current_prefix)
                        result.extend(entry.name.encode())
                        result.extend(self._dirname_end_b)
                        result.extend(self._NEWLINE)
                        new_prefix = _prefix + (" " * self.indent if is_last else self.line_ver + " " * (self.indent - 1))
                        result.extend(self._gen_tree(Path(entry.path), new_prefix, _level + 1, current_rel_path).encode())

                    else:
                        self._update_progress(Path(entry.path), is_dir=False)
                        result.extend(current_prefix)
                        result.extend(entry.name.encode())
                        result.extend(self._NEWLINE)

                        if self.include_file_contents and self._is_text_file(entry.path):
                            content_prefix = _prefix + (
                                " " * self.indent if is_last else self.line_ver + " " * (self.indent - 1)
                            )

                            try:
                                with open(entry.path, encoding="utf-8", errors="replace") as f:
                                    if lines := f.readlines():
                                        lines = [
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
                                            for line in lines
                                        ]
                                        content_width = max(len(line.rstrip()) for line in lines)
                                        hor_border = self.line_hor * (content_width + 2)
                                        result.extend(
                                            f"{content_prefix}{self.branch_new}{hor_border}{self.corners[2]}\n".encode()
                                        )

                                        for line in lines:
                                            result.extend(
                                                (
                                                    f"{content_prefix}{self.line_ver} {(stripped := line.rstrip())}"
                                                    f"{' ' * (content_width - len(stripped))} {self.line_ver}\n"
                                                ).encode()
                                            )

                                        result.extend(
                                            f"{content_prefix}{self.corners[0]}{hor_border}{self.corners[1]}\n".encode()
                                        )

                            except Exception:
                                result.extend(
                                    StyledText(
                                        (content_prefix, self.corners[0], self.line_hor),
                                        (S.BOLD | S.INVERSE | S.RED)(f" {self.error} Error reading file contents. "),
                                        ("\n", S.WHITE),
                                    ).ansi.encode()
                                )

        except Exception as exc:
            error_prefix = _prefix + self.corners[0] + (self.line_hor * (self.indent - 1))
            result.extend(
                StyledText(
                    error_prefix,
                    (S.BOLD | S.INVERSE | S.RED)(f" {self.error} {exc!s} "),
                    ("\n", S.WHITE),
                ).ansi.encode()
            )

        return bytes(result).decode() if result else ""


def main() -> None:
    if ARGS.help.exists:
        print_help()
        return

    tree = Tree(Path(v) if (v := ARGS.base_dir.get(0)) else Path.cwd())

    ignore_dirs = DEFAULT["ignore_dirs"]
    auto_ignore = DEFAULT["auto_ignore"]
    include_file_contents = DEFAULT["include_file_contents"]
    style = DEFAULT["tree_style"]
    indent = DEFAULT["indent"]
    into_file = DEFAULT["into_file"]

    if not ARGS.use_all_defaults.exists:
        if ARGS.ignore_dirs.exists:
            ignore_dirs = ARGS.ignore_dirs.values[0].split("|") if ARGS.ignore_dirs.values else []
        else:
            ignore_dirs = xx.console.input(
                StyledText(
                    S.BOLD("Enter directory names/paths which's content should be ignored "),
                    ("(", S.CYAN("|"), " separated)"),
                    S.BOLD(" > "),
                ),
            ).split("|")
        ignore_dirs = [d.strip() for d in ignore_dirs]

        auto_ignore = (
            xx.console.input(
                StyledText(
                    S.BOLD("Enable auto-ignore unimportant directories "),
                    ("(Y)" if auto_ignore else "(N)"),
                    S.BOLD(" > "),
                ),
                max_len=1,
                allowed_chars="yYnN",
                default_val="Y" if auto_ignore else "N",
            ).upper()
            == "Y"
        )

        include_file_contents = (
            xx.console.input(
                StyledText(
                    S.BOLD("Display the file contents in the tree "),
                    ("(Y)" if include_file_contents else "(N)"),
                    S.BOLD(" > "),
                ),
                max_len=1,
                allowed_chars="yYnN",
                default_val="Y" if include_file_contents else "N",
            ).upper()
            == "Y"
        )

        StyledText(S.BOLD("Enter the tree style "), "(1-4)").print()
        tree.show_styles()
        style = xx.console.input(
            StyledText(f"({style})", S.BOLD(" > ")),
            max_len=1,
            allowed_chars="1234",
            default_val=style,
            output_type=int,
        )

        indent = xx.console.input(
            StyledText(S.BOLD("Enter the indent "), f"({indent})", S.BOLD(" > ")),
            max_len=2,
            allowed_chars="0123456789",
            default_val=indent,
            output_type=int,
        )

        into_file = (
            xx.console.input(
                StyledText(S.BOLD("Output tree into file "), ("(Y)" if into_file else "(N)"), S.BOLD(" > ")),
                max_len=1,
                allowed_chars="yYnN",
                default_val="Y" if into_file else "N",
            ).upper()
            == "Y"
        )

    result = tree.generate(
        ignore_dirs=ignore_dirs,
        auto_ignore=auto_ignore,
        include_file_contents=include_file_contents,
        style=style,
        indent=indent,
        display_progress=(not ARGS.no_progress.exists),
    )

    if into_file:
        file, cls_line = None, ""
        try:
            file = xx.file.create("tree.txt", result)
        except FileExistsError:
            cls_line = "\033[F\033[K"
            if xx.console.confirm(StyledText("                 ", S.WHITE("tree.txt"), "already exists. Overwrite?"), end=""):
                file = xx.file.create("tree.txt", result, force=True)
            else:
                xx.console.exit()
        if file:
            xx.console.done(
                StyledText((S.WHITE | S.link(file))(file.name), " successfully created."), start=cls_line, end="\n\n"
            )
        else:
            xx.console.fail(StyledText((S.BR.RED)("File is empty or failed to create file.")), start=cls_line, end="\n\n")
    else:
        StyledText("\n", S.WHITE(result)).print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except PermissionError:
        xx.console.fail("Permission to create file was denied.", start="\n", end="\n\n")
    except Exception as exc:
        xx.console.fail(exc, start="\n", end="\n\n")
