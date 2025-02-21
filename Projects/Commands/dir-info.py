from concurrent.futures import ThreadPoolExecutor
from xulbux import Console
import math
import mmap
import sys
import os


ARGS = sys.argv[1:]
IGNORE = {item.lower() for item in (ARGS[1:] if ARGS and ARGS[0] in ("-i", "--ignore") else [])}
TEXT_EXTENSIONS = {'.txt', '.py', '.js', '.css', '.html', '.md', '.json', '.xml', '.csv', '.log', '.ini', '.cfg', '.conf'}


def print_overwrite(text: str, end="\n"):
    print("\033[2K\r" + text, end=end, flush=True)


def get_dir_files(directory: str) -> list:
    files = []
    try:
        for entry in os.scandir(directory):
            if entry.is_file():
                files.append(entry.path)
            elif entry.is_dir():
                files.extend(get_dir_files(entry.path))
    except PermissionError:
        pass
    return files


def count_lines(file_path: str) -> int:
    if not os.path.splitext(file_path)[1].lower() in TEXT_EXTENSIONS:
        return 0
    try:
        with open(file_path, "rb") as f:
            buf = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            lines = 0
            for _ in iter(buf.readline, b""):
                lines += 1
            buf.close()
            return lines
    except:
        try:
            with open(file_path, "rb") as f:
                return sum(1 for _ in f)
        except:
            return 0


def process_file(file_path: str) -> tuple[int, int, int]:
    try:
        lines = 0 if "scope" in IGNORE else count_lines(file_path)
        size = 0 if "size" in IGNORE else os.path.getsize(file_path)
        return 1, lines, size
    except:
        return 1, 0, 0


def calc_files_scope(files: list) -> tuple[int, int, int]:
    with ThreadPoolExecutor(max_workers=min(32, len(files))) as executor:
        results = list(executor.map(process_file, files, chunksize=10))
    return map(sum, zip(*results))


def format_bytes_size(bytes: int) -> str:
    if bytes <= 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.log(bytes, 1024))
    p = math.pow(1024, i)
    s = round(bytes / p, 2)
    return f"{s} {size_name[i]}"


def main():
    print_overwrite("searching files...", end="")
    files = get_dir_files(os.getcwd())
    print_overwrite("calculating scope...", end="")
    files_count, files_scope, files_size = calc_files_scope(files)
    files_size = format_bytes_size(files_size)
    info_parts = ["TOTAL FILES: " + str(files_count)]
    if "scope" not in IGNORE:
        info_parts.append("FILES SCOPE: " + str(files_scope) + " lines")
    if "size" not in IGNORE:
        info_parts.append("FILES SIZE: " + files_size)
    info = "  |  ".join(info_parts)
    border = "#" * ((len(info) - 16) // 2)
    print_overwrite(f"{border} CALCULATED INFO {border}")
    print(info, flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
