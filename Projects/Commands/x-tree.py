from functools import lru_cache
from itertools import chain
from typing import Optional, Pattern
import xulbux as xx
import sys
import os
import re


ARGS = sys.argv[1:]
DEFAULTS = {
    "ignore_dirs": [],
    "auto_ignore": True,
    "file_contents": False,
    "tree_style": 1,
    "indent": 3,
    "into_file": False,
}


class Tree:

    HASH_PATTERNS: list[Pattern] = [
        re.compile(pattern) for pattern in [
            r"^[a-fA-F0-9]{32}$",  # MD5
            r"^[a-fA-F0-9]{40}$",  # SHA-1
            r"^[a-fA-F0-9]{64}$",  # SHA-256
            r"^[a-fA-F0-9]{128}$",  # SHA-512
            r"^[a-fA-F0-9]{8,}_\d+$",  # PATTERN LIKE 'da4880697ffe4e19_0'
            r"^[0-9a-fA-F]{2}$",  # TWO-CHARACTER HEX
            r"^[X0-9a-fA-F]{32,}$",  # PATTERN WITH X PREFIX
            r"^\d+[a-fA-F0-9]{16,}$",  # NUMBER FOLLOWED BY HASH
        ]
    ]
    HEX_DIR_PATTERN = re.compile(r"^[a-fA-F0-9]{2}$")
    BINARY_EXTENSIONS = frozenset({
        ".exe", ".dll", ".so", ".dylib", ".bin", ".dat", ".db", ".sqlite", ".jpg", ".jpeg", ".png", ".gif", ".ico", ".cur",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".tar", ".gz", ".7z", ".rar", ".mp3", ".mp4", ".avi", ".mov"
    })
    DEFAULT_IGNORE_DIRS = [
        "$RECYCLE.BIN", ".git", "node_modules", "__pycache__", "env", "venv", ".env", ".venv", "build", "dist", "cache",
        "Code Cache", "target", "bin", "obj", ".idea", ".vscode", ".vs", "coverage", "logs", "log", "tmp", "temp", ".next",
        ".nuxt", "out", ".output", ".cache", "vendor", "packages", ".terraform", ".angular", ".svn", "CVS", ".hg",
        ".pytest_cache", ".coverage", "htmlcov", ".tox", "site-packages", ".DS_Store", "bower_components", ".sass-cache",
        ".parcel-cache", ".webpack", ".gradle", ".mvn", "Pods", "xcuserdata", "junit", "reports", ".github", ".gitlab",
        "docker", ".docker", ".kube", "node", "jspm_packages", ".npm", "artifacts", ".yarn", "wheels", "docs/_build", "_site",
        ".jekyll-cache", ".ipynb_checkpoints", ".mypy_cache", ".pytest_cache", "celerybeat-schedule", ".sonar", ".scannerwork",
        "migrations", "__tests__", "test-results", "coverage-reports", ".nx", "dist-newstyle", "target", "Debug", "Release",
        "x64", "x86"
    ]

    def __init__(
        self,
        base_dir: Optional[str] = None,
        ignore_dirs: Optional[list[str]] = None,
        auto_ignore: Optional[bool] = True,
        include_file_contents: Optional[bool] = False,
        style: Optional[int] = 1,
        indent: Optional[int] = 3,
    ):
        self.base_dir = base_dir
        self.ignore_dirs = ignore_dirs
        self.auto_ignore = auto_ignore
        self.include_file_contents = include_file_contents
        self.style = style
        self.indent = indent
        self.ignore_set = None
        self.style_presets = {
            1: {
                "line_ver": "│",
                "line_hor": "─",
                "branch_new": "├",
                "corners": ["└", "┘", "┐"],
                "error": "⚠",
                "skipped": "...",
                "dirname_end": "/",
            },
            2: {
                "line_ver": "│",
                "line_hor": "─",
                "branch_new": "├",
                "corners": ["╰", "╯", "╮"],
                "error": "⚠",
                "skipped": "...",
                "dirname_end": "/",
            },
            3: {
                "line_ver": "┃",
                "line_hor": "━",
                "branch_new": "┣",
                "corners": ["┗", "┛", "┓"],
                "error": "⚠",
                "skipped": "...",
                "dirname_end": "/",
            },
            4: {
                "line_ver": "║",
                "line_hor": "═",
                "branch_new": "╠",
                "corners": ["╚", "╝", "╗"],
                "error": "⚠",
                "skipped": "...",
                "dirname_end": "/",
            },
        }
        self._error_suffix = None
        self._skipped_suffix = None
        self._reset_style_attrs()

    def _reset_style_attrs(self) -> None:
        """Reset style attributes based on current style selection."""
        style_dict = self.style_presets.get(self.style, self.style_presets[1])
        self.line_ver = style_dict["line_ver"]
        self.line_hor = style_dict["line_hor"]
        self.branch_new = style_dict["branch_new"]
        self.corners = style_dict["corners"]
        self.error = style_dict["error"]
        self.skipped = style_dict["skipped"]
        self.dirname_end = style_dict["dirname_end"]
        self._error_suffix = f"{self.error} [Error: "
        self._skipped_suffix = f"{self.line_hor}{self.skipped}\n"

    def show_styles(self) -> None:
        for style, details in self.style_presets.items():
            print(
                f'{style}: {details["corners"][0]}{details["line_hor"]}{details["skipped"]}{details["dirname_end"]}',
                flush=True,
            )

    def _should_ignore_directory(self, dir_path: str) -> tuple[bool, int, int]:
        """Enhanced directory content analysis.
        Returns (should_ignore, total_count, hash_count) tuple."""
        if not self.auto_ignore:
            return False, 0, 0
        dir_name = os.path.basename(dir_path)
        likely_has_name = lambda name: any(pattern.match(name) for pattern in Tree.HASH_PATTERNS)
        if self.HEX_DIR_PATTERN.match(dir_name):
            try:
                entries = list(os.scandir(dir_path))
                if not entries:
                    return False, 0, 0
                hash_count = sum(1 for entry in entries if likely_has_name(entry.name))
                total_count = len(entries)
                return (hash_count / total_count > 0.7), total_count, hash_count
            except PermissionError:
                return False, 0, 0
        try:
            entries = list(os.scandir(dir_path))
            if not entries:
                return False, 0, 0
            hash_count = sum(1 for entry in entries
                             if likely_has_name(entry.name) or (entry.is_dir() and self.HEX_DIR_PATTERN.match(entry.name)))
            total_count = len(entries)
            return (hash_count / total_count > 0.8), total_count, hash_count
        except PermissionError:
            return False, 0, 0

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
        except:
            return False

    def generate(
        self,
        base_dir: Optional[str] = None,
        ignore_dirs: Optional[list[str]] = None,
        include_file_contents: Optional[bool] = None,
        style: Optional[int] = 1,
        indent: Optional[int] = 3,
        auto_ignore: Optional[bool] = None,
    ) -> str:
        self.base_dir = base_dir or self.base_dir
        self.ignore_dirs = ignore_dirs or self.ignore_dirs
        self.include_file_contents = include_file_contents or self.include_file_contents
        self.style = style or self.style
        self.indent = indent or self.indent
        self.auto_ignore = auto_ignore if auto_ignore is not None else self.auto_ignore
        self.base_dir = os.path.abspath(str(self.base_dir))
        if not os.path.isdir(self.base_dir):
            raise ValueError(f"Invalid base directory: {self.base_dir}")
        self.ignore_set = (frozenset() if self.ignore_dirs is None else frozenset(self.ignore_dirs))
        self._reset_style_attrs()
        return self._gen_tree(self.base_dir)

    def _gen_tree(
        self,
        _dir: str,
        _prefix: str = "",
        _level: int = 0,
    ) -> str:
        result = bytearray()
        try:
            tab = b" " * self.indent
            line_hor_mult = (self.indent - 2 if self.indent > 2 else 1 if self.indent == 2 else 0)
            line_hor = self.line_hor.encode() * line_hor_mult

            if _level == 0:
                base_dir_name = os.path.basename(_dir.rstrip(os.sep))
                if not base_dir_name:
                    base_dir_name = os.path.splitdrive(_dir)[0]
                result.extend(f"{base_dir_name}{self.dirname_end}\n".encode())

            entries = sorted(os.scandir(_dir), key=lambda e: e.name)
            if not entries:
                return result.decode()

            # Check if directory should be ignored
            should_ignore, _, _ = self._should_ignore_directory(_dir)
            if should_ignore:
                result.extend(_prefix.encode())
                result.extend(self.corners[0].encode())
                result.extend(self._skipped_suffix.encode())
                return result.decode()

            entries_count = len(entries)
            prefix_ver = _prefix.encode() + self.line_ver.encode() + tab[:-1]
            prefix_tab = _prefix.encode() + tab

            for idx, entry in enumerate(entries):
                is_last = idx == entries_count - 1
                is_dir = entry.is_dir()
                branch = self.corners[0] if is_last else self.branch_new
                current_prefix = _prefix.encode() + branch.encode() + line_hor

                if entry.name in self.ignore_set or (is_dir and self._should_ignore_directory(entry.path)[0]):
                    result.extend(current_prefix)
                    result.extend(entry.name.encode())
                    if is_dir:
                        result.extend(self.dirname_end.encode())
                        next_prefix = prefix_tab if is_last else prefix_ver
                        result.extend(b"\n")
                        result.extend(next_prefix)
                        result.extend(self.corners[0].encode())
                        result.extend(self._skipped_suffix.encode())
                    else:
                        result.extend(b"\n")
                    continue
                if is_dir:
                    result.extend(current_prefix)
                    result.extend(entry.name.encode())
                    result.extend(self.dirname_end.encode())
                    result.extend(b"\n")
                    new_prefix = _prefix + (" " * self.indent if is_last else self.line_ver + " " * (self.indent - 1))
                    result.extend(self._gen_tree(entry.path, new_prefix, _level + 1).encode())
                else:
                    result.extend(current_prefix)
                    result.extend(entry.name.encode())
                    result.extend(b"\n")
                    if self.include_file_contents and self._is_text_file(entry.path):
                        content_prefix = _prefix + (" " * self.indent if is_last else self.line_ver + " " * (self.indent - 1))
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
                                    result.extend(f"{content_prefix}{self.branch_new}{hor_border}{self.corners[2]}\n".encode())
                                    for line in lines:
                                        stripped = line.rstrip()
                                        padding = " " * (content_width - len(stripped))
                                        result.extend(
                                            f"{content_prefix}{self.line_ver} {stripped}{padding} {self.line_ver}\n".encode())
                                    result.extend(f"{content_prefix}{self.corners[0]}{hor_border}{self.corners[1]}\n".encode())
                        except:
                            result.extend(
                                f"{content_prefix}{self.corners[0]}{line_hor.decode()}{self._error_suffix}Error reading file contents]\n"
                                .encode())
        except Exception as e:
            error_prefix = (_prefix + self.corners[0] + (self.line_hor * (self.indent - 1)))
            result.extend(f"{error_prefix}{self._error_suffix}{str(e)}]\n".encode())
        return result.decode()


def main():
    tree = Tree(os.getcwd())

    if len(ARGS) > 1:
        if ARGS[0] in ("-i", "--ignore"):
            ignore_dirs = ARGS[1:]
        elif ARGS[1] in ("-i", "--ignore"):
            ignore_dirs = ARGS[2:]
    else:
        ignore_input = xx.FormatCodes.input(
            "Enter directories or files which's content should be ignore [dim]((`/` separated) >  )").strip()
        ignore_dirs = list(chain.from_iterable(item.split("/") for item in ignore_input.split("/")))

    file_contents = xx.FormatCodes.input(
        f'Display the file contents in the tree [dim]({"(Y/n)" if DEFAULTS["file_contents"] else "(y/N)"} >  )').strip().lower(
        ) in ("y", "yes")

    print("Enter the tree style (1-4): ")
    tree.show_styles()
    tree_style = xx.FormatCodes.input(f'[dim]([default is {DEFAULTS["tree_style"]}] >  )').strip()
    tree_style = (int(tree_style) if tree_style.isnumeric() and 1 <= int(tree_style) <= 4 else DEFAULTS["tree_style"])

    indent = xx.FormatCodes.input(f'Enter the indent [dim]([default is {DEFAULTS["indent"]}] >  )').strip()
    indent = (int(indent) if indent.isnumeric() and int(indent) >= 0 else DEFAULTS["indent"])

    auto_ignore = xx.FormatCodes.input(
        f'Enable auto-ignore unimportant directories [dim]({"(Y/n)" if DEFAULTS["auto_ignore"] else "(y/N)"} >  )').strip(
        ).lower() in ("y", "yes")

    into_file = xx.FormatCodes.input(
        f'Output tree into file [dim]({"(Y/n)" if DEFAULTS["into_file"] else "(y/N)"} >  )').strip().lower() in ("y", "yes")

    xx.Console.info("generating tree ...", start="\n")
    result = tree.generate(
        ignore_dirs=ignore_dirs,
        auto_ignore=auto_ignore,
        include_file_contents=file_contents,
        style=tree_style,
        indent=indent,
    )

    if into_file:
        file, cls_line = None, ""
        try:
            file = xx.File.create("tree.txt", result)
        except FileExistsError:
            cls_line = "\033[F\033[K"
            if xx.Console.confirm("[white]tree.txt[_] already exists. Overwrite?", end=""):
                file = xx.File.create("tree.txt", result, force=True)
            else:
                xx.Console.exit()
        if file:
            xx.Console.done(f"[white]{file}[_] successfully created.", start=cls_line, end="\n\n")
        else:
            xx.Console.fail("File is empty or failed to create file.", start=cls_line, end="\n\n")
    else:
        xx.FormatCodes.print("[white]")
        sys.stdout.write(result)
        xx.FormatCodes.print("[_]")


if __name__ == "__main__":
    try:

        main()
    except KeyboardInterrupt:
        xx.Console.exit(end="\n\n")
    except PermissionError:
        xx.Console.fail("Permission to create file was denied.")
    except Exception as e:
        xx.Console.fail(str(e))
