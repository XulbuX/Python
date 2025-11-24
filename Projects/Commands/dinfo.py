#!/usr/bin/env python3
"""Get detailed information about files in the current directory."""
from xulbux.console import Spinner
from xulbux import FormatCodes, ProgressBar, Console
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from typing import Callable
from pathlib import Path
import fnmatch
import math
import stat
import os


ARGS = Console.get_args(
    {
        "recursive": {"-r", "--recursive"},
        "exclude_info": {"-e", "--exclude"},
        "skip_type": {"-s", "--skip"},
        "apply_gitignore": {"-g", "--gitignore"},
        "help": {"-h", "--help"},
    },
    allow_spaces=True,
)
EXCLUDE = {item.lower() for item in str(ARGS.exclude_info.value).split()}
SKIP = {item.lower() for item in str(ARGS.skip_type.value).split()} if ARGS.skip_type.exists else set()


def print_help():
    help_text = """
[b|in|bg:black]( Directory Info - Get details about files in the current directory )

[b](Usage:) [br:green](x-qr) [br:blue]([options])

[b](Options:)
  [br:blue](-r), [br:blue](--recursive)    Also scan all subdirectories recursively
  [br:blue](-e), [br:blue](--exclude S)    Exclude parts of the info [dim]((scope, size))
  [br:blue](-s), [br:blue](--skip S)       Skip hidden and/or system items [dim]((hidden, system))
  [br:blue](-g), [br:blue](--gitignore)    Apply .gitignore rules when scanning files

[b](Examples:)
  [br:green](dinfo)                         [dim](# [i](Get all directory info, not ignoring any items))
  [br:green](dinfo) [br:blue](-e 'scope')              [dim](# [i](Exclude scope info))
  [br:green](dinfo) [br:blue](-s 'hidden' 'system')    [dim](# [i](Skip hidden and system items))
  [br:green](dinfo) [br:blue](--gitignore)             [dim](# [i](Apply .gitignore rules when scanning files))
"""
    FormatCodes.print(help_text)


def is_hidden(path: str) -> bool:
    """Check if a file or directory is hidden."""
    name = os.path.basename(path)
    if name.startswith("."):
        return True
    if os.name == "nt":
        try:
            attrs = os.stat(path).st_file_attributes
            return bool(attrs & stat.FILE_ATTRIBUTE_HIDDEN)
        except (AttributeError, OSError):
            pass
    return False


def is_system(path: str) -> bool:
    """Check if a file or directory is a system file."""
    if os.name == "nt":
        try:
            attrs = os.stat(path).st_file_attributes
            return bool(attrs & stat.FILE_ATTRIBUTE_SYSTEM)
        except (AttributeError, OSError):
            pass
    system_dirs = {"/proc", "/sys", "/dev", "/tmp"}
    return path in system_dirs or any(path.startswith(d) for d in system_dirs)


def should_skip_path(path: str) -> bool:
    """Check if a path should be skipped based on skip options."""
    if "hidden" in SKIP and is_hidden(path):
        return True
    if "system" in SKIP and is_system(path):
        return True
    return False


def load_gitignore_patterns(directory: str) -> list:
    """Load .gitignore patterns from the given directory and parent directories."""
    patterns = []
    current_dir = Path(directory).resolve()

    for parent in [current_dir] + list(current_dir.parents):
        gitignore_path = parent / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.append((str(parent), line))
            except (OSError, UnicodeDecodeError):
                continue

    return patterns


def is_gitignored(file_path: str, patterns: list) -> bool:
    """Check if a file should be ignored based on .gitignore patterns."""
    if not patterns:
        return False

    file_path = os.path.abspath(file_path)

    for gitignore_dir, pattern in patterns:
        if pattern.startswith("/"):
            full_pattern = os.path.join(gitignore_dir, pattern[1:])
        else:
            full_pattern = os.path.join(gitignore_dir, pattern)

        full_pattern = os.path.normpath(full_pattern)

        if pattern.endswith("/"):
            if os.path.isdir(file_path) and (fnmatch.fnmatch(file_path, full_pattern)
                                             or fnmatch.fnmatch(file_path + os.sep, full_pattern)):
                return True
        else:
            if fnmatch.fnmatch(file_path, full_pattern):
                return True
            parent = file_path
            while parent != os.path.dirname(parent):
                parent = os.path.dirname(parent)
                if fnmatch.fnmatch(parent, full_pattern):
                    return True

    return False


def get_dir_files(directory: str) -> list:
    """Get the paths of all files in a directory, optionally recursively."""
    files = []
    gitignore_patterns = load_gitignore_patterns(directory) if ARGS.apply_gitignore.exists else []

    try:
        for root, dirs, filenames in os.walk(directory):
            if should_skip_path(root):
                dirs.clear()
                continue
            if ARGS.apply_gitignore.exists and is_gitignored(root, gitignore_patterns):
                dirs.clear()
                continue

            if not ARGS.recursive.exists:
                dirs.clear()
            else:
                dirs[:] = [d for d in dirs if not should_skip_path(os.path.join(root, d))]
                if ARGS.apply_gitignore.exists:
                    dirs[:] = [d for d in dirs if not is_gitignored(os.path.join(root, d), gitignore_patterns)]

            for filename in filenames:
                file_path = os.path.join(root, filename)
                if should_skip_path(file_path):
                    continue
                if ARGS.apply_gitignore.exists and is_gitignored(file_path, gitignore_patterns):
                    continue
                files.append(file_path)
    except PermissionError:
        pass
    return files


def count_lines(file_path: str) -> int:
    try:
        with open(file_path, "rb") as f:
            file_size = os.path.getsize(file_path)
            if file_size == 0: return 0
            if file_size < 1024 * 1024:
                content = f.read()
                if b"\x00" in content: return 0
                return content.count(b"\n")
            lines = 0
            bytes_checked = 0
            is_text_confirmed = False
            check_limit = 2048
            buffer_size = 65536
            while True:
                chunk = f.read(buffer_size)
                if not chunk: break
                if not is_text_confirmed and bytes_checked < check_limit:
                    check_end = min(len(chunk), check_limit - bytes_checked)
                    sample = chunk[:check_end]
                    if b"\x00" in sample: return 0
                    bytes_checked += check_end
                    if bytes_checked >= check_limit:
                        is_text_confirmed = True
                        printable = sum(1 for byte in sample if 32 <= byte <= 126 or byte in (9, 10, 13))
                        if printable / len(sample) < 0.6:
                            return 0
                lines += chunk.count(b"\n")
            return lines
    except:
        return 0


def process_file(file_path: str) -> tuple[int, int, int]:
    try:
        if "size" in EXCLUDE and "scope" in EXCLUDE:
            return 1, 0, 0
        size = os.path.getsize(file_path)
        if "scope" in EXCLUDE: lines = 0
        elif size == 0: lines = 0
        else: lines = count_lines(file_path)
        return 1, lines, 0 if "size" in EXCLUDE else size
    except:
        return 1, 0, 0


def calc_files_scope(files: list, update_progress: Callable[[int], None]) -> tuple[int, int, int]:
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
                    if completed % 101 == 0 or completed == len(files):
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

    with Spinner("Searching items").context():
        files = get_dir_files(os.getcwd())

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
            files_count, files_scope, files_size = calc_files_scope(files, lambda x: None)

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
        FormatCodes.print("\033[2K\r[b|br:red](⨯)\n")
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
