#!/usr/bin/env python3
"""Gives details about the files in the current directory.
Information can be ignored, since it can take quite long to calculate."""
from xulbux import FormatCodes, ProgressBar, Console
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from typing import Callable
import math
import sys
import os


ARGS = sys.argv[1:]  # [ignore_info: [-i, --ignore]]
IGNORE = {item.lower() for item in (ARGS[1:] if ARGS and ARGS[0] in ("-i", "--ignore") else [])}


def print_overwrite(text: str, end="\n"):
    FormatCodes.print("\033[2K\r" + text, end=end)


def get_dir_files(directory: str) -> list:
    """Recursively get the paths of all files in a directory."""
    files = []
    try:
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                files.append(os.path.join(root, filename))
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
        if "size" in IGNORE and "scope" in IGNORE:
            return 1, 0, 0
        size = os.path.getsize(file_path)
        if "scope" in IGNORE: lines = 0
        elif size == 0: lines = 0
        else: lines = count_lines(file_path)
        return 1, lines, 0 if "size" in IGNORE else size
    except:
        return 1, 0, 0


def calc_files_scope(files: list, update_progress: Callable[[int], None]) -> tuple[int, int, int]:
    cpu_count = os.cpu_count() or 4
    if len(files) < 50:
        max_workers = min(len(files), cpu_count)
    else:
        max_workers = min(cpu_count * 3, len(files), 128)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {executor.submit(process_file, file_path): i for i, file_path in enumerate(files)}
        total_files = 0
        total_lines = 0
        total_size = 0
        completed = 0
        for future in as_completed(future_to_index):
            file_count, lines, size = future.result()
            total_files += file_count
            total_lines += lines
            total_size += size
            completed += 1
            if completed % 100 == 0 or completed == len(files):
                update_progress(completed)
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
    print_overwrite("[dim](searching files...)", end="")
    files = get_dir_files(os.getcwd())

    if "scope" in IGNORE and "size" in IGNORE:
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
    info_parts = [f"[b](TOTAL FILES:) {files_count:,}"]
    if "scope" not in IGNORE:
        info_parts.append(f"[b](FILES SCOPE:) {files_scope:,} lines")
    if "size" not in IGNORE:
        info_parts.append(f"[b](FILES SIZE:) {files_size}")
    info = "  [dim](|)  ".join(info_parts)

    print_overwrite(f"\n{info}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
