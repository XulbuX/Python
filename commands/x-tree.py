#!/usr/bin/env python3
# [x-cmds]: UPDATE

"""A really advanced directory tree generator
with a lot of options and customization."""

from __future__ import annotations

import fnmatch
import os
import re
import textwrap
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Literal, NamedTuple, TypedDict, cast
import xulbux as xx
from xulbux import S, StyledText, Throbber

if TYPE_CHECKING:
    from xulbux.ansi import AnyStyle

ARGS = xx.console.get_args(
    {
        "base_dir": "before",
        "ignore_dirs": {"-i", "--ignore"},
        "auto_ignore_mode": {"-a", "--auto-ignore"},
        "include_file_contents": {"-c", "--content"},
        "to_file": {"-f", "--file"},
        "interactive": {"-I", "--interactive"},
        "help": {"-h", "--help"},
    }
)

COLORS: TreeColorConfig = {
    "line": S.BR.BLACK,
    "line_dull": S.BR.BLACK,
    "error": S.BOLD | S.RED,
    "dir": S.BOLD | S.BR.WHITE,
    "dir_dull": S.BR.WHITE,
    "file": S.WHITE,
    "symlink": S.BR.BLUE,
    "executable": S.BR.GREEN,
    "archive": S.BR.RED,
    "image": S.BR.MAGENTA,
    "video": S.MAGENTA,
    "audio": S.BR.CYAN,
    "code": S.BR.YELLOW,
    "content": S.DIM | S.WHITE,
}

CHARS: TreeCharConfig = {
    "line_ver": "│",
    "line_hor": "─",
    "branch_new": "├",
    "corners": ("╰", "╯", "╮"),
    "error": "⚠",
    "ignored": "…",
    "dirname_end": "/",
}

DEFAULT: ScriptDefaults = {
    "ignore_dirs": [],
    "auto_ignore_mode": 2,
    "include_file_contents": False,
    "max_content_lines": 0,
    "indent": 2,
    "into_file": False,
}

# fmt: off
IMAGE_EXTS = frozenset({
    ".ai", ".bmp", ".cr2", ".eps", ".gif", ".heic", ".ico", ".indd", ".jpeg", ".jpg", ".nef", ".orf", ".png", ".psd", ".raw",
    ".sr2", ".svg", ".tif", ".tiff", ".webp", ".xcf"
})
ARCHIVE_EXTS = frozenset({
    ".7z", ".apk", ".bz2", ".cab", ".deb", ".dmg", ".gz", ".iso", ".jar", ".lz", ".lzma", ".rar", ".rpm", ".tar", ".tgz",
    ".xz", ".z", ".zip"
})
VIDEO_EXTS = frozenset({
    ".3g2", ".3gp", ".amv", ".asf", ".avi", ".flv", ".m2ts", ".m4v", ".mkv", ".mov", ".mp4", ".mts", ".ogv", ".rm", ".rmvb",
    ".ts", ".vob", ".webm", ".wmv"
})
AUDIO_EXTS = frozenset({
    ".aac", ".aiff", ".alac", ".amr", ".au", ".flac", ".m4a", ".mid", ".midi", ".mp3", ".ogg", ".opus", ".voc", ".wav", ".wma"
})
EXEC_EXTS = frozenset({
    ".appimage", ".bat", ".bin", ".cmd", ".com", ".exe", ".msi", ".run", ".sh"
})
CODE_EXTS = frozenset({
    ".asm", ".bash", ".bat", ".c", ".cfg", ".cmake", ".conf", ".cpp", ".cs", ".css", ".csv", ".dart", ".diff", ".dockerfile",
    ".ejs", ".env", ".erl", ".ex", ".exs", ".go", ".gql", ".graphql", ".h", ".hbs", ".hpp", ".hs", ".html", ".ini", ".ipynb",
    ".j2", ".jade", ".java", ".jinja", ".jl", ".js", ".json", ".jsx", ".kt", ".less", ".log", ".lua", ".m", ".make", ".md",
    ".patch", ".php", ".pl", ".pom", ".proto", ".ps1", ".pug", ".py", ".pyi", ".pyw", ".r", ".rb", ".rs", ".s", ".sass", ".sc",
    ".scala", ".scss", ".sh", ".sql", ".styl", ".svelte", ".swift", ".toml", ".ts", ".tsx", ".tsv", ".txt", ".vbs", ".vue",
    ".xml", ".yaml", ".yml", ".zsh"
})
BINARY_EXTS = frozenset({
    ".7z", ".ai", ".apk", ".avi", ".bak", ".bin", ".blend", ".cab", ".class", ".cur", ".dat", ".db", ".db3", ".dbf", ".dcm",
    ".dll", ".dmg", ".doc", ".docx", ".dylib", ".eps", ".exe", ".fbx", ".frm", ".gif", ".glb", ".gltf", ".gz", ".heic", ".ibd",
    ".ico", ".iges", ".img", ".iso", ".jar", ".jpeg", ".jpg", ".mha", ".mhd", ".mkv", ".mobi", ".mov", ".mp3", ".mp4", ".msi",
    ".myd", ".myi", ".ndf", ".nef", ".nhdr", ".nii", ".nrrd", ".o", ".obj", ".ods", ".odt", ".opt", ".orf", ".ova", ".ovf",
    ".pdf", ".ply", ".png", ".ppt", ".pptx", ".psd", ".pyc", ".pyd", ".qcow2", ".rar", ".raw", ".rpm", ".rtf", ".so",
    ".sqlite", ".sqlite3", ".sr2", ".step", ".stl", ".svg", ".tar", ".tif", ".tiff", ".vdi", ".vhdx", ".vmdk", ".vtp", ".vtu",
    ".webp", ".xls", ".xlsx", ".zip"
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
        ("  ", S.BR.BLUE("-i"), ", ", S.BR.BLUE("--ignore", S.DIM("="), "S"), "         Directories to ignore ", S.DIM("(directory paths/names, separated by ", S.BR.CYAN("|"), ")")),  # noqa: E501
        ("  ", S.BR.BLUE("-a"), ", ", S.BR.BLUE("--auto-ignore", S.DIM("="), "N"), "    Auto-ignore mode (0: OFF, 1: Hardcoded only, 2: Smart) ", S.DIM(f"(default: {DEFAULT['auto_ignore_mode']})")),  # noqa: E501
        ("  ", S.BR.BLUE("-c"), ", ", S.BR.BLUE("--content", S.DIM("="), "N"), "        Include file contents, optionally truncated to N lines"),  # noqa: E501
        ("  ", S.BR.BLUE("-f"), ", ", S.BR.BLUE("--file", S.DIM("="), "P"), "           Output tree to file P ", S.DIM("(default: ", S.WHITE("tree.txt"), " in ", S.WHITE("CWD"), " if ", S.BR.BLUE("P"), " is omitted)")),  # noqa: E501
        ("  ", S.BR.BLUE("-I"), ", ", S.BR.BLUE("--interactive"), "      Prompt for interactive tree settings"),
        "",
        S.BOLD("Examples:"),
        ("  ", S.BR.GREEN("x-tree "), S.BR.BLUE("-I"), "                                        ", S.DIM("# ", S.ITALIC("Prompt for interactive settings"))),  # noqa: E501
        ("  ", S.BR.GREEN("x-tree "), S.BR.BLUE("-i", S.DIM("="), '"/abs/to/dir1 | rel/to/dir2 | dir3"'), "    ", S.DIM("# ", S.ITALIC("Ignore specified directories"))),  # noqa: E501
        ("  ", S.BR.GREEN("x-tree "), S.BR.BLUE("--auto-ignore", S.DIM("="), "1"), "                           ", S.DIM("# ", S.ITALIC("Set auto-ignore mode to hardcoded only"))),  # noqa: E501
        ("  ", S.BR.GREEN("x-tree "), S.BR.BLUE("--content"), "                                 ", S.DIM("# ", S.ITALIC("Include full file contents"))),  # noqa: E501
        ("  ", S.BR.GREEN("x-tree "), S.BR.BLUE("--content", S.DIM("="), "10"), "                              ", S.DIM("# ", S.ITALIC("Include file contents, truncated to 10 lines"))),  # noqa: E501
        ("  ", S.BR.GREEN("x-tree "), S.BR.BLUE("-f", S.DIM("="), '"/path/to/dir_or_file"'), "                 ", S.DIM("# ", S.ITALIC("Output to specific file or directory"))),  # noqa: E501
        "",
        (S.BOLD("Prompts: "), S.DIM("(only when using the ", S.BR.BLUE("-I"), " or ", S.BR.BLUE("--interactive"), " flag)")),
        ("  ", (S.ITALIC | S.DIM)("1"), "  Directories to ignore"),
        ("  ", (S.ITALIC | S.DIM)("2"), "  Auto-ignore mode"),
        ("  ", (S.ITALIC | S.DIM)("3"), "  Include file contents in tree"),
        ("  ", (S.ITALIC | S.DIM)("4"), "  Indentation size"),
        ("  ", (S.ITALIC | S.DIM)("5"), "  Output tree to file"),
        "",
        sep="\n",
    ).print()
# fmt: on


class TreeColorConfig(TypedDict):
    line: AnyStyle
    line_dull: AnyStyle
    error: AnyStyle
    dir: AnyStyle
    dir_dull: AnyStyle
    file: AnyStyle
    symlink: AnyStyle
    executable: AnyStyle
    archive: AnyStyle
    image: AnyStyle
    video: AnyStyle
    audio: AnyStyle
    code: AnyStyle
    content: AnyStyle


class TreeCharConfig(TypedDict):
    line_ver: str
    line_hor: str
    branch_new: str
    corners: tuple[str, str, str]
    error: str
    ignored: str
    dirname_end: str


class ScriptDefaults(TypedDict):
    ignore_dirs: list[str]
    auto_ignore_mode: Literal[0, 1, 2]
    include_file_contents: bool
    max_content_lines: int
    indent: int
    into_file: bool


class DirScanResult(NamedTuple):
    should_ignore: bool
    total_count: int
    hash_count: int
    show_partial: bool
    entries: tuple[os.DirEntry[str], ...]
    sorted_entries: tuple[os.DirEntry[str], ...]


@dataclass
class GenerationStats:
    """Keeps track of statistics during the tree generation process."""

    processed_dirs: int = 0
    processed_files: int = 0
    current_depth: int = 0
    max_depth: int = 0
    start_time: float = field(default_factory=time.time)


class IGNORE:
    """Contains patterns and logic for determining which
    directories/files to auto-ignore during tree generation."""

    paths: ClassVar[set[str]] = {
        "__pycache__",
        "__pypackages__",
        "__tests__",
        "_locales",
        "_site",
        ".adobe",
        ".angular",
        ".archive-unpack",
        ".cache",
        ".codeium",
        ".coverage",
        ".ds_store",
        ".eslintcache",
        ".fleet",
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
        ".mypy_*",
        ".next",
        ".npm",
        ".nuxt",
        ".nvm",
        ".nx",
        ".output",
        ".pytest_*",
        ".ruff_*",
        ".scannerwork",
        ".sonar",
        ".styleLintCache",
        ".svn",
        ".terraform",
        ".tmp.*",
        ".tox",
        ".venv",
        ".vs",
        ".webpack",
        ".yarn",
        "*.map",
        "*.min.css",
        "*.min.js",
        "*.noindex",
        "*.temp",
        "*.tmp",
        "*[-_.@]cache",
        "*[-_.@]indexed",
        "*[-_.@]temp",
        "$recycle.bin",
        "adobe/common/ptx",
        "adobe/typeQuest",
        "aggregatedCache",
        "artifacts",
        "autofillStates",
        "backstageInAppNavCache",
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
        "debugbar",
        "dim-1/mw$default",
        "dim1/mw$default",
        "dist-newstyle",
        "dist",
        "docs/_build",
        "gpuCache",
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
        "packages",
        "patch64",
        "program64",
        "pythonLocator",
        "recent/automaticDestinations",
        "recent/customDestinations",
        "reports",
        "rsa",
        "scriptCache",
        "session storage",
        "shaderCache",
        "slCache",
        "spotify/data",
        "spotify/users",
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

    # All patterns sorted from least to most resource-intensive for efficiency:
    reoccurring: ClassVar[dict[str, str]] = {
        "delimited_number": r"[-_][0-9]{1,2}",
        "num5-rand12": r"[0-9]{5}-[a-zA-Z0-9]{12}",
        "min_hex32": r"\.min_[a-fA-F0-9]{32}",
        "lower32_num1,2.hex64": r"[a-z]{32}_[0-9]{1,2}\.[a-fA-F0-9]{64}",
        "id3hex4": rf"\w{{3}}[a-fA-F0-9]{{4}}(?:{sep}|{ext})",
        "e_rand32": rf"e_[a-zA-Z0-9]{{32}}(?:{sep}|{ext})",
        "date": date,
        "version.date": r"(?:[0-9]\.){3}" + date,
        "delimited_date": r"(?:[0-9]{2}|[0-9]{4})[-.](?:[0-9]{2}|[0-9]{4})[-.](?:[0-9]{2}|[0-9]{4})",
        "base64": r"[+/0-9A-Za-z]{8,}={1,2}",
        "hex": r"(?:[a-fA-F0-9]{7,8}|[a-fA-F0-9]{16}[a-fA-F0-9]{20}|[a-fA-F0-9]{32}|[a-fA-F0-9]{38}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64})",  # noqa: E501
        "uuid": rf"\{{?[a-zA-Z0-9]{{8}}-[a-zA-Z0-9]{{4}}-[a-zA-Z0-9]{{4}}-[a-zA-Z0-9]{{4}}-[a-zA-Z0-9]{{12}}\}}?(?:[-_a-zA-Z0-9]+(?:{sep}|{ext}))?",  # noqa: E501
        "sid": r"S-[0-9]+-[0-9]+(?:-[0-9]+){2,}",
        "domain": r"[-a-z]+(?:\.[-a-z]+){2,}",
        "rand_short": rf"(?![A-Z][a-z]{{4,}})(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9]))[a-zA-Z0-9]{{4,12}}(?:{sep}|{ext})",
        "rand_long": rf"(?![A-Z][a-z]{{4,}})(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9]))[a-zA-Z0-9]{{13,64}}(?:{sep}|{ext})",
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


class TreeChars:
    """Manages the visual styling and ANSI codes for the tree."""

    def __init__(self, indent_size: int):
        """Initialize tree styling options and compile required ANSI characters."""

        preset = CHARS
        self.line_ver = preset["line_ver"]
        self.line_hor = preset["line_hor"]
        self.branch_new = preset["branch_new"]
        self.corners = preset["corners"]
        self.error = preset["error"]
        self.ignored = preset["ignored"]
        self.dirname_end = preset["dirname_end"]

        self.indent_size = indent_size
        self.tab = " " * indent_size
        self.line_hor_str = f"{self.line_hor} "
        # Pre-computed indent strings used in the hot render path:
        self.indent_last = " " * indent_size
        self.indent_cont = f"{self.line_ver}{' ' * (indent_size - 1)}"

        # Colors as ANSI strings:
        self.c_dim = StyledText(S.DIM).ansi
        self.c_bold = StyledText(S.BOLD).ansi
        self.c_bold_in = StyledText(S.BOLD | S.INVERSE).ansi
        self.c_italic = StyledText(S.ITALIC).ansi
        self.c_reset = StyledText(S.RESET).ansi

        self.c_line = StyledText(self.c_reset, COLORS["line"]).ansi
        self.c_line_dull = StyledText(self.c_reset, COLORS["line_dull"]).ansi
        self.c_error = StyledText(self.c_reset, COLORS["error"]).ansi
        self.c_dir = StyledText(self.c_reset, COLORS["dir"]).ansi
        self.c_dir_dull = StyledText(self.c_reset, COLORS["dir_dull"]).ansi
        self.c_file = StyledText(self.c_reset, COLORS["file"]).ansi
        self.c_file_dim = StyledText(self.c_reset, S.DIM, COLORS["file"]).ansi
        self.c_symlink = StyledText(self.c_reset, COLORS["symlink"]).ansi
        self.c_symlink_dim = StyledText(self.c_reset, S.DIM, COLORS["symlink"]).ansi
        self.c_executable = StyledText(self.c_reset, COLORS["executable"]).ansi
        self.c_executable_dim = StyledText(self.c_reset, S.DIM, COLORS["executable"]).ansi
        self.c_archive = StyledText(self.c_reset, COLORS["archive"]).ansi
        self.c_archive_dim = StyledText(self.c_reset, S.DIM, COLORS["archive"]).ansi
        self.c_image = StyledText(self.c_reset, COLORS["image"]).ansi
        self.c_image_dim = StyledText(self.c_reset, S.DIM, COLORS["image"]).ansi
        self.c_video = StyledText(self.c_reset, COLORS["video"]).ansi
        self.c_video_dim = StyledText(self.c_reset, S.DIM, COLORS["video"]).ansi
        self.c_audio = StyledText(self.c_reset, COLORS["audio"]).ansi
        self.c_audio_dim = StyledText(self.c_reset, S.DIM, COLORS["audio"]).ansi
        self.c_code = StyledText(self.c_reset, COLORS["code"]).ansi
        self.c_code_dim = StyledText(self.c_reset, S.DIM, COLORS["code"]).ansi
        self.c_content = StyledText(self.c_reset, COLORS["content"]).ansi


class DirectoryScanner:
    """Handles scanning directories and applying ignore rules."""

    _HEX_SEGMENT = re.compile(r"^[a-fA-F0-9]{8,}$")
    _UUID_ANYWHERE = re.compile(r"[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}")
    _SEP_SPLITTER = re.compile(r"[-_~@\s]+")

    _TEXT_TRANS = str.maketrans(
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

    def __init__(self, ignore_dirs: list[str], auto_ignore_mode: Literal[0, 1, 2]):
        """Initialize the directory scanner with ignore sets and rules."""

        self.auto_ignore_mode = auto_ignore_mode

        all_ignores = ignore_dirs.copy()
        if auto_ignore_mode > 0:
            all_ignores.extend(path.lower() for path in IGNORE.paths)

        self.exact_names: set[str] = set()
        self.exact_paths: set[str] = set()
        self.wildcard_names: list[re.Pattern[str]] = []
        self.wildcard_paths: list[list[re.Pattern[str]]] = []
        self.wildcard_abs_paths: list[re.Pattern[str]] = []
        self._scan_cache: dict[str, DirScanResult] = {}
        self._ignore_cache: dict[str, bool] = {}

        for pattern in all_ignores:
            p = pattern.lower().replace("\\", "/")
            if Path(p).is_absolute():
                p = f"/{p.lstrip('/')}"

            if "*" not in p and "[" not in p:
                if "/" in p:
                    self.exact_paths.add(p)
                else:
                    self.exact_names.add(p)
            else:
                if "/" in p:
                    if p.startswith("/"):
                        self.wildcard_abs_paths.append(re.compile(fnmatch.translate(p[1:])))
                    else:
                        parts = [re.compile(fnmatch.translate(part)) for part in p.split("/")]
                        self.wildcard_paths.append(parts)
                else:
                    self.wildcard_names.append(re.compile(fnmatch.translate(p)))

    def should_ignore_path(self, path: str) -> bool:  # noqa: C901
        """Check if a relative path matches any user-specified or default ignore pattern."""

        if not path:
            return False

        cached = self._ignore_cache.get(path)
        if cached is not None:
            return cached

        path_lower = path.lower().replace("\\", "/")
        name = path_lower.rsplit("/", 1)[-1]

        if name in self.exact_names:
            self._ignore_cache[path] = True
            return True

        if self.exact_paths:
            for ep in self.exact_paths:
                if (ep.startswith("/") and path_lower == ep[1:]) or ep in path_lower:
                    self._ignore_cache[path] = True
                    return True

        if self.wildcard_names:
            for w_name in self.wildcard_names:
                if w_name.match(name):
                    self._ignore_cache[path] = True
                    return True

        if self.wildcard_abs_paths:
            for w_name in self.wildcard_abs_paths:
                if w_name.match(path_lower):
                    self._ignore_cache[path] = True
                    return True

        if self.wildcard_paths:
            path_parts = path_lower.split("/")
            for pattern_parts in self.wildcard_paths:
                plen = len(pattern_parts)
                for i in range(len(path_parts) - plen + 1):
                    if all(pattern_parts[j].match(path_parts[i + j]) for j in range(plen)):
                        self._ignore_cache[path] = True
                        return True

        self._ignore_cache[path] = False
        return False

    @staticmethod
    @lru_cache(maxsize=4096)
    def is_likely_hash_name(name: str) -> bool:
        """Determine if a filename or directory name is likely a hash or unique identifier."""

        if name.strip("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_~@. \t{}+/=") or len(name) < 2:
            return False
        elif bool(IGNORE.pattern.match(name)):
            return True

        base = name.rsplit(".", 1)[0] if "." in name else name
        # Cheap hex-segment check first; UUID regex (more expensive) only as fallback
        if any(
            len(seg) >= 8 and DirectoryScanner._HEX_SEGMENT.match(seg) for seg in DirectoryScanner._SEP_SPLITTER.split(base)
        ):
            return True

        return bool(DirectoryScanner._UUID_ANYWHERE.search(name))

    @staticmethod
    def _find_filename_patterns(names: list[str], min_pattern_length: int = 4) -> tuple[bool, float]:
        """Analyze filenames to detect patterns indicating localization, versioning etc."""

        if len(names) < 5:
            return False, 0.0

        # A longer prefix always has a count <= its shorter sub-prefix, so the
        # maximum match count is always found at exactly `min_pattern_length` chars.
        prefixes: dict[str, int] = {}
        suffixes: dict[str, int] = {}

        for name in names:
            dot = name.rfind(".")
            base = name[:dot] if dot > 0 else name

            if len(base) >= min_pattern_length:
                prefix = base[:min_pattern_length]
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                suffix = base[-min_pattern_length:]
                suffixes[suffix] = suffixes.get(suffix, 0) + 1

        best_prefix_count = max(prefixes.values()) if prefixes else 0
        best_suffix_count = max(suffixes.values()) if suffixes else 0
        best = max(best_prefix_count, best_suffix_count)
        pattern_ratio = best / len(names)

        return (best >= 5 and pattern_ratio >= 0.7), pattern_ratio

    def scan_directory(self, dir_path: str) -> DirScanResult:  # noqa: C901
        """Scan a directory and decide if it should be auto-ignored or partially ignored."""

        cached = self._scan_cache.get(dir_path)
        if cached is not None:
            return cached

        if self.auto_ignore_mode != 2:
            try:
                with os.scandir(dir_path) as it:
                    raw = tuple(it)
                sorted_raw = tuple(sorted(raw, key=lambda e: (not e.is_dir(), e.name.lower())))
                result = DirScanResult(False, 0, 0, False, raw, sorted_raw)
            except Exception:
                result = DirScanResult(False, 0, 0, False, (), ())
            self._scan_cache[dir_path] = result
            return result

        try:
            with os.scandir(dir_path) as it:
                entries = tuple(it)

            if not entries:
                result = DirScanResult(False, 0, 0, False, entries, entries)
                self._scan_cache[dir_path] = result
                return result

            # Pre-sort once here (parallel pre-scan phase) so render never needs to sort:
            sorted_entries = tuple(sorted(entries, key=lambda e: (not e.is_dir(), e.name.lower())))

            slash = dir_path.rfind("/")
            bslash = dir_path.rfind("\\")
            sep_pos = max(slash, bslash)
            dir_name = dir_path[sep_pos + 1 :] if sep_pos >= 0 else dir_path
            total_count = len(entries)

            if total_count < 3:
                return DirScanResult(False, total_count, 0, False, entries, sorted_entries)

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
                result = DirScanResult(False, total_count, hash_count, True, entries, sorted_entries)
            elif (has_pattern and total_count > 5) or (total_count > 5 and (hash_count / total_count) > 0.8):
                result = DirScanResult(True, total_count, hash_count, False, entries, sorted_entries)
            elif self.is_likely_hash_name(dir_name):
                result = DirScanResult(
                    (hash_count / total_count > 0.7), total_count, hash_count, False, entries, sorted_entries
                )
            else:
                result = DirScanResult(False, total_count, hash_count, False, entries, sorted_entries)

            self._scan_cache[dir_path] = result
            return result

        except Exception:
            result = DirScanResult(False, 0, 0, False, (), ())
            self._scan_cache[dir_path] = result
            return result


@dataclass
class TreeConfig:
    base_dir: Path
    max_width: int = 0
    ignore_dirs: list[str] = field(default_factory=lambda: [])
    auto_ignore_mode: Literal[0, 1, 2] = 2
    include_file_contents: bool = False
    max_content_lines: int = 0
    indent: int = 2

    def __post_init__(self):
        """Resolve base directory and set derived properties."""

        self.base_dir = self.base_dir.resolve()
        self.indent_size = self.indent + 1


class TreeRenderer:
    """Orchestrates directory traversal and formats the tree output."""

    def __init__(self, config: TreeConfig):
        """Initialize the renderer with config, styling, and scanner."""

        self.config = config
        self.chars = TreeChars(config.indent_size)
        self.scanner = DirectoryScanner(config.ignore_dirs, config.auto_ignore_mode)
        self.stats = GenerationStats()
        self._progress_update_interval = 0.05
        self._last_progress_update: float = 0.0
        self._progress_item_count: int = 0
        self._console_width: int = xx.console.get_width()

    def _pre_scan_parallel(self, root_dir: str) -> None:  # noqa: C901
        """Pre-populate the scan and ignore caches by scanning all subdirectories in
        parallel before the single-threaded rendering pass. I/O calls release the GIL,
        so a thread pool gives a large real-world speedup on any modern SSD."""
        lock = threading.Lock()
        done = threading.Event()
        max_workers = min(64, (os.cpu_count() or 4) * 8)
        active = [1]  # Number of in-flight tasks; pre-counted before each submit.
        canceled = [False]

        def _scan(abs_path: str, rel_path: str) -> None:
            if canceled[0]:
                with lock:
                    active[0] -= 1
                    if active[0] == 0:
                        done.set()
                return

            try:
                result = self.scanner.scan_directory(abs_path)

                if not result.should_ignore and not canceled[0]:
                    new_items: list[tuple[str, str]] = []

                    for entry in result.entries:
                        if entry.is_dir():
                            entry_rel = f"{rel_path}/{entry.name}" if rel_path else entry.name
                            if not self.scanner.should_ignore_path(entry_rel):
                                new_items.append((entry.path, entry_rel))

                    if new_items and not canceled[0]:
                        with lock:
                            active[0] += len(new_items)
                        for item in new_items:
                            executor.submit(_scan, *item)

            finally:
                with lock:
                    active[0] -= 1
                    if active[0] == 0:
                        done.set()

        executor = ThreadPoolExecutor(max_workers=max_workers)
        try:
            executor.submit(_scan, root_dir, "")
            while not done.wait(0.1):
                pass
        except KeyboardInterrupt:
            canceled[0] = True
            executor.shutdown(wait=False)
            raise
        finally:
            executor.shutdown(wait=False)

    def generate(self) -> StyledText:
        """Generate the entire directory tree."""

        if not self.config.base_dir.is_dir():
            raise ValueError(f"Invalid base directory: {self.config.base_dir}")

        with Throbber(
            label=StyledText(S.WHITE("Rooting tree from "), S.CYAN(str(self.config.base_dir))),
            format=[("  ", S.BR.BLUE("{a}")), "{l}"],
            frames=("⊶", "⊷"),
            sep="  ",
        ).context():
            self._pre_scan_parallel(str(self.config.base_dir))

        print()

        lines: list[str] = []
        self._render_tree(str(self.config.base_dir), "", 0, "", lines)
        result_str = "".join(lines)

        print("\x1b[F\x1b[K", end="")  # Clear the last progress output.

        time_taken = StyledText("took ", S.BR.CYAN(self._format_time(time.time() - self.stats.start_time)))
        tree_stats = StyledText(
            ("max depth ", S.BR.CYAN(str(self.stats.max_depth))),
            (S.DIM(" | "), S.BR.CYAN(f"{self.stats.processed_dirs:,}"), " dirs"),
            (S.DIM(" | "), S.BR.CYAN(f"{self.stats.processed_files:,}"), " files"),
        )

        if self.config.max_width > 0:
            max_width = self.config.max_width
        else:
            max_width = max(
                max((len(re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", line)) for line in result_str.split("\n")), default=80) + 1,
                len(time_taken.raw) + len(tree_stats.raw) + 2,
            )

        return StyledText(
            (COLORS["line"], result_str),
            "\n",
            (S.RESET, S.DIM("─" * max_width), "\n"),
            (" ", time_taken.ansi, " " * max(2, max_width - len(time_taken.raw) - len(tree_stats.raw) - 2), tree_stats.ansi),
            "\n",
        )

    @staticmethod
    def _format_time(elapsed: float) -> str:
        m, s = divmod(int(elapsed), 60)
        h, m = divmod(m, 60)
        ms = int((elapsed % 1) * 1000)

        parts: list[str] = []
        if h > 0:
            parts.append(f"{h}h")
        if m > 0:
            parts.append(f"{m}m")
        if s > 0:
            parts.append(f"{s}s")
        if ms > 0:
            parts.append(f"{ms}ms")

        return "".join(parts) if parts else "0ms"

    def _update_progress(self, current_name: str, level: int, is_dir: bool = True) -> None:
        """Update the generation progress display in terminal."""

        if is_dir:
            self.stats.processed_dirs += 1
        else:
            self.stats.processed_files += 1
            # Only check wall-clock time every 64 files to avoid sys-call overhead:
            self._progress_item_count += 1
            if self._progress_item_count & 63:
                return  # Fast path: skip ALL remaining work for most file calls.

        if level > self.stats.max_depth:
            self.stats.max_depth = level

        if (current_time := time.time()) - self._last_progress_update < self._progress_update_interval:
            return

        self._last_progress_update = current_time

        max_rel_path_len = max(10, self._console_width - 22)

        rel_path = current_name if len(current_name) <= max_rel_path_len else f".{current_name[-max_rel_path_len:]}"
        rel_path = rel_path or " "

        if is_dir:
            xx.console.log("Sprouting", f"{self.chars.c_dir}{rel_path}", title_bg_color=S.BG.BR.BLUE, start="\x1b[F\x1b[K")
        else:
            xx.console.log("Sprouting", f"{self.chars.c_file}{rel_path}", title_bg_color=S.BG.BR.BLUE, start="\x1b[F\x1b[K")

    def _render_tree(self, dir_path: str, prefix: str, level: int, parent_rel_path: str, lines: list[str]) -> None:
        """Recursively traverse and render the directory tree."""

        slash = dir_path.rfind("/")
        bslash = dir_path.rfind("\\")
        sep_pos = max(slash, bslash)
        dir_name = dir_path[sep_pos + 1 :] if sep_pos >= 0 else dir_path
        self._update_progress(dir_name or dir_path, level)

        try:
            if level == 0:
                self._render_root(dir_path, lines)
                parent_rel_path = ""

            scan_result = self.scanner.scan_directory(dir_path)

            if not (entries := scan_result.sorted_entries):
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

    def _render_root(self, dir_path: str, lines: list[str]) -> None:
        """Render the root directory at the top of the tree."""

        path = Path(dir_path)
        base_name = path.name or path.drive.rstrip(":\\")
        lines.append(
            f"{self.chars.c_dir}{base_name}{self.chars.c_reset}"
            f"{self.chars.c_line}{self.chars.c_dir_dull}{self.chars.dirname_end}{self.chars.c_reset}"
            f"{self.chars.c_line}\n"
        )

    def _render_all_entries(
        self, entries: tuple[os.DirEntry[str], ...], prefix: str, level: int, parent_rel_path: str, lines: list[str]
    ) -> None:
        """Render standard directory entries."""

        last_idx = len(entries) - 1
        for idx, entry in enumerate(entries):
            is_dir = entry.is_dir()
            is_last = idx == last_idx
            branch = self.chars.corners[0] if is_last else self.chars.branch_new
            current_prefix = f"{prefix}{branch}{self.chars.line_hor_str}"
            current_rel_path = f"{parent_rel_path}/{entry.name}" if parent_rel_path else entry.name

            should_ignore_entry = self.scanner.should_ignore_path(current_rel_path)
            if is_dir and not should_ignore_entry:
                should_ignore_entry = self.scanner.scan_directory(entry.path).should_ignore

            if should_ignore_entry:
                self._render_ignored_entry(entry, prefix, is_last, is_dir, lines)
                continue

            if is_dir:
                self._render_directory(entry, prefix, current_prefix, level, is_last, current_rel_path, lines)
            else:
                self._render_file(entry, prefix, current_prefix, level, is_last, lines)

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

        for i, entry in enumerate(visible_entries):
            is_last = bool(i == len(visible_entries) - 1)

            if entry is None:
                self._render_ignored_branch(prefix, is_last, lines)
                continue

            branch = self.chars.corners[0] if is_last else self.chars.branch_new
            current_prefix = f"{prefix}{branch}{self.chars.line_hor_str}"

            if entry.is_dir():
                self._render_directory(
                    entry,
                    prefix,
                    current_prefix,
                    level,
                    is_last,
                    f"{parent_rel_path}/{entry.name}" if parent_rel_path else entry.name,
                    lines,
                )
            else:
                self._render_file(entry, prefix, current_prefix, level, is_last, lines)

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
        """Render a single directory node and recursively process its children."""

        max_name_width = (
            max(10, self.config.max_width - len(current_prefix) - len(self.chars.dirname_end))
            if self.config.max_width > 0
            else 0
        )

        if self.config.max_width <= 0 or len(entry.name) <= max_name_width:
            lines.append(
                f"{current_prefix}{self.chars.c_dir}{entry.name}{self.chars.c_reset}"
                f"{self.chars.c_line}{self.chars.c_dir_dull}{self.chars.dirname_end}{self.chars.c_reset}"
                f"{self.chars.c_line}\n"
            )

        else:
            chunk = textwrap.wrap(entry.name, width=max_name_width, break_long_words=True, drop_whitespace=True)
            lines.append(f"{current_prefix}{self.chars.c_dir}{chunk[0]}{self.chars.c_reset}\n")

            branch = self.chars.corners[0] if is_last else self.chars.branch_new
            if is_last:
                wrap_indent = " " * (len(branch) + len(self.chars.line_hor_str))
            else:
                indent_len = len(branch) + len(self.chars.line_hor_str) - len(self.chars.line_ver)
                wrap_indent = f"{self.chars.line_ver}{' ' * indent_len}"
            wrap_prefix = f"{prefix}{wrap_indent}"

            for part in chunk[1:-1]:
                lines.append(f"{wrap_prefix}{self.chars.c_dir}{part}{self.chars.c_reset}\n")

            lines.append(
                f"{wrap_prefix}{self.chars.c_dir}{chunk[-1]}{self.chars.c_reset}"
                f"{self.chars.c_line}{self.chars.c_dir_dull}{self.chars.dirname_end}{self.chars.c_reset}"
                f"{self.chars.c_line}\n"
            )

        new_prefix = f"{prefix}{self.chars.indent_last if is_last else self.chars.indent_cont}"
        self._render_tree(entry.path, new_prefix, level + 1, current_rel_path, lines)

    def _render_file(
        self, entry: os.DirEntry[str], prefix: str, current_prefix: str, level: int, is_last: bool, lines: list[str]
    ) -> None:
        """Render a file node and optionally its contents if configured."""

        self._update_progress(entry.name, level, is_dir=False)
        color, color_dim = self._get_file_color(entry)

        max_name_width = max(10, self.config.max_width - len(current_prefix)) if self.config.max_width > 0 else 0

        if self.config.max_width <= 0 or len(entry.name) <= max_name_width:
            lines.append(f"{current_prefix}{color}{entry.name}{self.chars.c_reset}{self.chars.c_line}\n")

        else:
            chunk = textwrap.wrap(entry.name, width=max_name_width, break_long_words=True, drop_whitespace=True)
            lines.append(f"{current_prefix}{color}{chunk[0]}{self.chars.c_reset}{self.chars.c_line}\n")

            branch = self.chars.corners[0] if is_last else self.chars.branch_new
            if is_last:
                wrap_indent = " " * (len(branch) + len(self.chars.line_hor_str))
            else:
                indent_len = len(branch) + len(self.chars.line_hor_str) - len(self.chars.line_ver)
                wrap_indent = f"{self.chars.line_ver}{' ' * indent_len}"
            wrap_prefix = f"{prefix}{wrap_indent}"

            for part in chunk[1:]:
                lines.append(f"{wrap_prefix}{color}{part}{self.chars.c_reset}{self.chars.c_line}\n")

        if self.config.include_file_contents and self._is_text_file(entry.path):
            self._render_file_contents(entry.path, prefix, is_last, color_dim, lines)

    def _render_ignored_entry(
        self, entry: os.DirEntry[str], prefix: str, is_last: bool, is_dir: bool, lines: list[str]
    ) -> None:
        """Render a specifically ignored node with dimmed styling."""

        branch = self.chars.corners[0] if is_last else self.chars.branch_new
        suffix = self.chars.dirname_end if is_dir else ""

        if is_last:
            lines.append(
                f"{prefix}{self.chars.c_line_dull}{branch}{self.chars.line_hor_str}{entry.name}{suffix}{self.chars.c_reset}{self.chars.c_line}\n"
            )
        else:
            lines.append(
                f"{prefix}{branch}{self.chars.c_line_dull}{self.chars.line_hor_str}{entry.name}{suffix}{self.chars.c_reset}{self.chars.c_line}\n"
            )

        if is_dir:
            ignored_prefix = f"{prefix}{self.chars.indent_last if is_last else self.chars.indent_cont}"
            self._render_ignored_branch(ignored_prefix, is_last=True, lines=lines)

    def _render_ignored_branch(self, prefix: str, is_last: bool, lines: list[str]) -> None:
        """Render a branch indicating collapsed or ignored files."""

        branch = self.chars.corners[0] if is_last else self.chars.branch_new
        lines.append(
            f"{prefix}{self.chars.c_line_dull}{branch}{self.chars.line_hor_str}{self.chars.ignored}{self.chars.c_reset}{self.chars.c_line}\n"
        )

    def _render_file_contents(self, filepath: str, prefix: str, is_last: bool, border_color: str, lines: list[str]) -> None:
        """Read and render the contents of a text file into the tree view."""

        indent_str = " " * self.chars.indent_size if is_last else f"{self.chars.line_ver}{' ' * (self.chars.indent_size - 1)}"
        content_prefix = f"{prefix}{indent_str}"

        try:
            with open(filepath, encoding="utf-8", errors="replace") as file:
                file_lines = file.readlines()

            if not file_lines:
                return

            file_lines = [
                line.replace("\t", "    ")
                .translate(
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
                .rstrip()
                for line in file_lines
            ]

            max_content_width = max(10, self.config.max_width - len(content_prefix) - 4) if self.config.max_width > 0 else 0

            wrapped_lines: list[str] = []
            for line in file_lines:
                if self.config.max_width > 0 and len(line) > max_content_width:
                    chunk = textwrap.wrap(line, width=max_content_width, drop_whitespace=True, break_long_words=True)
                    if not chunk:
                        wrapped_lines.append("")
                    else:
                        wrapped_lines.extend(chunk)
                else:
                    wrapped_lines.append(line)
            file_lines = wrapped_lines

            truncation_msg = ""
            if self.config.max_content_lines > 0 and len(file_lines) > self.config.max_content_lines:
                remaining = len(file_lines) - self.config.max_content_lines
                file_lines = file_lines[: self.config.max_content_lines]
                truncation_msg = f"{remaining} more"

            content_width = max((len(line) for line in file_lines), default=0)
            if truncation_msg:
                content_width = max(content_width, len(truncation_msg))

            hor_border = self.chars.line_hor * (content_width + 2)

            lines.append(
                f"{self.chars.c_line}{content_prefix}{border_color}{self.chars.branch_new}{hor_border}{self.chars.corners[2]}\n"
            )

            for line in file_lines:
                padding = " " * (content_width - len(line))
                lines.append(
                    f"{self.chars.c_line}{content_prefix}{border_color}{self.chars.line_ver} {line}"
                    f"{self.chars.c_reset}{border_color}{padding} {self.chars.line_ver}\n"
                )

            if truncation_msg:
                padding = " " * (content_width - len(truncation_msg))
                lines.append(
                    f"{self.chars.c_line}{content_prefix}{border_color}{self.chars.line_ver} "
                    f"{padding}{self.chars.c_italic}{truncation_msg}"
                    f"{self.chars.c_reset}{border_color} {self.chars.line_ver}\n"
                )

            lines.append(
                f"{self.chars.c_line}{content_prefix}{border_color}{self.chars.corners[0]}{hor_border}{self.chars.corners[1]}{self.chars.c_reset}{self.chars.c_line}\n"
            )

        except Exception:
            lines.append(
                f"{self.chars.c_line}{content_prefix}{border_color}{self.chars.corners[0]}{self.chars.line_hor}"
                f"{self.chars.c_bold_in}{self.chars.c_error} {self.chars.error} "
                f"Error reading file contents. {self.chars.c_reset}\n{self.chars.c_line}"
            )

    def _render_error(self, exc: Exception, prefix: str, lines: list[str]) -> None:
        """Render an error message node when a path cannot be accessed."""

        error_prefix = f"{prefix}{self.chars.corners[0]}{self.chars.line_hor * (self.chars.indent_size - 1)}"
        lines.append(
            f"{error_prefix}{self.chars.c_bold_in}{self.chars.c_error} {self.chars.error} "
            f"{exc!s} {self.chars.c_reset}\n{self.chars.c_line}"
        )

    def _get_file_color(self, entry: os.DirEntry[str]) -> tuple[str, str]:
        """Determine the color string for a file based on its type and extension."""

        if entry.is_symlink():
            return self.chars.c_symlink, self.chars.c_symlink_dim

        try:
            if entry.stat(follow_symlinks=False).st_mode & 0o111:
                return self.chars.c_executable, self.chars.c_executable_dim
        except Exception:
            pass

        dot = (name := entry.name).rfind(".")
        ext = name[dot:].lower() if dot > 0 else ""

        if ext in EXEC_EXTS:
            return self.chars.c_executable, self.chars.c_executable_dim
        elif ext in IMAGE_EXTS:
            return self.chars.c_image, self.chars.c_image_dim
        elif ext in ARCHIVE_EXTS:
            return self.chars.c_archive, self.chars.c_archive_dim
        elif ext in CODE_EXTS:
            return self.chars.c_code, self.chars.c_code_dim
        elif ext in VIDEO_EXTS:
            return self.chars.c_video, self.chars.c_video_dim
        elif ext in AUDIO_EXTS:
            return self.chars.c_audio, self.chars.c_audio_dim

        return self.chars.c_file, self.chars.c_file_dim

    @staticmethod
    @lru_cache(maxsize=1024)
    def _is_text_file(filepath: str) -> bool:
        """Determine if a file is a text file by inspecting its mime type or bytes."""

        if Path(filepath).suffix.lower() in BINARY_EXTS:
            return False

        try:
            with open(filepath, "rb") as file:
                if not (chunk := file.read(1024)):
                    return False
                return b"\0" not in chunk
        except Exception:
            return False


def get_user_inputs(config: TreeConfig) -> None:
    """Prompt the user for terminal inputs to construct the TreeConfig interactively."""

    if not ARGS.ignore_dirs.exists:
        ignore_input = xx.console.input(
            StyledText(
                S.BOLD("Which directory names/paths should be ignored? "),
                S.DIM("(", S.CYAN("|"), " separated)\n"),
                " > ",
            ),
        )
        config.ignore_dirs = [i_dir.strip() for i_dir in ignore_input.split("|")]

    config.auto_ignore_mode = cast(
        "Literal[0, 1, 2]",
        xx.console.input(
            StyledText(
                S.BOLD("Auto-ignore unimportant directories?\n"),
                "0 = None, 1 = Hardcoded only, 2 = Smart\n",
                (S.DIM(f"({config.auto_ignore_mode})"), " > "),
            ),
            max_len=1,
            allowed_chars="012",
            default_val=config.auto_ignore_mode,
            output_type=int,
        ),
    )

    if not ARGS.include_file_contents.exists:
        content_input = xx.console.input(
            StyledText(
                S.BOLD("How much file contents should be included?\n"),
                "0 = full file contents, N = first N lines\n",
                (S.DIM("(none)"), " > "),
            ),
        )
        if content_input.strip() == "":
            config.include_file_contents = False
        else:
            try:
                config.include_file_contents = True
                config.max_content_lines = max(0, int(content_input))
            except ValueError:
                config.include_file_contents = False

    config.indent = xx.console.input(
        StyledText(
            S.BOLD("What should the indentation size be?\n"),
            (S.DIM(f"({config.indent})"), " > "),
        ),
        max_len=2,
        allowed_chars="0123456789",
        default_val=config.indent,
        output_type=int,
    )


def main() -> None:  # noqa: C901
    if ARGS.help.exists:
        print_help()
        return
    else:
        print()

    base_dir = Path(val) if (val := ARGS.base_dir.get(0)) else Path.cwd()

    if ARGS.ignore_dirs.exists:
        ignore_dirs = [i_dir.strip() for i_dir in ARGS.ignore_dirs.values[0].split("|")] if ARGS.ignore_dirs.values else []
    else:
        ignore_dirs = DEFAULT["ignore_dirs"].copy()

    inc_contents = DEFAULT["include_file_contents"]
    max_lines = DEFAULT["max_content_lines"]

    if (inc_contents := ARGS.include_file_contents.exists) and (flag_val := ARGS.include_file_contents.get(0)) is not None:
        try:
            max_lines = max(0, int(flag_val))
        except ValueError:
            max_lines = 0

    auto_ignore_mode = DEFAULT["auto_ignore_mode"]
    if ARGS.auto_ignore_mode.exists and (flag_val := ARGS.auto_ignore_mode.get(0)) is not None:
        try:
            val = int(flag_val)
            if val not in (0, 1, 2):
                raise ValueError
            auto_ignore_mode = val
        except ValueError:
            xx.console.fail(f"Invalid auto-ignore mode: {flag_val}. Must be 0, 1, or 2.", start="\n", end="\n\n")

    config = TreeConfig(
        base_dir=base_dir,
        ignore_dirs=ignore_dirs,
        auto_ignore_mode=auto_ignore_mode,
        include_file_contents=inc_contents,
        max_content_lines=max_lines,
        indent=DEFAULT["indent"],
    )

    into_file = DEFAULT["into_file"]
    target_path = Path.cwd() / "tree.txt"

    if (into_file := ARGS.to_file.exists) and (val := ARGS.to_file.get(0)) is not None:
        target_path = Path(val).resolve()
        if target_path.is_dir() or val.endswith("/") or val.endswith("\\"):
            target_path = target_path / "tree.txt"

    if ARGS.interactive.exists:
        get_user_inputs(config)

        if not ARGS.to_file.exists:
            into_file = (
                xx.console.input(
                    StyledText(
                        S.BOLD("Output tree to a file?\n"),
                        (S.DIM("(Y)" if into_file else "(N)"), " > "),
                    ),
                    max_len=1,
                    allowed_chars="yYnN",
                    default_val="Y" if into_file else "N",
                ).upper()
                == "Y"
            )

        print()

    # Re-initialize config in case user changed indent/style properties:
    config = TreeConfig(
        base_dir=config.base_dir,
        max_width=0 if into_file else xx.console.get_width(),
        ignore_dirs=config.ignore_dirs,
        auto_ignore_mode=config.auto_ignore_mode,
        include_file_contents=config.include_file_contents,
        max_content_lines=config.max_content_lines,
        indent=config.indent,
    )

    renderer = TreeRenderer(config)
    result = renderer.generate()

    if into_file:
        if not target_path.parent.exists():
            xx.console.fail(
                StyledText("Directory ", S.BR.CYAN(str(target_path.parent)), " does not exist."),
                start="\x1b[F\x1b[K",
                end="\n\n",
            )

        file, cls_line = None, ""
        try:
            file = xx.file.create(str(target_path), result.raw)
        except FileExistsError:
            cls_line = "\x1b[F\x1b[K"
            if xx.console.confirm(
                StyledText("  ", S.WHITE(target_path.name), " already exists. Overwrite? "), start=cls_line, end=""
            ):
                file = xx.file.create(str(target_path), result.raw, force=True)
            else:
                xx.console.exit(start=cls_line, end="\n\n")

        if file:
            xx.console.done(StyledText("Generated tree to ", (S.WHITE | S.link(file))(file.name)), start=cls_line, end="\n\n")
        else:
            xx.console.fail(StyledText((S.BR.RED)("File is empty or failed to create file.")), start=cls_line, end="\n\n")

    else:
        result.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        StyledText(S.RESET, "\x1b[F\x1b[K", S.BR.RED("✗ Canceled by user.")).print(end="\n\n")
    except PermissionError:
        xx.console.fail("Permission to create file was denied.", start="\n", end="\n\n")
    except Exception as exc:
        xx.console.fail(exc, start="\n", end="\n\n")
