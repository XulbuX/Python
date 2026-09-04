#!/usr/bin/env python3
# x-cmds:file[update]
"""Quickly and accurately count lines of code in a directory or project."""

import fnmatch
import os
import re
import stat
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from pathlib import Path
from typing import NamedTuple
import xulbux as xx
from xulbux import ArgumentParser, S, Term, Throbber

# ********************************************************* CONSTANTS *********************************************************

_BUFFER_SIZE: int = 65536
"""Buffer size in bytes for reading file chunks during line counting."""

_CHECK_LIMIT: int = 8192
"""Maximum number of bytes sampled from a file to determine if it is binary."""

# ****************************************************** HELPER CLASSES *******************************************************


class GitIgnoreRule:
    """Represents a compiled Git ignore rule relative to a root folder.\n
    ----------------------------------------------------------------------------------------------------
    *   `base_dir` – Root folder containing the .gitignore file.
    *   `raw_pattern` – Unparsed line from the .gitignore file.
    """

    base_dir: Path
    """Directory where the .gitignore file is located."""

    negated: bool
    """Whether the pattern is negated with a leading exclamation mark."""

    dir_only: bool
    """Whether the pattern applies exclusively to directories."""

    anchored: bool
    """Whether the pattern is anchored to the base directory."""

    regex: re.Pattern[str]
    """Compiled regular expression for matching paths against the pattern."""

    def __init__(self, base_dir: Path, raw_pattern: str) -> None:
        self.base_dir = base_dir
        pattern_str = raw_pattern.strip()
        self.negated = pattern_str.startswith("!")
        if self.negated:
            pattern_str = pattern_str[1:].strip()

        self.dir_only = pattern_str.endswith("/")
        clean_pattern = pattern_str.rstrip("/")
        self.anchored = "/" in clean_pattern.lstrip("/") or clean_pattern.startswith("/")
        pattern_flags = re.IGNORECASE if os.name == "nt" else 0
        compile_target = clean_pattern.lstrip("/") if self.anchored else clean_pattern
        self.regex = re.compile(fnmatch.translate(compile_target), pattern_flags)

    def matches(self, target_path: Path, is_dir: bool) -> bool | None:
        """Check whether this rule matches a target path.\n
        ----------------------------------------------------------------------------------------------------
        *   `target_path` – Path to inspect.
        *   `is_dir` – Whether the path refers to a directory.
        """

        try:
            rel_posix = target_path.relative_to(self.base_dir).as_posix()
        except ValueError:
            return None

        if self.anchored:
            if self.dir_only and not is_dir:
                return None
            if self.regex.fullmatch(rel_posix):
                return not self.negated
        else:
            if not (self.dir_only and not is_dir) and self.regex.fullmatch(target_path.name):
                return not self.negated
            for parent_dir in target_path.parents:
                if parent_dir == self.base_dir:
                    break
                if self.regex.fullmatch(parent_dir.name):
                    return not self.negated

        return None


class ScanResult(NamedTuple):
    """Container holding collected line counting statistics.\n
    ----------------------------------------------------------------------------------------------------
    *   `total_lines` – Total number of lines counted across all matched files.
    *   `total_files` – Total count of processed files.
    *   `files_data` – Dictionary mapping relative file paths to their individual line counts.
    *   `extensions_data` – Dictionary mapping file extensions to counts of lines and files.
    """

    total_lines: int
    """Sum of lines of code across all processed files."""

    total_files: int
    """Number of files successfully processed."""

    files_data: dict[str, int]
    """Mapping of relative file path strings to line counts."""

    extensions_data: dict[str, dict[str, int]]
    """Mapping of file extensions to counts of lines and files."""


# ***************************************************** HELPER FUNCTIONS ******************************************************


def is_hidden_entry(entry: os.DirEntry[str]) -> bool:
    """Check whether a directory entry represents a hidden or system item.\n
    ----------------------------------------------------------------------------------------------------
    *   `entry` – Directory entry to inspect.
    """

    if entry.name.startswith("."):
        return True

    if os.name == "nt":
        with suppress(AttributeError, OSError):
            file_attrs = entry.stat(follow_symlinks=False).st_file_attributes
            if entry.is_dir(follow_symlinks=False):
                return bool(file_attrs & stat.FILE_ATTRIBUTE_HIDDEN)
            return bool(file_attrs & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM))
    else:
        entry_path = entry.path
        system_dirs = {"/proc", "/sys", "/dev", "/tmp"}
        if entry_path in system_dirs:
            return True
        for sys_dir in system_dirs:
            if entry_path.startswith(sys_dir):
                return True

    return False


def parse_glob_patterns(raw_input: str) -> list[str]:
    """Parse comma, pipe, or space delimited glob patterns from user input.\n
    ----------------------------------------------------------------------------------------------------
    *   `raw_input` – Raw string containing one or more glob patterns.
    """

    normalized = raw_input.replace("|", " ").replace(",", " ")
    return [token.strip() for token in normalized.split() if token.strip()]


def compile_glob_patterns(patterns: list[str]) -> list[tuple[re.Pattern[str], bool]]:
    """Compile a list of glob patterns into regular expressions.\n
    ----------------------------------------------------------------------------------------------------
    *   `patterns` – List of glob pattern strings.
    """

    compiled: list[tuple[re.Pattern[str], bool]] = []
    pattern_flags = re.IGNORECASE if os.name == "nt" else 0

    for pattern in patterns:
        clean_pattern = pattern.replace("\\", "/").strip()
        if not clean_pattern:
            continue
        is_name_only = "/" not in clean_pattern
        target = clean_pattern if is_name_only else clean_pattern.lstrip("/")
        with suppress(re.error):
            compiled.append((re.compile(fnmatch.translate(target), pattern_flags), is_name_only))

    return compiled


def matches_glob_patterns(name: str, rel_path: str, patterns: list[tuple[re.Pattern[str], bool]]) -> bool:
    """Check whether a file name or relative path matches any compiled glob pattern.\n
    ----------------------------------------------------------------------------------------------------
    *   `name` – Base name of the file or directory.
    *   `rel_path` – Relative POSIX path from the scanning root directory.
    *   `patterns` – List of compiled pattern regexes with name-only flags.
    """

    for pattern_regex, is_name_only in patterns:
        if is_name_only:
            if pattern_regex.fullmatch(name) or pattern_regex.fullmatch(rel_path):
                return True
        elif pattern_regex.fullmatch(rel_path):
            return True

    return False


def load_gitignore_rules(directory: Path) -> list[GitIgnoreRule]:
    """Load and compile .gitignore rules from a directory and all parent directories.\n
    ----------------------------------------------------------------------------------------------------
    *   `directory` – Directory from which to discover .gitignore files.
    """

    rules: list[GitIgnoreRule] = []
    hierarchy = [directory, *list(directory.parents)]
    hierarchy.reverse()

    for folder in hierarchy:
        ignore_path = folder / ".gitignore"
        if not ignore_path.is_file():
            continue
        try:
            with open(ignore_path, encoding="utf-8", errors="ignore") as file_handle:
                for line in file_handle:
                    if not (stripped_line := line.strip()) or stripped_line.startswith("#"):
                        continue
                    with suppress(re.error):
                        rules.append(GitIgnoreRule(folder, stripped_line))
        except (OSError, UnicodeDecodeError):
            continue

    return rules


def parse_gitignore_file(gitignore_path: Path) -> list[GitIgnoreRule]:
    """Parse a single .gitignore file and return its compiled rules.\n
    ----------------------------------------------------------------------------------------------------
    *   `gitignore_path` – Path to the .gitignore file.
    """

    rules: list[GitIgnoreRule] = []
    parent_dir = gitignore_path.parent

    try:
        with open(gitignore_path, encoding="utf-8", errors="ignore") as file_handle:
            for line in file_handle:
                if not (stripped_line := line.strip()) or stripped_line.startswith("#"):
                    continue
                with suppress(re.error):
                    rules.append(GitIgnoreRule(parent_dir, stripped_line))
    except (OSError, UnicodeDecodeError):
        pass

    return rules


def is_gitignored(target_path: Path, is_dir: bool, rules: list[GitIgnoreRule]) -> bool:
    """Check whether a path is ignored according to active Git ignore rules.\n
    ----------------------------------------------------------------------------------------------------
    *   `target_path` – Path to inspect.
    *   `is_dir` – Whether the path is a directory.
    *   `rules` – List of active Git ignore rules.
    """

    ignored = False
    for rule in rules:
        if (rule_match := rule.matches(target_path, is_dir)) is not None:
            ignored = rule_match

    return ignored


def should_skip_directory(
    entry: os.DirEntry[str],
    rel_posix: str,
    skip_hidden: bool,
    apply_gitignore: bool,
    rules: list[GitIgnoreRule],
    exclude_patterns: list[tuple[re.Pattern[str], bool]],
) -> bool:
    """Check whether a directory entry should be skipped during scanning.\n
    ----------------------------------------------------------------------------------------------------
    *   `entry` – Directory entry to inspect.
    *   `rel_posix` – Relative POSIX path from the scanning root.
    *   `skip_hidden` – Whether hidden directories should be skipped.
    *   `apply_gitignore` – Whether Git ignore rules are active.
    *   `rules` – List of active Git ignore rules.
    *   `exclude_patterns` – List of compiled exclude glob patterns.
    """

    if entry.name == ".git" and skip_hidden:
        return True

    if skip_hidden and is_hidden_entry(entry):
        return True

    if apply_gitignore and is_gitignored(Path(entry.path), True, rules):
        return True

    return bool(exclude_patterns and matches_glob_patterns(entry.name, rel_posix, exclude_patterns))


def should_include_file(
    entry: os.DirEntry[str],
    rel_posix: str,
    skip_hidden: bool,
    apply_gitignore: bool,
    rules: list[GitIgnoreRule],
    include_patterns: list[tuple[re.Pattern[str], bool]],
    exclude_patterns: list[tuple[re.Pattern[str], bool]],
) -> bool:
    """Check whether a file entry should be processed for line counting.\n
    ----------------------------------------------------------------------------------------------------
    *   `entry` – File entry to inspect.
    *   `rel_posix` – Relative POSIX path from the scanning root.
    *   `skip_hidden` – Whether hidden files should be skipped.
    *   `apply_gitignore` – Whether Git ignore rules are active.
    *   `rules` – List of active Git ignore rules.
    *   `include_patterns` – List of compiled include glob patterns.
    *   `exclude_patterns` – List of compiled exclude glob patterns.
    """

    if skip_hidden and is_hidden_entry(entry):
        return False

    if apply_gitignore and is_gitignored(Path(entry.path), False, rules):
        return False

    if exclude_patterns and matches_glob_patterns(entry.name, rel_posix, exclude_patterns):
        return False

    return not (include_patterns and not matches_glob_patterns(entry.name, rel_posix, include_patterns))


def count_lines(file_path: str) -> int:
    """Count lines in a file, returning 0 for empty or binary files.\n
    ----------------------------------------------------------------------------------------------------
    *   `file_path` – Path string of the file to count.
    """

    try:
        if (file_size := Path(file_path).stat().st_size) == 0:
            return 0

        with open(file_path, "rb") as file_handle:
            if file_size < 1024 * 1024:
                content = file_handle.read()
                if b"\x00" in content:
                    return 0
                line_count = content.count(b"\n")
                if not content.endswith(b"\n"):
                    line_count += 1
                return line_count

            line_count = 0
            bytes_read = 0
            last_chunk: bytes = b""

            while chunk := file_handle.read(_BUFFER_SIZE):
                if bytes_read < _CHECK_LIMIT:
                    sample_size = min(len(chunk), _CHECK_LIMIT - bytes_read)
                    if b"\x00" in chunk[:sample_size]:
                        return 0
                    bytes_read += sample_size

                line_count += chunk.count(b"\n")
                last_chunk = chunk

            if last_chunk and not last_chunk.endswith(b"\n"):
                line_count += 1

            return line_count

    except Exception:
        return 0


# ****************************************************** SCANNING LOGIC *******************************************************


class DirectoryScanner:
    """Orchestrates multi-threaded directory traversal and line counting.\n
    ----------------------------------------------------------------------------------------------------
    *   `target_dir` – Root directory to scan.
    *   `skip_hidden` – Whether hidden and system items should be ignored.
    *   `apply_gitignore` – Whether .gitignore rules should be discovered and enforced.
    *   `is_recursive` – Whether subdirectories should be traversed recursively.
    *   `include_patterns` – Compiled glob patterns to filter included files.
    *   `exclude_patterns` – Compiled glob patterns to filter excluded files/directories.
    """

    target_dir: Path
    """Root directory where scanning started."""

    skip_hidden: bool
    """Whether to skip hidden and system files/directories."""

    apply_gitignore: bool
    """Whether to load and follow .gitignore rules."""

    is_recursive: bool
    """Whether to recurse into subdirectories."""

    include_patterns: list[tuple[re.Pattern[str], bool]]
    """Compiled patterns for inclusion filtering."""

    exclude_patterns: list[tuple[re.Pattern[str], bool]]
    """Compiled patterns for exclusion filtering."""

    total_lines: int
    """Accumulated total code lines count."""

    files_data: dict[str, int]
    """Mapping of relative file path strings to line counts."""

    extensions_data: dict[str, dict[str, int]]
    """Mapping of file extensions to counts of lines and files."""

    _lock: threading.Lock
    """Lock synchronizing data mutation across worker threads."""

    _done: threading.Event
    """Event signaling when all queued tasks have completed."""

    _active_tasks: list[int]
    """Single-element list storing active work counter."""

    _canceled: list[bool]
    """Single-element list storing cancellation state."""

    _executor: ThreadPoolExecutor
    """Thread pool executor running scan and count tasks."""

    def __init__(
        self,
        target_dir: Path,
        skip_hidden: bool,
        apply_gitignore: bool,
        is_recursive: bool,
        include_patterns: list[tuple[re.Pattern[str], bool]],
        exclude_patterns: list[tuple[re.Pattern[str], bool]],
    ) -> None:
        self.target_dir = target_dir
        self.skip_hidden = skip_hidden
        self.apply_gitignore = apply_gitignore
        self.is_recursive = is_recursive
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns

        self.total_lines = 0
        self.files_data = {}
        self.extensions_data = defaultdict(lambda: {"files": 0, "lines": 0})

        self._lock = threading.Lock()
        self._done = threading.Event()
        self._active_tasks = [1]
        self._canceled = [False]
        worker_count = min(64, (os.cpu_count() or 4) * 8)
        self._executor = ThreadPoolExecutor(max_workers=worker_count)

    def _process_entries(
        self,
        entries: list[os.DirEntry[str]],
        active_rules: list[GitIgnoreRule],
    ) -> tuple[list[str], list[tuple[str, str, str]]]:
        """Categorize directory entries into directories to visit and files to count.\n
        ----------------------------------------------------------------------------------------------------
        *   `entries` – List of scanned filesystem directory entries.
        *   `active_rules` – Git ignore rules applicable to this directory level.
        """

        new_dirs: list[str] = []
        file_tasks: list[tuple[str, str, str]] = []

        for entry in entries:
            entry_path_obj = Path(entry.path)
            try:
                rel_posix = entry_path_obj.relative_to(self.target_dir).as_posix()
            except ValueError:
                rel_posix = entry.name

            if entry.is_dir(follow_symlinks=False):
                if self.is_recursive and not should_skip_directory(
                    entry,
                    rel_posix,
                    self.skip_hidden,
                    self.apply_gitignore,
                    active_rules,
                    self.exclude_patterns,
                ):
                    new_dirs.append(entry.path)
            elif entry.is_file(follow_symlinks=False) and should_include_file(
                entry,
                rel_posix,
                self.skip_hidden,
                self.apply_gitignore,
                active_rules,
                self.include_patterns,
                self.exclude_patterns,
            ):
                extension = Path(entry.name).suffix.lower() or "(no ext)"
                file_tasks.append((entry.path, rel_posix, extension))

        return new_dirs, file_tasks

    def _count_lines_worker(self, file_path: str, rel_path: str, extension: str) -> None:
        """Worker task to count lines in a file and record statistics.\n
        ----------------------------------------------------------------------------------------------------
        *   `file_path` – Full path to the file.
        *   `rel_path` – Relative path from the target directory.
        *   `extension` – Lowercase file extension.
        """

        if not self._canceled[0]:
            lines = count_lines(file_path)
            with self._lock:
                self.total_lines += lines
                self.files_data[rel_path] = lines
                stats = self.extensions_data[extension]
                stats["files"] += 1
                stats["lines"] += lines

        with self._lock:
            self._active_tasks[0] -= 1
            if self._active_tasks[0] == 0:
                self._done.set()

    def _scan_dir_worker(self, dir_path: str, current_rules: list[GitIgnoreRule]) -> None:
        """Worker task to inspect a directory and dispatch child tasks.\n
        ----------------------------------------------------------------------------------------------------
        *   `dir_path` – Directory path to read.
        *   `current_rules` – Git ignore rules applicable to this directory level.
        """

        if self._canceled[0]:
            with self._lock:
                self._active_tasks[0] -= 1
                if self._active_tasks[0] == 0:
                    self._done.set()
            return

        try:
            with os.scandir(dir_path) as iterator:
                entries = list(iterator)
        except OSError:
            entries = []

        active_rules = current_rules
        if self.apply_gitignore:
            for entry in entries:
                if entry.name == ".gitignore":
                    active_rules = [*current_rules, *parse_gitignore_file(Path(entry.path))]
                    break

        new_dirs, file_tasks = self._process_entries(entries, active_rules)

        with self._lock:
            self._active_tasks[0] += len(new_dirs) + len(file_tasks)

        for next_directory in new_dirs:
            self._executor.submit(self._scan_dir_worker, next_directory, active_rules)

        for task_file_path, task_rel_posix, task_extension in file_tasks:
            self._executor.submit(self._count_lines_worker, task_file_path, task_rel_posix, task_extension)

        with self._lock:
            self._active_tasks[0] -= 1
            if self._active_tasks[0] == 0:
                self._done.set()

    def run(self) -> ScanResult:
        """Start the parallel scanning process and wait until complete."""

        base_rules = load_gitignore_rules(self.target_dir) if self.apply_gitignore else []

        try:
            self._executor.submit(self._scan_dir_worker, str(self.target_dir), base_rules)
            while not self._done.wait(0.05):
                pass
        except KeyboardInterrupt:
            self._canceled[0] = True
            raise
        finally:
            self._executor.shutdown(wait=False, cancel_futures=True)

        return ScanResult(
            total_lines=self.total_lines,
            total_files=len(self.files_data),
            files_data=self.files_data,
            extensions_data=dict(self.extensions_data),
        )


def scan_directory(target_dir: Path) -> ScanResult:
    """Scan the target directory recursively and compute line count statistics.\n
    ----------------------------------------------------------------------------------------------------
    *   `target_dir` – Root directory to scan.
    """

    include_patterns = (
        compile_glob_patterns(parse_glob_patterns(raw_val))
        if ARGS.include_patterns.exists and (raw_val := ARGS.include_patterns.val(default=""))
        else []
    )
    exclude_patterns = (
        compile_glob_patterns(parse_glob_patterns(raw_val))
        if ARGS.exclude_patterns.exists and (raw_val := ARGS.exclude_patterns.val(default=""))
        else []
    )

    scanner = DirectoryScanner(
        target_dir=target_dir,
        skip_hidden=not (ARGS.include_hidden.exists or ARGS.include_all.exists),
        apply_gitignore=not (ARGS.no_gitignore.exists or ARGS.include_all.exists),
        is_recursive=not ARGS.no_recursive.exists,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
    )
    return scanner.run()


# *********************************************************** MAIN ************************************************************


def main() -> None:
    """Execute the lines of code counter command."""

    raw_path = ARGS.target_dir.val()
    target_path = Path(raw_path).resolve() if raw_path else Path.cwd()

    if not target_path.exists():
        xx.console.fail(f"Path does not exist: {target_path}", start="\n", end="\n\n")
        raise SystemExit(1)

    if target_path.is_file():
        file_lines = count_lines(str(target_path))
        file_extension = target_path.suffix.lower() or "(no ext)"
        scan_result = ScanResult(
            total_lines=file_lines,
            total_files=1,
            files_data={target_path.name: file_lines},
            extensions_data={file_extension: {"files": 1, "lines": file_lines}},
        )
    else:
        if ARGS.raw_output.exists or ARGS.as_json.exists:
            scan_result = scan_directory(target_path)
        else:
            print()
            with Throbber(label="Counting lines of code...").context():
                scan_result = scan_directory(target_path)

    # [1] Raw numeric output:
    if ARGS.raw_output.exists:
        print(scan_result.total_lines)
        return

    # [2] Formatted JSON output:
    if ARGS.as_json.exists:
        json_data = {
            "target_dir": str(target_path),
            "total_lines": scan_result.total_lines,
            "total_files": scan_result.total_files,
            "extensions": scan_result.extensions_data,
            "files": scan_result.files_data,
        }
        print(xx.data.render(json_data, indent=2, as_json=True, syntax_highlighting=True).ansi)
        return

    # [3] Formatted banner output:
    file_count_formatted = f"{scan_result.total_files:,}"
    files_label = f"({file_count_formatted} file)" if scan_result.total_files == 1 else f"({file_count_formatted} files)"

    banner_content = S(
        (S.INVERSE | S.BG.BLACK)(
            "  ",
            S.BOLD(f"{scan_result.total_lines:,}"),
            " total lines  ",
            S.DIM(files_label),
            "  ",
        )
    )

    S(
        (Term.CLEAR_LINE, "▄" * (len(banner_content) + 2)),
        (banner_content, S.INVERSE("  ")),
        ("▀" * (len(banner_content) + 2)),
        sep="\n",
    ).print(end="\n\n")

    # [4] Detailed matched files list or extension breakdown:
    if ARGS.show_files.exists:
        if not scan_result.files_data:
            S.DIM("  No matching files found.").print(end="\n\n")
        else:
            sorted_files = sorted(scan_result.files_data.items(), key=lambda item: item[1], reverse=True)
            max_line_width = max((len(f"{line_num:,}") for _, line_num in sorted_files), default=0)
            file_rows: list[S] = [S(S.BOLD("  Matched Files:"), S.DIM(f" ({len(sorted_files)} files)\n"))]

            for file_path_key, file_line_count in sorted_files:
                formatted_count = f"{file_line_count:,}".rjust(max_line_width)
                file_rows.append(S("   ", S.BR.CYAN(formatted_count), "  ", S.DIM("lines"), "  ", S.WHITE(file_path_key)))

            S(*file_rows, sep="\n").print(end="\n\n")

    elif len(scan_result.extensions_data) > 1:
        sorted_extensions = sorted(
            scan_result.extensions_data.items(),
            key=lambda item: item[1]["lines"],
            reverse=True,
        )
        max_extension_width = max((len(ext_name) for ext_name, _ in sorted_extensions), default=0)
        max_lines_width = max((len(f"{data['lines']:,}") for _, data in sorted_extensions), default=0)

        extension_rows: list[S] = []
        for extension_name, extension_stats in sorted_extensions:
            lines_str = f"{extension_stats['lines']:,}".rjust(max_lines_width)
            padded_ext = extension_name.ljust(max_extension_width)
            count_label = "file" if extension_stats["files"] == 1 else "files"
            extension_rows.append(
                S(
                    "   ",
                    S.BR.BLUE(padded_ext),
                    "  ",
                    S.WHITE(lines_str),
                    " lines  ",
                    S.DIM(f"({extension_stats['files']:,} {count_label})"),
                )
            )

        S(*extension_rows, sep="\n").print(end="\n\n")


if __name__ == "__main__":
    args = ArgumentParser(
        title="Lines of Code",
        subtitle="Count total lines of code in a directory or project",
        controls=[("Ctrl+C", "Cancel and exit")],
        examples=[
            ("{cmd}", "Count lines of code in the current working directory"),
            ('{cmd} "my_project"', "Count lines in a specific directory"),
            ('{cmd} -i="*.py | *.toml"', "Count lines only in matching file patterns"),
            ('{cmd} -e="tests/** | build/**"', "Exclude files or directories matching patterns"),
            ("{cmd} -f", "Show list of all included files and their line counts"),
            ("{cmd} --json", "Output full statistics as formatted JSON"),
            ("{cmd} --raw", "Output only the raw total line count number"),
            ("{cmd} -H", "Include hidden and system files/directories"),
            ("{cmd} -ng", "Do not apply .gitignore ignore rules"),
            ("{cmd} -a", "Disable all ignore filters (hidden, system, and .gitignore)"),
        ],
    )

    args.add_arg("target_dir", required=False, help=("Target directory to count lines in ", S.DIM("(default: CWD)")))
    args.add_opt(
        {"-i", "--include"},
        "include_patterns",
        expects_value="PATTERNS",
        help=("Include only files matching glob patterns ", S.DIM("(e.g. ", S.WHITE("*.py | *.toml"), ")")),
    )
    args.add_opt(
        {"-e", "--exclude"},
        "exclude_patterns",
        expects_value="PATTERNS",
        help=("Exclude files or directories matching glob patterns ", S.DIM("(e.g. ", S.WHITE("tests/** | *.min.js"), ")")),
    )
    args.add_opt({"-ng", "--no-gitignore"}, help="Do not ignore files/directories specified in .gitignore")
    args.add_opt({"-H", "--hidden"}, "include_hidden", help="Do not ignore hidden and system files/directories")
    args.add_opt({"-a", "--all"}, "include_all", help="Disable all ignore filters (hidden, system, and .gitignore)")
    args.add_opt({"-nr", "--no-recursive"}, help="Do not scan subdirectories recursively")
    args.add_opt({"-f", "--files"}, "show_files", help="Show all matched files and their line counts")
    args.add_opt({"-j", "--json"}, "as_json", help="Output all gathered statistics as formatted JSON")
    args.add_opt({"-r", "--raw"}, "raw_output", help="Output only the bare total line count number")

    global ARGS
    ARGS = args.parse()

    try:
        main()
    except KeyboardInterrupt:
        S(Term.CLEAR_LINE, S.RESET, S.BR.RED("✗ Canceled by user.")).print(end="\n\n")
    except Exception as exc:
        xx.console.fail(exc, start="\n", end="\n\n")
