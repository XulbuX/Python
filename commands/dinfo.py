#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Get detailed information about files in the current directory."""
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from pathlib import Path
from xulbux.base.types import ProgressUpdater
from xulbux.console import ProgressBar, Throbber
from xulbux import FormatCodes, Console
import fnmatch
import math
import re
import stat
import os


ARGS = Console.get_args({
    "recursive": {"-r", "--recursive"},
    "exclude_info": {"-e", "--exclude"},
    "skip_hidden": {"-H", "--skip-hidden"},
    "apply_gitignore": {"-G", "--gitignore"},
    "help": {"-h", "--help"},
})

EXCLUDE: set[str] = {item.lower() for item in ARGS.exclude_info.get(0, "").split()}
TEXT_BYTES: bytes = bytes(range(32, 127)) + bytes([9, 10, 13])


def print_help():
    help_text = """
[b|in|bg:black]( Directory Info — Get details about files in the current directory )

[b](Usage:) [br:green](dinfo) [br:blue]([options])

[b](Options:)
  [br:blue](-r), [br:blue](--recursive)      Also scan all subdirectories recursively
  [br:blue](-e), [br:blue](--exclude[dim](=)S)      Exclude parts of the info [dim]((scope, size — count is always included))
  [br:blue](-H), [br:blue](--skip-hidden)    Skip hidden, system, and protected items
  [br:blue](-G), [br:blue](--gitignore)      Apply .gitignore rules when scanning files

[b](Examples:)
  [br:green](dinfo)                    [dim](# [i](Get all directory info, not ignoring any items))
  [br:green](dinfo) [br:blue](-e[dim](=)"scope size")    [dim](# [i](Only show file count, excluding scope and size))
  [br:green](dinfo) [br:blue](--skip-hidden)      [dim](# [i](Skip hidden and system items))
  [br:green](dinfo) [br:blue](--gitignore)        [dim](# [i](Apply .gitignore rules when scanning files))
"""
    FormatCodes.print(help_text)


def is_hidden(path: str) -> bool:
    """Check if a file or directory is hidden, system, or protected."""
    if os.name == "nt":
        try:
            attrs = Path(path).stat().st_file_attributes
            if attrs & stat.FILE_ATTRIBUTE_DIRECTORY:
                return bool(attrs & stat.FILE_ATTRIBUTE_HIDDEN)
            return bool(attrs & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM))
        except (AttributeError, OSError):
            pass

    else:
        system_dirs = {"/proc", "/sys", "/dev", "/tmp"}
        return path in system_dirs or any(path.startswith(d) for d in system_dirs)

    return False


def should_skip_path(path: str) -> bool:
    """Check if a path should be skipped based on skip options."""
    if ARGS.skip_hidden.exists and is_hidden(path):
        return True
    else:
        return False


def load_gitignore_patterns(directory: str) -> list[tuple[re.Pattern[str], bool]]:
    """Load and pre-compile .gitignore patterns from the given directory and parent directories."""
    patterns: list[tuple[re.Pattern[str], bool]] = []
    current_dir = Path(directory).resolve()

    for parent in [current_dir] + list(current_dir.parents):
        gitignore_path = parent / ".gitignore"

        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as file:
                    for line in file:
                        if not (line := line.strip()) or line.startswith("#"):
                            continue

                        is_dir = line.endswith("/")
                        clean = line.rstrip("/")

                        if clean.startswith("/"):
                            full = str(parent / clean[1:])
                        else:
                            full = str(parent / clean)

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


def get_dir_files(directory: str) -> list[str]:
    """Get the paths of all files in a directory, optionally recursively."""
    files: list[str] = []
    gitignore_patterns = load_gitignore_patterns(directory) if ARGS.apply_gitignore.exists else []

    try:
        for root, dirs, filenames in Path(directory).walk():
            if not ARGS.recursive.exists:
                dirs.clear()
            else:
                dirs[:] = [dir for dir in dirs if not should_skip_path(str(root / dir))]
                if ARGS.apply_gitignore.exists:
                    dirs[:] = [dir for dir in dirs if not is_gitignored(str(root / dir), gitignore_patterns)]

            for filename in filenames:
                if should_skip_path(file_path := str(root / filename)):
                    continue
                if ARGS.apply_gitignore.exists and is_gitignored(file_path, gitignore_patterns):
                    continue
                files.append(file_path)

    except PermissionError:
        pass

    return files


def count_lines(file_path: str) -> int:
    try:
        with open(file_path, "rb") as file:
            if (file_size := Path(file_path).stat().st_size) == 0:
                return 0
            if file_size < 1024 * 1024:
                content = file.read()
                if b"\x00" in content: return 0
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

    except:
        return 0


def process_file(file_path: str) -> tuple[int, int, int]:
    try:
        if "size" in EXCLUDE and "scope" in EXCLUDE:
            return 1, 0, 0

        size = Path(file_path).stat().st_size

        if "scope" in EXCLUDE:
            lines = 0
        elif size == 0:
            lines = 0
        else:
            lines = count_lines(file_path)

        return 1, lines, 0 if "size" in EXCLUDE else size

    except:
        return 1, 0, 0


def calc_files_scope(files: list[str], update_progress: ProgressUpdater) -> tuple[int, int, int]:
    if not files:
        return 0, 0, 0

    cpu_count = os.cpu_count() or 4

    if len(files) < 50:
        max_workers = min(len(files), cpu_count)
    else:
        max_workers = min(cpu_count * 3, len(files), 128)

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {executor.submit(process_file, file_path): i for i, file_path in enumerate(files)}
            total_files = 0
            total_lines = 0
            total_size = 0
            completed = 0

            try:
                for future in as_completed(future_to_index):
                    file_count, lines, size = future.result()
                    total_files += file_count
                    total_lines += lines
                    total_size += size
                    completed += 1

                    if completed % 1221 == 0 or completed == len(files):
                        update_progress(completed)

            except KeyboardInterrupt:
                for future in future_to_index:
                    future.cancel()
                raise

    except KeyboardInterrupt:
        raise

    return total_files, total_lines, total_size


def format_bytes_size(bytes: int) -> str:
    if bytes <= 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.log(bytes, 1024))
    p = math.pow(1024, i)
    s = round(bytes / p, 2)
    return f"{s} {size_name[i]}"


def main():
    if ARGS.help.exists:
        print_help()
        return

    print()

    with Throbber(label="Searching items").context():
        files = get_dir_files(str(Path.cwd()))

    if "scope" in EXCLUDE and "size" in EXCLUDE:
        files_count = len(files)
        files_scope = 0
        files_size = 0

    else:
        if len(files) >= 100:
            with ProgressBar().progress_context(len(files), "Calculating scope...") as update_progress:
                update_progress(0)
                files_count, files_scope, files_size = calc_files_scope(files, update_progress)

        else:
            files_count, files_scope, files_size = calc_files_scope(files, lambda current=None, label=None: None)

    files_size = format_bytes_size(files_size)
    info_parts = [f"[b|bg:black]([in]( TOTAL FILES: ) {files_count:,} )"]

    if "scope" not in EXCLUDE:
        info_parts.append(f"[b|bg:black]([in]( FILES SCOPE: ) {files_scope:,} lines )")
    if "size" not in EXCLUDE:
        info_parts.append(f"[b|bg:black]([in]( FILES SIZE: ) {files_size} )")
    info = "".join(info_parts)

    FormatCodes.print(f"\033[2K\r{info}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        FormatCodes.print("\033[2K\r[b|br:red](✗)\n")
    except Exception as exc:
        Console.fail(exc, start="\n", end="\n\n")
