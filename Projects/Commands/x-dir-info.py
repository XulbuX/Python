import os
import math
import sys
from concurrent.futures import ThreadPoolExecutor


ARGS = sys.argv[1:]
IGNORE = {item.lower() for item in (ARGS[1:] if ARGS and ARGS[0] in ['-i', '--ignore'] else [])}



def print_overwrite(text: str, end='\n'):
    print('\033[2K\r' + text, end=end, flush=True)

def get_dir_files(directory: str) -> list:
    found_files = []
    for root, _, files in os.walk(directory):
        found_files.extend(os.path.join(root, file) for file in files)
    return found_files

def count_lines(file_path: str) -> int:
    try:
        with open(file_path, 'rb') as f:
            return sum(1 for _ in f)
    except:
        return 0

def process_file(file_path: str) -> tuple[int, int, int]:
    lines = 0 if 'scope' in IGNORE else count_lines(file_path)
    size = 0 if 'size' in IGNORE else os.path.getsize(file_path)
    return 1, lines, size

def calc_files_scope(files: list) -> tuple[int, int, int]:
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_file, files))
    return map(sum, zip(*results))

def format_bytes_size(bytes: int) -> str:
    if bytes <= 0:
        return '0 B'
    size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    i = int(math.log(bytes, 1024))
    p = math.pow(1024, i)
    s = round(bytes / p, 2)
    return f'{s} {size_name[i]}'

def main():
    print_overwrite('searching files...', end='')
    files = get_dir_files(os.getcwd())
    print_overwrite('calculating scope...', end='')
    files_count, files_scope, files_size = calc_files_scope(files)
    files_size = format_bytes_size(files_size)

    info = f' TOTAL FILES: {files_count}'
    if 'scope' not in IGNORE:
        info += f'  |  FILES SCOPE: {files_scope} lines'
    if 'size' not in IGNORE:
        info += f'  |  FILES SIZE: {files_size}'
    
    print_overwrite(f"{'#' * ((len(info) - 16) // 2)} CALCULATED INFO {'#' * ((len(info) - 16) // 2)}")
    print(info, flush=True)

if __name__ == "__main__":
    main()