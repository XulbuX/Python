"""A really advanced directory tree generator
with a lost of options and customization."""
from xulbux import FormatCodes, Console, File, COLOR
from typing import Optional, Pattern, NamedTuple
from functools import lru_cache
from itertools import chain
import time
import sys
import os
import re


FIND_ARGS = {
    "ignore_dirs": ["-i", "--ignore"],
    "no_progress": ["-n", "-np", "--no-progress"],
}
DEFAULT = {
    "ignore_dirs": [],
    "auto_ignore": True,
    "include_file_contents": False,
    "tree_style": 2,
    "indent": 2,
    "into_file": False,
}


class IgnoreDirectory(Exception):
    pass


class DirScanResult(NamedTuple):

    should_ignore: bool
    total_count: int
    hash_count: int
    show_partial: bool
    entries: tuple


class GenerationStats:

    processed_dirs: int = 0
    processed_files: int = 0
    current_depth: int = 0
    max_depth: int = 0


class IGNORE:

    sep: str = r"[-_~x@\s]+"
    ext: str = r"(?:\.[-_a-zA-Z0-9]+)*?$"
    pre: str = rf"^(?![a-zA-Z]+\.[a-zA-Z])(?:\w+{sep}\w*)*?"
    date = r"[12][0-9]{3}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])"
    reoccurring: dict[str, str] = {
        "number": r"-?[a-fA-F0-9]{4,}",
        "delimited_number": r"_[0-9]{1,2}",
        "hex": r"(?:[a-fA-F0-9]{16}[a-fA-F0-9]{20}|[a-fA-F0-9]{32}|[a-fA-F0-9]{38}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64})",
        "min_hex32": r"\.min_[a-fA-F0-9]{32}",
        "id3hex4": rf"\w{{3}}[a-fA-F0-9]{{4}}(?:{sep}|{ext})",
        "rand4": rf"(?![A-Z][a-z]{{3}})(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9]))[a-zA-Z0-9]{{4}}{ext}",
        "rand5": rf"(?![A-Z][a-z]{{4}})(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9]))[a-zA-Z0-9]{{5}}{ext}",
        "rand11": rf"(?![A-Z][a-zA-Z]{{10}})(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9]))[a-zA-Z0-9]{{11}}(?:{sep}|{ext})",
        "rand25": rf"(?![A-Z][a-zA-Z]{{24}})(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9]))[a-zA-Z0-9]{{25}}(?:{sep}|{ext})",
        "rand32": rf"(?![A-Z][a-zA-Z]{{31}})(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9]))[a-zA-Z0-9]{{32}}(?:{sep}|{ext})",
        "rand59": rf"(?![A-Z][a-zA-Z]{{58}})(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9]))[a-zA-Z0-9]{{59}}(?:{sep}|{ext})",
        "e_rand32": rf"e_[a-zA-Z0-9]{{32}}(?:{sep}|{ext})",
        "num5-rand12": r"[0-9]{5}-[a-zA-Z0-9]{12}",
        "lower32_num1,2.hex64": r"[a-z]{32}_[0-9]{1,2}\.[a-fA-F0-9]{64}",
        "date": date,
        "delimited_date": r"(?:[0-9]{2}|[0-9]{4})[-.](?:[0-9]{2}|[0-9]{4})[-.](?:[0-9]{2}|[0-9]{4})",
        "domain": r"[-a-z]+(?:\.[-a-z]+){2,}",
        "version.date": r"(?:[0-9]\.){3}" + date,
        "base64": r"[+/0-9A-Za-z]{8,}={1,2}",
        "uuid": rf"\{{?[a-zA-Z0-9]{{8}}-[a-zA-Z0-9]{{4}}-[a-zA-Z0-9]{{4}}-[a-zA-Z0-9]{{4}}-[a-zA-Z0-9]{{12}}\}}?(?:[-_a-zA-Z0-9]+(?:{sep}|{ext}))?",
        "sid": r"S-[0-9]+-[0-9]+(?:-[0-9]+){2,}",
    }
    standalones: dict[str, str] = {
        "hex2": r"[a-fA-F0-9]{2}",
        "upper2": r"[A-Z]{2}" + ext,
        "alt-lower2": r"alt-[a-z]{2}" + ext,
        "rand_num": r"[A-Z0-9]{2,6}_[a-z][0-9]" + ext,
        "id_num": r"(?:[a-zA-Z0-9]{6}-){2}[a-zA-Z0-9]{6}\s(?:[0-9]{2}|[a-z][0-9]{2})",
        "domain_hex": rf"{reoccurring['domain']}_{reoccurring['hex']}",
        "camelCase_version-hex64": r"[a-z]+(?:[A-Z][a-z]+)*?_[0-9]{1,2}(?:\.[0-9]{1,2})+-[a-fA-F0-9]{64}",
    }
    pattern: Pattern = re.compile(
        rf"(?:^(?:{'|'.join(standalones.values())})$|{pre}(?:(?:{sep})?(?:{'|'.join(reoccurring.values())}))+{ext})"
    )


class Tree:

    _NEWLINE = b"\n"
    _SPACE = b" "

    BINARY_EXTENSIONS: frozenset[str] = frozenset({
        ".exe", ".dll", ".so", ".dylib", ".bin", ".dat", ".db", ".sqlite", ".jpg", ".jpeg", ".png", ".gif", ".ico", ".cur",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".tar", ".gz", ".7z", ".rar", ".mp3", ".mp4", ".avi", ".mov"
    })
    IGNORE_DIRS: list[str] = [
        d.lower() for d in {
            "$RECYCLE.BIN", ".git", "code_tracker", "node_modules", "storage/framework", "addons-l10n", "__pycache__", "npm",
            ".npm", "nvm", ".nvm", "env", "venv", ".env", ".venv", "build", "dist", "cache", "cache_data", "HTMLCache",
            "Code Cache", "D3DSCache", "DawnGraphiteCache", "GrShaderCache", "DawnWebGPUCache", "GPUCache",
            "node-compile-cache", "component_crx_cache", "DEVSENSE/packages-cache", "target", "bin", "_locales",
            "AutofillStates", "obj", ".idea", ".vscode", ".vs", ".codeium", ".adobe", "coverage", "logs", "log", "tmp", "temp",
            ".next", ".nuxt", "out", ".output", ".cache", "vendor", "packages", ".terraform", ".angular", ".svn", "CVS", ".hg",
            ".pytest_cache", ".coverage", "htmlcov", ".tox", "site-packages", ".DS_Store", "bower_components", ".sass-cache",
            ".parcel-cache", ".webpack", ".gradle", ".mvn", "Pods", "xcuserdata", "hyphen-data", "junit", "reports", ".github",
            ".gitlab", "docker", ".docker", ".kube", "node", "jspm_packages", ".npm", "artifacts", ".yarn", "wheels",
            "docs/_build", "_site", ".jekyll-cache", ".ipynb_checkpoints", ".mypy_cache", ".pytest_cache",
            "celerybeat-schedule", ".sonar", ".scannerwork", "migrations", "__tests__", "test-results", "coverage-reports",
            ".nx", "dist-newstyle", "target", "debugbar", "Debug", "Release", "x64", "x86"
        }
    ]

    def __init__(
        self,
        base_dir: Optional[str] = None,
        ignore_dirs: Optional[list[str]] = [],
        auto_ignore: Optional[bool] = True,
        include_file_contents: Optional[bool] = False,
        style: Optional[int] = 1,
        indent: Optional[int] = 2,
        display_progress: Optional[bool] = True,
    ):
        self.base_dir: str = base_dir
        self.ignore_dirs: list[str] = ignore_dirs + (self.IGNORE_DIRS if auto_ignore else [])
        self.auto_ignore: bool = auto_ignore
        self.include_file_contents: bool = include_file_contents
        self.style: int = style
        self.indent: int = indent
        self.display_progress: bool = display_progress
        self.ignore_set: frozenset[str] = None
        self.style_presets: dict[int, dict[str, str]] = {
            1: {
                "line_ver": "│",
                "line_hor": "─",
                "branch_new": "├",
                "corners": ("└", "┘", "┐"),
                "error": "⚠",
                "ignored": "...",
                "dirname_end": "/",
            },
            2: {
                "line_ver": "│",
                "line_hor": "─",
                "branch_new": "├",
                "corners": ("╰", "╯", "╮"),
                "error": "⚠",
                "ignored": "...",
                "dirname_end": "/",
            },
            3: {
                "line_ver": "┃",
                "line_hor": "━",
                "branch_new": "┣",
                "corners": ("┗", "┛", "┓"),
                "error": "⚠",
                "ignored": "...",
                "dirname_end": "/",
            },
            4: {
                "line_ver": "║",
                "line_hor": "═",
                "branch_new": "╠",
                "corners": ("╚", "╝", "╗"),
                "error": "⚠",
                "ignored": "...",
                "dirname_end": "/",
            },
        }
        self._error_suffix = None
        self._ignored_suffix = None
        self._reset_style_attrs()
        self.gen_stats = None
        self._progress_update_interval = 0.05  # SECONDS BETWEEN UPDATES
        self._last_progress_update = 0

    def generate(
        self,
        base_dir: Optional[str] = None,
        ignore_dirs: list[str] = [],
        auto_ignore: Optional[bool] = None,
        include_file_contents: Optional[bool] = None,
        style: Optional[int] = None,
        indent: Optional[int] = None,
        display_progress: Optional[bool] = None,
    ) -> str:
        self.display_progress = self.display_progress if display_progress is None else display_progress
        if self.display_progress:
            Console.info("starting tree generation...", start="\n")
        else:
            Console.info("generating tree...", start="\n")
        self.gen_stats = GenerationStats()
        self.base_dir = base_dir or self.base_dir
        self.ignore_dirs += ignore_dirs
        self.auto_ignore = self.auto_ignore if auto_ignore is None else auto_ignore
        self.include_file_contents = include_file_contents or self.include_file_contents
        self.style = style if style >= 1 else self.style
        self.indent = (indent if indent >= 0 else self.indent) + 1
        self.base_dir = os.path.abspath(str(self.base_dir))
        if not os.path.isdir(self.base_dir):
            raise ValueError(f"Invalid base directory: {self.base_dir}")
        self.ignore_set = (
            frozenset() if len(
                norm_ignore_dirs := set(
                    # Normalize paths and convert absolute paths to start with /
                    (d.lower().replace("\\", "/") if not os.path.isabs(d) else "/" + d.lower().replace("\\", "/").lstrip("/"))
                    for d in self.ignore_dirs
                )
            ) == 0 else frozenset(norm_ignore_dirs)
        )
        self._reset_style_attrs()
        result = self._gen_tree(self.base_dir)
        Console.done(
            f"[b](Generated tree:) max depth [br:cyan]({self.gen_stats.max_depth}) [dim](|) [br:cyan]({self.gen_stats.processed_dirs}) dirs [dim](|) [br:cyan]({self.gen_stats.processed_files}) files",
            start="\033[F\033[K"
        )
        return result

    def _reset_style_attrs(self) -> None:
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
        self._error_suffix_b = f"{self.error} [Error: ".encode()
        self._ignored_suffix_b = f"{self.line_hor}{self.ignored}\n".encode()
        self._prefix_space = b" " * self.indent
        self._prefix_ver = self._line_ver_b + b" " * (self.indent - 1)

    def show_styles(self) -> None:
        for style, details in self.style_presets.items():
            print(
                f"{style}: {details["corners"][0]}{details["line_hor"]}{details["ignored"]}{details["dirname_end"]}",
                flush=True,
            )

    @staticmethod
    @lru_cache(maxsize=4096)
    def _encode_str(s: str) -> bytes:
        return s.encode()

    @staticmethod
    @lru_cache(maxsize=4096)
    def _is_likely_hash_name(name: str) -> bool:
        return bool(IGNORE.pattern.match(name))

    @staticmethod
    def _find_filename_patterns(names: list[str], min_pattern_length: int = 4) -> tuple[bool, float]:
        """Analyze filenames to detect patterns indicating localization, versioning etc."""
        if len(names) < 5:
            return False, 0.0
        prefixes = {}
        suffixes = {}
        for name in names:
            base, _ = os.path.splitext(name)
            for i in range(1, len(base) + 1):
                prefix = base[:i]
                if len(prefix) >= min_pattern_length:
                    prefixes[prefix] = prefixes.get(prefix, 0) + 1
                suffix = base[-i:]
                if len(suffix) >= min_pattern_length:
                    suffixes[suffix] = suffixes.get(suffix, 0) + 1
        best_prefix_count = max(prefixes.values()) if prefixes else 0
        best_suffix_count = max(suffixes.values()) if suffixes else 0
        total_files = len(names)
        pattern_ratio = max(best_prefix_count, best_suffix_count) / total_files
        return (max(best_prefix_count, best_suffix_count) >= 5 and pattern_ratio >= 0.7), pattern_ratio

    @lru_cache(maxsize=1024)
    def _scan_directory(self, dir_path: str) -> DirScanResult:
        """Cached directory scanning with analysis."""
        if not self.auto_ignore:
            with os.scandir(dir_path) as it:
                return DirScanResult(False, 0, 0, False, tuple(it))
        try:
            with os.scandir(dir_path) as it:
                entries = tuple(it)
            if not entries:
                return DirScanResult(False, 0, 0, False, entries)
            dir_name = os.path.basename(dir_path)
            total_count = len(entries)
            if total_count < 3:
                return DirScanResult(False, total_count, 0, False, entries)
            hash_count = normal_count = 0
            filenames = []
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
        except PermissionError:
            return DirScanResult(False, 0, 0, False, ())

    def _should_ignore_path(self, path: str) -> bool:
        """Check if a path matches any ignore pattern by first checking the last directory name."""
        if not path:
            return False
        path_parts = path.lower().replace("/", "\\").split("\\")
        matching_patterns = [p for p in self.ignore_set if p.split("/")[-1] == path_parts[-1]]
        if not matching_patterns:
            return False
        for pattern in matching_patterns:
            pattern_parts = pattern.split("/")
            if len(pattern_parts) <= len(path_parts):
                path_slice = path_parts[-len(pattern_parts):]
                if path_slice == pattern_parts:
                    return True
                if pattern.startswith("/"):
                    if pattern_parts == path_parts:
                        return True
        return False

    @staticmethod
    @lru_cache(maxsize=1024)
    def _is_text_file(filepath: str) -> bool:
        if os.path.splitext(filepath)[1].lower() in Tree.BINARY_EXTENSIONS:
            return False
        try:
            with open(filepath, "rb") as f:
                chunk = f.read(1024)
                text_characters = bytes(range(32, 127)) + b"\n\r\t\f\b"
                return bool(chunk) and all(byte in text_characters for byte in chunk)
        except Exception:
            return False

    def _update_progress(self, current_dir: str, is_dir: bool = True) -> None:
        """Update the generation progress display."""
        if is_dir:
            self.gen_stats.processed_dirs += 1
        else:
            self.gen_stats.processed_files += 1
        self.gen_stats.current_depth = current_dir.count(os.sep) - self.base_dir.count(os.sep)
        self.gen_stats.max_depth = max(self.gen_stats.max_depth, self.gen_stats.current_depth)
        if not self.display_progress:
            return
        elif (current_time := time.time()) - self._last_progress_update < self._progress_update_interval:
            return
        self._last_progress_update = current_time
        rel_path = current_dir[len(self.base_dir):].lstrip(os.sep) if current_dir.startswith(
            self.base_dir
        ) else os.path.basename(current_dir)
        max_rel_path_len = Console.w - (
            30 + len(
                f"depth {self.gen_stats.current_depth}/{self.gen_stats.max_depth} | {self.gen_stats.processed_dirs} dirs | {self.gen_stats.processed_files} files | "
            )
        )
        if len(rel_path) > max_rel_path_len:
            rel_path = ("..." + rel_path[-max_rel_path_len:])
        Console.log(
            "GENERATING TREE",
            f"depth [br:cyan]({self.gen_stats.current_depth}/{self.gen_stats.max_depth}) [dim](|) [br:cyan]({self.gen_stats.processed_dirs}) dirs [dim](|) [br:cyan]({self.gen_stats.processed_files}) files [dim](|) [white]{rel_path}[_]",
            title_bg_color=COLOR.blue,
            start="\033[F\033[K",
        )

    def _gen_tree(self, _dir: str, _prefix: str = "", _level: int = 0, _parent_path: str = "") -> str:
        """Generate tree for directory.
        _dir: Current directory path
        _prefix: Line prefix for visual tree structure
        _level: Current recursion depth
        _parent_path: Relative path from base_dir to current dir"""
        self._update_progress(_dir)
        result = bytearray()
        try:
            if (_level == 0):
                base_name = os.path.basename(_dir.rstrip(os.sep)) or os.path.splitdrive(_dir)[0]
                result.extend(base_name.encode())
                result.extend(self._dirname_end_b)
                result.extend(self._NEWLINE)
                _parent_path = ""
            scan_result = self._scan_directory(_dir)
            entries = scan_result.entries
            if not entries:
                return "" if result is None else bytes(result).decode()
            prefix_bytes = self._encode_str(_prefix)
            if scan_result.should_ignore:
                result.extend(prefix_bytes)
                result.extend(self._corners_b[0])
                result.extend(self._ignored_suffix_b)
                return "" if result is None else bytes(result).decode()
            should_ignore, _, _, show_partial = scan_result.should_ignore, scan_result.total_count, scan_result.hash_count, scan_result.show_partial
            if should_ignore:
                result.extend(prefix_bytes)
                result.extend(self._corners_b[0])
                result.extend(self._ignored_suffix_b)
                return "" if result is None else bytes(result).decode()
            entries_count = len(entries)
            prefix_ver = prefix_bytes + self._line_ver_b + self._tab[:-1]
            prefix_tab = prefix_bytes + self._tab
            if show_partial:
                visible_entries, last_was_ignored = [], False
                for entry in entries:
                    is_ignored = self._is_likely_hash_name(entry.name)
                    if not is_ignored:
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
                        result.extend((self._corners_b[0] if is_last else self._branch_new_b))
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
                        result.extend(self._gen_tree(entry.path, new_prefix, _level + 1).encode())
                    else:
                        self._update_progress(entry.path, is_dir=False)
                        result.extend(current_prefix)
                        result.extend(entry.name.encode())
                        result.extend(self._NEWLINE)
                        if self.include_file_contents and self._is_text_file(entry.path):
                            content_prefix = _prefix + (
                                " " * self.indent if is_last else self.line_ver + " " * (self.indent - 1)
                            )
                            try:
                                with open(entry.path, "r", encoding="utf-8", errors="replace") as f:
                                    lines = f.readlines()
                                    if lines:
                                        lines = [
                                            l.replace("\t", "    ").translate({
                                                0x2000: " ", 0x2001: " ", 0x2002: " ", 0x2003: " ", 0x2004: " ", 0x2005: " ",
                                                0x2006: " ", 0x2007: " ", 0x2008: " ", 0x2009: " ", 0x200A: " "
                                            }) for l in lines
                                        ]
                                        content_width = max(len(line.rstrip()) for line in lines)
                                        hor_border = self.line_hor * (content_width + 2)
                                        result.extend(
                                            f"{content_prefix}{self.branch_new}{hor_border}{self.corners[2]}\n".encode()
                                        )
                                        for l in lines:
                                            stripped = l.rstrip()
                                            padding = " " * (content_width - len(stripped))
                                            result.extend(
                                                f"{content_prefix}{self.line_ver} {stripped}{padding} {self.line_ver}\n"
                                                .encode()
                                            )
                                        result.extend(
                                            f"{content_prefix}{self.corners[0]}{hor_border}{self.corners[1]}\n".encode()
                                        )
                            except:
                                result.extend(
                                    f"{content_prefix}{self.corners[0]}{self.line_hor}{self._error_suffix}Error reading file contents]\n"
                                    .encode()
                                )
            else:
                for idx, entry in enumerate(entries):
                    is_dir, is_last = entry.is_dir(), idx == entries_count - 1
                    branch = self._corners_b[0] if is_last else self._branch_new_b
                    current_prefix = prefix_bytes + branch + self._line_hor_b
                    current_rel_path = os.path.join(_parent_path, entry.name)
                    if self._should_ignore_path(current_rel_path) or (is_dir
                                                                      and self._scan_directory(entry.path).should_ignore):
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
                        result.extend(self._gen_tree(entry.path, new_prefix, _level + 1, current_rel_path).encode())
                    else:
                        self._update_progress(entry.path, is_dir=False)
                        result.extend(current_prefix)
                        result.extend(entry.name.encode())
                        result.extend(self._NEWLINE)
                        if self.include_file_contents and self._is_text_file(entry.path):
                            content_prefix = _prefix + (
                                " " * self.indent if is_last else self.line_ver + " " * (self.indent - 1)
                            )
                            try:
                                with open(entry.path, "r", encoding="utf-8", errors="replace") as f:
                                    lines = f.readlines()
                                    if lines:
                                        lines = [
                                            l.replace("\t", "    ").translate({
                                                0x2000: " ", 0x2001: " ", 0x2002: " ", 0x2003: " ", 0x2004: " ", 0x2005: " ",
                                                0x2006: " ", 0x2007: " ", 0x2008: " ", 0x2009: " ", 0x200A: " "
                                            }) for l in lines
                                        ]
                                        content_width = max(len(l.rstrip()) for l in lines)
                                        hor_border = self.line_hor * (content_width + 2)
                                        result.extend(
                                            f"{content_prefix}{self.branch_new}{hor_border}{self.corners[2]}\n".encode()
                                        )
                                        for l in lines:
                                            result.extend(
                                                f"{content_prefix}{self.line_ver} {(stripped := l.rstrip())}{" " * (content_width - len(stripped))} {self.line_ver}\n"
                                                .encode()
                                            )
                                        result.extend(
                                            f"{content_prefix}{self.corners[0]}{hor_border}{self.corners[1]}\n".encode()
                                        )
                            except:
                                result.extend(
                                    f"{content_prefix}{self.corners[0]}{self.line_hor}{self._error_suffix}Error reading file contents]\n"
                                    .encode()
                                )
        except Exception as e:
            error_prefix = (_prefix + self.corners[0] + (self.line_hor * (self.indent - 1)))
            result.extend(f"{error_prefix}{self._error_suffix}{str(e)}]\n".encode())
        return "" if result is None else bytes(result).decode()


def main():
    global ARGS
    ARGS, tree = Console.get_args(FIND_ARGS, True), Tree(os.getcwd())
    if ARGS.ignore_dirs.exists:
        ignore_dirs = ARGS.ignore_dirs.value.split()
    else:
        ignore_dirs = FormatCodes.input(
            "Enter directory names/rel-paths which's content should be ignored [dim]((space separated) >  )"
        ).strip().split()

    auto_ignore = True if FormatCodes.input(
        f"Enable auto-ignore unimportant directories [dim]({"(Y)" if DEFAULT["auto_ignore"] else "(N)"} >  )"
    ).strip().lower() in ("y", "yes") else DEFAULT["auto_ignore"]

    include_file_contents = True if FormatCodes.input(
        f"Display the file contents in the tree [dim]({"(Y)" if DEFAULT["include_file_contents"] else "(N)"} >  )"
    ).strip().lower() in ("y", "yes") else DEFAULT["include_file_contents"]

    print("Enter the tree style (1-4): ")
    tree.show_styles()
    style = (
        int(style) if (style := FormatCodes.input(f"[dim](({DEFAULT["tree_style"]}) >  )").strip()).isnumeric()
        and 1 <= int(style) <= 4 else DEFAULT["tree_style"]
    )

    indent = (
        int(indent) if (indent := FormatCodes.input(f"Enter the indent [dim](({DEFAULT["indent"]}) >  )").strip()).isnumeric()
        and int(indent) >= 0 else DEFAULT["indent"]
    )

    into_file = True if FormatCodes.input(f"Output tree into file [dim]({"(Y)" if DEFAULT["into_file"] else "(N)"} >  )"
                                          ).strip().lower() in ("y", "yes") else DEFAULT["into_file"]

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
            file = File.create("tree.txt", result)
        except FileExistsError:
            cls_line = "\033[F\033[K"
            if Console.confirm("[white]tree.txt[_] already exists. Overwrite?", end=""):
                file = File.create("tree.txt", result, force=True)
            else:
                Console.exit()
        if file:
            Console.done(f"[white]{file}[_] successfully created.", start=cls_line, end="\n\n")
        else:
            Console.fail("File is empty or failed to create file.", start=cls_line, end="\n\n")
    else:
        FormatCodes.print("[white]")
        sys.stdout.write(result)
        FormatCodes.print("[_]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except PermissionError:
        Console.fail("Permission to create file was denied.", start="\n", end="\n\n")
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
