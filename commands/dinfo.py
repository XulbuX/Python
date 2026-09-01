#!/usr/bin/env python3
# x-cmds:file[update]
"""Get detailed information about files in the current directory."""

import fnmatch
import math
import os
import re
import stat
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import xulbux as xx
from xulbux import ArgumentParser, S, Term, Throbber

EXCLUDE: set[str] = set()
TEXT_BYTES: bytes = bytes(range(32, 127)) + bytes([9, 10, 13])


def is_hidden_entry(entry: os.DirEntry[str]) -> bool:
    """Check if a file or directory is hidden, system, or protected."""

    if os.name == "nt":
        try:
            attrs = entry.stat(follow_symlinks=False).st_file_attributes
            if entry.is_dir(follow_symlinks=False):
                return bool(attrs & stat.FILE_ATTRIBUTE_HIDDEN)
            return bool(attrs & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM))
        except (AttributeError, OSError):
            pass

    else:
        path = entry.path
        system_dirs = {"/proc", "/sys", "/dev", "/tmp"}
        return path in system_dirs or any(path.startswith(d) for d in system_dirs)

    return False


def should_skip_entry(entry: os.DirEntry[str]) -> bool:
    """Check if an entry should be skipped based on skip options."""

    return bool(ARGS.skip_hidden.exists and is_hidden_entry(entry))


def load_gitignore_patterns(directory: str) -> list[tuple[re.Pattern[str], bool]]:
    """Load and pre-compile .gitignore patterns from the given directory and parent directories."""

    patterns: list[tuple[re.Pattern[str], bool]] = []
    current_dir = Path(directory).resolve()

    for parent in [current_dir, *list(current_dir.parents)]:
        gitignore_path = parent / ".gitignore"

        if gitignore_path.exists():
            try:
                with open(gitignore_path, encoding="utf-8", errors="ignore") as file:
                    for line in file:
                        if not (line := line.strip()) or line.startswith("#"):
                            continue

                        is_dir = line.endswith("/")
                        clean = line.rstrip("/")

                        full = str(parent / clean[1:]) if clean.startswith("/") else str(parent / clean)

                        try:
                            flags = re.IGNORECASE if os.name == "nt" else 0
                            patterns.append((re.compile(fnmatch.translate(full), flags), is_dir))
                        except re.error:
                            pass

            except (OSError, UnicodeDecodeError):
                continue

    return patterns


def is_gitignored(file_path: str, patterns: list[tuple[re.Pattern[str], bool]]) -> bool:
    """Check if a file should be ignored based on pre-compiled .gitignore patterns."""

    if not patterns:
        return False

    resolved = Path(file_path).resolve()
    path_is_dir = resolved.is_dir()

    for regex, dir_only in patterns:
        if dir_only and not path_is_dir:
            continue
        if regex.match(str(resolved)):
            return True
        if not dir_only:
            for parent in resolved.parents:
                if regex.match(str(parent)):
                    return True

    return False


def count_lines(file_path: str) -> int:
    """Count the number of lines in a file, returning 0 for binary files or errors."""

    try:
        with open(file_path, "rb") as file:
            if (file_size := Path(file_path).stat().st_size) == 0:
                return 0
            if file_size < 1024 * 1024:
                content = file.read()
                if b"\x00" in content:
                    return 0
                return content.count(b"\n")

            lines = 0
            bytes_checked = 0
            is_text_confirmed = False
            check_limit = 2048
            buffer_size = 65536

            while True:
                if not (chunk := file.read(buffer_size)):
                    break

                if not is_text_confirmed and bytes_checked < check_limit:
                    check_end = min(len(chunk), check_limit - bytes_checked)
                    sample = chunk[:check_end]

                    if b"\x00" in sample:
                        return 0

                    bytes_checked += check_end
                    if bytes_checked >= check_limit:
                        is_text_confirmed = True
                        if len(sample.translate(None, TEXT_BYTES)) / len(sample) > 0.4:
                            return 0

                lines += chunk.count(b"\n")

            return lines

    except Exception:
        return 0


def scan_and_calc_scope(directory: str) -> tuple[int, int, int]:  # ruff:ignore[complex-structure]
    """Recursively scan directory and calculate total files, lines, and size in bytes in parallel."""

    total_files = 0
    total_lines = 0
    total_size = 0

    gitignore_patterns = load_gitignore_patterns(directory) if ARGS.apply_gitignore.exists else []

    lock = threading.Lock()
    done = threading.Event()
    active = [1]
    canceled = [False]

    def _count_lines_task(file_path: str) -> None:
        if not canceled[0]:
            lines = count_lines(file_path)
            with lock:
                nonlocal total_lines
                total_lines += lines
        with lock:
            active[0] -= 1
            if active[0] == 0:
                done.set()

    def _scan(dir_path: str) -> None:  # ruff:ignore[complex-structure]
        if canceled[0]:
            with lock:
                active[0] -= 1
                if active[0] == 0:
                    done.set()
            return

        try:
            with os.scandir(dir_path) as it:
                entries = list(it)
        except OSError:
            entries = []

        new_dirs: list[str] = []
        local_files = 0
        local_size = 0
        lines_tasks: list[str] = []

        for entry in entries:
            if should_skip_entry(entry):
                continue

            entry_path = entry.path

            if ARGS.apply_gitignore.exists and is_gitignored(entry_path, gitignore_patterns):
                continue

            if entry.is_dir(follow_symlinks=False):
                if ARGS.recursive.exists:
                    new_dirs.append(entry_path)
            elif entry.is_file(follow_symlinks=False):
                local_files += 1

                try:
                    size = entry.stat(follow_symlinks=False).st_size
                except OSError:
                    size = 0

                if "size" not in EXCLUDE:
                    local_size += size

                if "lines" not in EXCLUDE and size > 0:
                    lines_tasks.append(entry_path)

        with lock:
            nonlocal total_files, total_size
            total_files += local_files
            total_size += local_size

            active[0] += len(new_dirs) + len(lines_tasks)

        for d in new_dirs:
            executor.submit(_scan, d)

        for f in lines_tasks:
            executor.submit(_count_lines_task, f)

        with lock:
            active[0] -= 1
            if active[0] == 0:
                done.set()

    max_workers = min(64, (os.cpu_count() or 4) * 8)
    executor = ThreadPoolExecutor(max_workers=max_workers)

    try:
        executor.submit(_scan, directory)
        while not done.wait(0.1):
            pass
    except KeyboardInterrupt:
        canceled[0] = True
        raise
    finally:
        executor.shutdown(wait=False)

    return total_files, total_lines, total_size


def format_bytes_size(bytes: int) -> str:
    """Format bytes into a human-readable string."""

    if bytes <= 0:
        return "0 B"

    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    size_idx = int(math.log(bytes, 1024))

    return f"{round(bytes / math.pow(1024, size_idx), 2)} {size_name[size_idx]}"


def main() -> None:
    EXCLUDE = {item.lower() for item in ARGS.exclude_info.val(default="").split()}

    print()

    with Throbber(label="Scanning directory tree...").context():
        files_count, files_line_count, files_size = scan_and_calc_scope(str(Path.cwd()))

    info_parts = S((S.INVERSE | S.BG.BLACK)("  ", S.BOLD(f"{files_count:,}"), " total files"))

    if "size" not in EXCLUDE:
        info_parts += (S.INVERSE | S.BG.BLACK)("  ", S.BOLD(format_bytes_size(files_size)), " total size")
    if "lines" not in EXCLUDE:
        info_parts += (S.INVERSE | S.BG.BLACK)("  ", S.BOLD(f"{files_line_count:,}"), " total lines")

    S(
        (Term.CLEAR_LINE, "▄" * (len(info_parts) + 2)),
        (info_parts, S.INVERSE("  ")),
        ("▀" * (len(info_parts) + 2)),
        sep="\n",
    ).print(end="\n\n")


if __name__ == "__main__":
    args = ArgumentParser(
        title="Directory Info",
        subtitle="Get details about files in the current directory",
        controls=[("Ctrl+C", "Cancel and exit")],
        examples=[
            ("{cmd}", "Get all directory info, not ignoring any items"),
            ('{cmd} -e="size lines"', "Only show file count, excluding size and line count"),
            ("{cmd} --skip-hidden", "Skip hidden and system items"),
            ("{cmd} --gitignore", "Apply .gitignore rules when scanning files"),
        ],
    )

    args.add_opt({"-r", "--recursive"}, help="Also scan all subdirectories recursively")
    args.add_opt(
        {"-e", "--exclude"},
        "exclude_info",
        expects_value="S",
        help=(
            "Exclude parts of the info ",
            S.DIM("(", S.ITALIC("size"), ", ", S.ITALIC("lines"), "; count is always included)"),
        ),
    )
    args.add_opt({"-H", "--skip-hidden"}, help="Skip hidden, system, and protected items")
    args.add_opt(
        {"-G", "--gitignore"},
        "apply_gitignore",
        help=("Apply ", S.WHITE(".gitignore"), " rules when scanning files"),
    )

    global ARGS
    ARGS = args.parse()

    try:
        main()
    except KeyboardInterrupt:
        S(Term.CLEAR_LINE, S.RESET, S.BR.RED("✗ Canceled by user.")).print(end="\n\n")
    except Exception as exc:
        xx.console.fail(exc, start="\n", end="\n\n")
